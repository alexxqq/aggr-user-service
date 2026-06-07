# User Service Improvement Plan — Crypto Payment Aggregator

## 1) Summary: What’s Missing and Why It Matters

| Gap | Why it matters in a crypto aggregator |
|-----|----------------------------------------|
| **No limits / anti-abuse** | We sponsor gas from our wallets. Without per-merchant limits (e.g. daily tx cap, max pending), abuse or bugs can burn unbounded gas. |
| **Webhook secret from client** | `secret_hash` is currently client-supplied. For verification, the server should generate a secret, store its hash, and return the plain secret only once (create/rotate). |
| **Internal API uses firebase_uid** | Other services (Payment, Blockchain Core) should use stable **merchant_id (UUID)** so we don’t couple internal contracts to Firebase. |
| **No feature flags** | Optional but useful for rolling out chain/asset support or limits per merchant without code deploys. |
| **Explicit /me/init required** | Frontend must remember to call init; auto-init on first authenticated request reduces integration friction and race conditions. |
| **Init race** | Concurrent first requests can double-create; idempotent init with proper locking/unique constraint is required. |
| **Limits not exposed to other services** | Blockchain Core needs to know merchant limits (e.g. max txs per day) before sponsoring gas. |

---

## 2) Role & Responsibilities

### User Service owns
- **Merchant identity mapping**: Firebase UID → internal `merchant_id` (UUID).
- **Merchant profile**: email, display_name, status (active/disabled).
- **Merchant configuration**: allowed chains/assets, default chain, timezone.
- **Payout wallets**: per-chain addresses, default wallet, labels (no private keys).
- **Webhook config**: URL, enabled flag, **server-generated secret** (stored as hash; plain returned only on create/rotate).
- **Limits / anti-abuse**: per-merchant policies (e.g. daily tx cap, max pending invoices) used by Payment and Blockchain Core.
- **Feature flags** (optional): per-merchant toggles for capabilities.

### User Service does NOT own
- **Auth**: Firebase issues and verifies tokens; User Service only verifies ID token on public routes and maps to `merchant_id`.
- **Payments / invoices / products**: Payment Service.
- **Gas / oracle / tx execution / chain watcher / our hot wallets**: Blockchain Core Service.
- **Private keys**: Never stored in User Service; keys live in Blockchain Core or a secrets vault.

---

## 3) Proposed Data Model (Postgres)

All PKs are UUID. Use `firebase_uid` only for auth mapping; internal references use `user_id` (= merchant_id).

### Table: `users` (merchant identity)
| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | **merchant_id** for internal APIs |
| firebase_uid | VARCHAR(128) UNIQUE NOT NULL | Auth mapping only |
| email | VARCHAR(255) | |
| display_name | VARCHAR(255) | |
| status | ENUM(active, disabled) | Default active |
| created_at, updated_at | TIMESTAMPTZ | |

### Table: `merchant_settings` (capabilities)
| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| user_id | UUID FK(users.id) UNIQUE | |
| allowed_chains | JSONB | e.g. ["ethereum", "polygon"] |
| allowed_assets | JSONB | e.g. ["USDC", "ETH"] |
| default_chain | VARCHAR(64) | |
| timezone | VARCHAR(64) | |
| created_at, updated_at | TIMESTAMPTZ | |

### Table: `wallets` (payout / receiving)
| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| user_id | UUID FK(users.id) | |
| chain | VARCHAR(64) | |
| address | VARCHAR(255) | |
| label | VARCHAR(255) | |
| is_default | BOOLEAN | One per user (or per chain if you prefer) |
| created_at | TIMESTAMPTZ | |
| UNIQUE(user_id, chain, address) | | |

