# Implementation Plan

**Date:** 2026-04-13
**Audit by:** Claude Code

---

## What is already implemented

**Models (all 6 tables exist):**
- User (`users` table) — firebase_uid, email, status, timestamps
- MerchantSettings — allowed_chains, allowed_assets, default_chain, timezone
- Wallet — chain, address, label, is_default, unique(user_id, chain, address)
- WebhookConfig — url, secret_hash, is_enabled, secret_rotated_at
- MerchantLimits — max_txs_per_day, max_pending_invoices, max_single_tx_amount_usd
- MerchantFeatureFlags — flags (JSONB)

**Migrations:** 2 migrations cover all 6 tables cleanly.

**Services:** user_service, wallet_service, limits_service, features_service — all well-implemented.

**Schemas:** All Pydantic schemas exist and are correct.

**Infrastructure:** Dockerfile, docker-compose, alembic setup — all functional.

---

## What is broken / mismatched

### 1. Firebase auth in routes (architecture violation — MUST FIX)
- `security.py` implements direct Firebase token verification.
- `routes_me.py` depends on `get_current_firebase_uid` → calls Firebase SDK directly.
- **Spec says:** "Gateway verifies Firebase token; User Service trusts forwarded headers."
- **Fix:** Add `get_merchant_id_from_header` that reads `X-Merchant-Id` (UUID) from header. Replace all route dependencies.

### 2. Missing /v1 prefix on public routes
- Current: `/me/...`
- Spec: `/v1/me/...`
- **Fix:** Change `prefix="/me"` to `prefix="/v1/me"` in routes_me.py.

### 3. PATCH /v1/me path wrong
- Current: `PATCH /me/profile`
- Spec: `PATCH /v1/me`
- **Fix:** Change route path from `/profile` to `""`.

### 4. Internal route paths don't match spec
- Spec: `GET /internal/merchant/{merchant_id}/config` (singular "merchant")
- Current: `GET /internal/merchants/{merchant_id}` (plural)
- **Fix:** Add spec-compliant aliases; keep existing routes for compatibility.

### 5. Missing capabilities endpoint
- Spec: `GET /internal/merchant/{merchant_id}/capabilities`
- Current: not present.
- **Fix:** Implement returning status + allowed_chains + allowed_assets.

---

## What is missing

- `GET /v1/me/settings` — endpoint exists for PATCH but not GET
- `GET /v1/me/wallets` — POST and DELETE exist, but not GET list
- `PATCH /v1/me/wallets/{wallet_id}` — update wallet, missing entirely
- `WalletUpdate` schema — not defined
- `wallet_service.update_wallet()` — not implemented
- `POST /internal/merchant/init` — gateway bootstrap (create user from firebase_uid)
- Tests split into unit/integration subdirectories

---

## What will NOT be changed

- All model definitions (correct, no schema changes needed)
- All migrations (correct)
- All service implementations (correct; adding update_wallet only)
- Docker/Dockerfile setup (correct)
- Internal endpoints that already work (keep, add aliases)

---

## Implementation steps (smallest correct changes)

1. `security.py`: add `get_merchant_id_from_header` dependency
2. `routes_me.py`: rewrite using new auth, fix prefix, fix PATCH path, add 3 missing endpoints
3. `wallet.py` (schemas): add `WalletUpdate`
4. `wallet_service.py`: add `update_wallet`
5. `routes_internal.py`: add `/merchant/{id}/config`, `/merchant/{id}/capabilities`, `POST /merchant/init`
6. `schemas/internal.py`: add `InternalMerchantCapabilitiesResponse`, `MerchantInitRequest/Response`
7. Move existing tests → `tests/unit/`, add new unit tests
8. Run linting + tests
9. Update docs
