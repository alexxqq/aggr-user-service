# API Contract

**Auth model:**
- Public `/v1/*` endpoints: API Gateway verifies Firebase token, forwards `X-Merchant-Id: <uuid>` header. Service trusts this header.
- Internal `/internal/*` endpoints: require `X-Internal-Secret` header.

---

## Public endpoints

### GET /health
Returns service health status. No auth required.

**Response:** `{"status": "ok"}`

---

### GET /v1/me
Returns full merchant config.

**Headers:** `X-Merchant-Id: <uuid>`

**Response:** `MeResponse` — profile, settings, wallets, webhook, limits, feature_flags

---

### PATCH /v1/me
Updates merchant profile (display_name).

**Headers:** `X-Merchant-Id: <uuid>`

**Body:** `{"display_name": "..."}` (all fields optional)

---

### GET /v1/me/settings
Returns merchant settings.

**Headers:** `X-Merchant-Id: <uuid>`

---

### PATCH /v1/me/settings
Updates merchant settings.

**Headers:** `X-Merchant-Id: <uuid>`

**Body:** `{"allowed_chains": [...], "allowed_assets": [...], "default_chain": "...", "timezone": "..."}`

---

### GET /v1/me/wallets
Returns list of payout wallets.

**Headers:** `X-Merchant-Id: <uuid>`

---

### POST /v1/me/wallets
Creates a new payout wallet. Returns 409 if chain+address already exists.

**Headers:** `X-Merchant-Id: <uuid>`

**Body:** `{"chain": "ethereum", "address": "0x...", "label": "...", "is_default": false}`

---

### PATCH /v1/me/wallets/{wallet_id}
Updates wallet label or default flag.

**Headers:** `X-Merchant-Id: <uuid>`

**Body:** `{"label": "...", "is_default": true}` (all fields optional)

---

### DELETE /v1/me/wallets/{wallet_id}
Removes a wallet. Returns 204.

**Headers:** `X-Merchant-Id: <uuid>`

---

### GET /v1/me/webhook
Returns webhook config. Secret is never returned in GET.

**Headers:** `X-Merchant-Id: <uuid>`

---

### PUT /v1/me/webhook
Creates or updates webhook. Secret returned only on creation.

**Headers:** `X-Merchant-Id: <uuid>`

**Body:** `{"webhook_url": "https://...", "is_enabled": true}`

---

### POST /v1/me/webhook/rotate
Rotates webhook secret. Returns new plain secret once.

**Headers:** `X-Merchant-Id: <uuid>`

---

### GET /v1/me/limits
Returns anti-abuse limits.

**Headers:** `X-Merchant-Id: <uuid>`

---

### PATCH /v1/me/limits
Updates limits.

**Headers:** `X-Merchant-Id: <uuid>`

---

### GET /v1/me/features
Returns feature flags.

**Headers:** `X-Merchant-Id: <uuid>`

---

### PATCH /v1/me/features
Updates feature flags (replaces flags dict).

**Headers:** `X-Merchant-Id: <uuid>`

---

## Internal endpoints (X-Internal-Secret required)

### POST /internal/merchant/init
Idempotent bootstrap called by API Gateway after Firebase verification.
Creates merchant if not exists. Returns merchant_id.

**Body:** `{"firebase_uid": "...", "email": "...", "display_name": "..."}`

**Response:** `{"merchant_id": "...", "firebase_uid": "...", "status": "active", "created": true}`

---

### GET /internal/merchant/{merchant_id}/config
Returns full merchant configuration.

---

### GET /internal/merchant/{merchant_id}/capabilities
Returns merchant status, is_active flag, allowed chains/assets.

---

### GET /internal/merchants/{merchant_id}
*(Legacy, prefer /internal/merchant/{id}/config)*

---

### GET /internal/merchants/{merchant_id}/limits
Returns limits only.

---

### GET /internal/users/{firebase_uid}
Resolves firebase_uid → merchant config. Used by Gateway for bootstrap lookup.