### Table: `webhook_config`
| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| user_id | UUID FK(users.id) UNIQUE | |
| webhook_url | VARCHAR(2048) | |
| secret_hash | VARCHAR(255) | Server-generated secret, stored as hash (e.g. SHA-256 HMAC) |
| is_enabled | BOOLEAN | Default true |
| created_at, updated_at | TIMESTAMPTZ | |
| *(optional)* secret_rotated_at | TIMESTAMPTZ | For audit |

**Webhook secret behavior**: Server generates cryptographically random secret (e.g. 32 bytes hex), stores `hash(secret)`, returns plain secret **only once** in response on create or rotate. Client uses it to verify webhook signatures.

### Table: `merchant_limits` (anti-abuse / gas sponsorship)
| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| user_id | UUID FK(users.id) UNIQUE | One row per merchant |
| max_txs_per_day | INT | NULL = no limit (or use default in code) |
| max_pending_invoices | INT | NULL = no limit |
| max_single_tx_amount_usd | DECIMAL(20,2) | Optional |
| created_at, updated_at | TIMESTAMPTZ | |

### Table: `merchant_feature_flags` (optional)
| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| user_id | UUID FK(users.id) UNIQUE | One row per merchant |
| flags | JSONB | e.g. {"new_checkout": true, "polygon_enabled": true} |
| updated_at | TIMESTAMPTZ | |

---

## 4) Proposed Public API (via Gateway, Firebase Auth)

All under `/me`, Bearer token required. Prefer **auto-init**: if user not found on any authenticated request, create user + merchant_settings (and optionally default limits) then proceed; otherwise keep explicit `POST /me/init` as alternative.

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /me | Full config: profile, merchant_settings, wallets, webhook_config (no secret), limits, [features]. **Auto-init if missing.** |
| POST | /me/init | Idempotent create user + merchant_settings (+ default limits). Optional if auto-init is on. |
| PATCH | /me/profile | Update display_name (and email if you allow). |
| PATCH | /me/settings | Update allowed_chains, allowed_assets, default_chain, timezone. |
| GET | /me/wallets | List wallets. |
| POST | /me/wallets | Add wallet (body: chain, address, label?, is_default?). |
| DELETE | /me/wallets/{wallet_id} | Remove wallet. |
| GET | /me/webhook | Get webhook config (url, is_enabled; never return secret). |
| PUT | /me/webhook | Set URL + is_enabled. **Server generates new secret**, stores hash, returns **plain secret once** in response. |
| POST | /me/webhook/rotate | Rotate secret: new secret generated, hash stored, **plain secret returned once**. |
| GET | /me/limits | Get current limits. |
| PATCH | /me/limits | Update limits (max_txs_per_day, max_pending_invoices, etc.). |
| GET | /me/features | (Optional) Get feature flags. |
| PATCH | /me/features | (Optional) Update feature flags (if you allow merchant-facing toggles). |

### Example: GET /me response (expanded)
```json
{
  "profile": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "firebase_uid": "abc123",
    "email": "merchant@example.com",
    "display_name": "Acme",
    "status": "active",
    "created_at": "2025-01-01T00:00:00Z",
    "updated_at": "2025-01-01T00:00:00Z"
  },
  "merchant_settings": {
    "allowed_chains": ["ethereum", "polygon"],
    "allowed_assets": ["USDC", "ETH"],
    "default_chain": "ethereum",
    "timezone": "Europe/Kyiv"
  },
  "wallets": [
    { "id": "...", "chain": "ethereum", "address": "0x...", "label": "Main", "is_default": true }
  ],
  "webhook_config": {
    "webhook_url": "https://...",
    "is_enabled": true
  },
  "limits": {
    "max_txs_per_day": 100,
    "max_pending_invoices": 50
  }
}
```

### Example: PUT /me/webhook response (secret returned only on create/update)
```json
{
  "webhook_url": "https://merchant.com/webhook",
  "is_enabled": true,
  "secret": "whsec_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
}
```
Omit `secret` in response on subsequent GET; include only when newly generated (create or rotate).

---

## 5) Proposed Internal API (service-to-service)

- **Auth**: Header `X-Internal-Secret: <INTERNAL_API_SECRET>` (no Firebase).
- **Identifier**: Use **merchant_id** (users.id UUID) in paths and responses so Payment and Blockchain Core don’t depend on firebase_uid.

### Endpoints

| Method | Endpoint | Consumer | Description |
|--------|----------|----------|-------------|
| GET | /internal/merchants/{merchant_id} | Payment, Blockchain Core | Full config for processing: status, settings, wallets, webhook_url, **limits**. |
| GET | /internal/merchants/{merchant_id}/limits | Blockchain Core | Only limits (for fast checks before sponsoring gas). |
| GET | /internal/merchants/by-firebase-uid/{firebase_uid} | Gateway or legacy | Resolve firebase_uid → merchant_id + minimal config (or 404). |

### Internal DTO: GET /internal/merchants/{merchant_id}
```json
{
  "merchant_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "active",
  "allowed_chains": ["ethereum", "polygon"],
  "allowed_assets": ["USDC", "ETH"],
  "default_chain": "ethereum",
  "wallets": [
    { "chain": "ethereum", "address": "0x...", "label": "Main", "is_default": true }
  ],
  "webhook_url": "https://...",
  "webhook_enabled": true,
  "limits": {
    "max_txs_per_day": 100,
    "max_pending_invoices": 50
  }
}
```

### Internal DTO: GET /internal/merchants/{merchant_id}/limits
```json
{
  "merchant_id": "550e8400-e29b-41d4-a716-446655440000",
  "max_txs_per_day": 100,
  "max_pending_invoices": 50
}
```

### Resolve firebase_uid → merchant_id
Either:
- **GET /internal/merchants/by-firebase-uid/{firebase_uid}** returns `{ "merchant_id": "uuid", ... minimal config }`, and other services then call GET by merchant_id, or
- Keep **GET /internal/users/{firebase_uid}** for backward compatibility and add **GET /internal/merchants/{merchant_id}** as the preferred contract. New consumers use merchant_id.

---

## 6) State / Logic Notes

- **Auto-init**: On first authenticated request, if user not found, create user + merchant_settings + default merchant_limits (e.g. max_txs_per_day=100), then continue. Optional: keep POST /me/init for explicit onboarding flows.
- **Webhook secret**: On PUT /me/webhook and POST /me/webhook/rotate: generate random secret (e.g. `secrets.token_hex(32)`), store hash (e.g. SHA-256 of secret or HMAC), return plain secret in response only this once. Never return secret in GET. Client stores it for signing/verification.
- **Idempotency / init race**: init_user: use SELECT ... FOR UPDATE or unique index on firebase_uid + insert ON CONFLICT DO NOTHING / handle IntegrityError and re-fetch. Current “select then insert” can race; add unique constraint and handle duplicate key.
- **Private keys**: Never in User Service. Wallets table stores only public addresses; keys in Blockchain Core or vault.

---

## 7) Checklist of Changes to Apply

### Migrations (Alembic)
- [ ] Add table `merchant_limits` (user_id UNIQUE, max_txs_per_day, max_pending_invoices, etc.).
- [ ] Add table `merchant_feature_flags` (optional) (user_id UNIQUE, flags JSONB).
- [ ] Ensure `webhook_config.secret_hash` is server-only (no client-supplied secret in upsert); add `secret_rotated_at` if desired.
- [ ] Init: create default `merchant_limits` row when creating user (e.g. max_txs_per_day=100).

### Models
- [ ] Add model `MerchantLimits` (user_id FK, max_txs_per_day, max_pending_invoices, timestamps).
- [ ] Add model `MerchantFeatureFlags` (optional) (user_id FK, flags JSONB).
- [ ] User: add relationship to limits and feature_flags.
- [ ] WebhookConfig: ensure secret_hash is only set server-side; add optional secret_rotated_at.

### Schemas (Pydantic)
- [ ] Limits: MerchantLimitsResponse, MerchantLimitsUpdate; include in MeResponse.
- [ ] Features (optional): MerchantFeatureFlagsResponse, MerchantFeatureFlagsUpdate.
- [ ] Webhook: response includes optional `secret` only when just created/rotated; remove client-supplied secret_hash from upsert body; add WebhookRotateResponse with `secret`.
- [ ] Internal: add InternalMerchantConfigResponse (merchant_id, status, settings, wallets, webhook_url, webhook_enabled, limits); add InternalMerchantLimitsResponse; add by-merchant_id endpoints DTOs.

### Services
- [ ] user_service: init_user creates default MerchantLimits; get_user_by_id loads limits (and feature_flags); add get_user_by_id_with_relations for internal API.
- [ ] Add limits_service (or in user_service): get_limits, update_limits.
- [ ] Webhook: generate secret (e.g. secrets.token_hex(32)), hash and store, return plain secret in response on create/rotate; add rotate_webhook_secret.
- [ ] Init idempotency: use unique on firebase_uid and handle duplicate insert (e.g. ON CONFLICT or catch IntegrityError and re-select).

### Routes (public /me)
- [ ] GET /me: auto-init if user missing (create user + settings + default limits), then return full config; include limits (and optional features).
- [ ] GET /me/wallets (optional explicit list endpoint; or keep GET /me as single read).
- [ ] GET /me/webhook, PUT /me/webhook (server-generated secret; return secret only once in PUT response).
- [ ] POST /me/webhook/rotate: generate new secret, store hash, return plain secret once.
- [ ] GET /me/limits, PATCH /me/limits.
- [ ] GET /me/features, PATCH /me/features (optional).

### Routes (internal)
- [ ] GET /internal/merchants/{merchant_id}: full config (status, settings, wallets, webhook_url, webhook_enabled, limits); auth: X-Internal-Secret.
- [ ] GET /internal/merchants/{merchant_id}/limits: limits only.
- [ ] GET /internal/merchants/by-firebase-uid/{firebase_uid}: return merchant_id + minimal config (or keep GET /internal/users/{firebase_uid} and add new routes).
- [ ] Deprecate or keep GET /internal/users/{firebase_uid} for backward compatibility; document preference for merchant_id.

### Tests
- [ ] Test auto-init on first GET /me.
- [ ] Test init idempotency (concurrent inits, no duplicate users).
- [ ] Test webhook secret: generated on create/rotate, not returned on GET.
- [ ] Test internal API by merchant_id (200, 404).
- [ ] Test limits CRUD and internal limits response.

### Docs and config
- [ ] Update README: public vs internal API, merchant_id usage, webhook secret behavior, limits.
- [ ] Update .env.example: no new vars required; document INTERNAL_API_SECRET if not already.

---

## 8) Implementation Order (suggested)

1. **Migrations**: merchant_limits (+ default in init), optional merchant_feature_flags; webhook secret_rotated_at optional.
2. **Models + schemas**: MerchantLimits, limits in MeResponse; webhook response with optional `secret`.
3. **Webhook secret**: server-side generation and hash; return plain only on create/rotate; add rotate endpoint.
4. **Limits**: service + PATCH/GET /me/limits; include in GET /me and in internal config.
5. **Internal API**: GET by merchant_id + GET limits; DTOs with merchant_id; keep or alias by-firebase-uid.
6. **Auto-init**: GET /me (and optionally other /me routes) create user+settings+limits if not found.
7. **Init race**: tighten idempotency (unique + conflict handling).
8. **Feature flags** (optional): model, schema, endpoints.
9. **Tests + README**.

This plan keeps the stack (FastAPI, async SQLAlchemy, Alembic, Pydantic v2, Firebase for public auth) and adds only the minimal tables and endpoints needed for a production-ready crypto aggregator User Service.
