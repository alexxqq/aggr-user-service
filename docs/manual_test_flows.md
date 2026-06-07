# Manual Test Flows — User Service

This document walks through every logical flow from a client perspective.
Run these against a locally started service before marking anything done.

**Base URL:** `http://localhost:8000`

**Prerequisites:**
```bash
docker compose up -d
# wait for postgres healthcheck, then:
docker compose exec user-service alembic upgrade head
```

Verify the service is alive:
```bash
curl http://localhost:8000/health
# → {"status":"ok"}
```

---

## 0. Shared variables

Set these once and reuse across all flows:

```bash
INTERNAL_SECRET="dev-internal-secret"   # matches INTERNAL_API_SECRET in .env / docker-compose
BASE="http://localhost:8000"
```

---

## 1. Merchant Bootstrap (Gateway flow)

The Gateway calls this after verifying a Firebase token.
This is how a merchant_id is created and obtained.

### 1.1 Init a new merchant

```bash
curl -s -X POST "$BASE/internal/merchant/init" \
  -H "X-Internal-Secret: $INTERNAL_SECRET" \
  -H "Content-Type: application/json" \
  -d '{"firebase_uid": "test-uid-001", "email": "merchant@example.com", "display_name": "Test Merchant"}' | jq
```

**Expected:**
```json
{
  "merchant_id": "<some-uuid>",
  "firebase_uid": "test-uid-001",
  "status": "active",
  "created": true
}
```

Save the merchant_id:
```bash
MERCHANT_ID="<uuid from above>"
```

### 1.2 Init same merchant again (idempotent)

```bash
curl -s -X POST "$BASE/internal/merchant/init" \
  -H "X-Internal-Secret: $INTERNAL_SECRET" \
  -H "Content-Type: application/json" \
  -d '{"firebase_uid": "test-uid-001", "email": "merchant@example.com"}' | jq
```

**Expected:** Same `merchant_id`, `"created": false`

### 1.3 Init without internal secret → 403

```bash
curl -s -X POST "$BASE/internal/merchant/init" \
  -H "Content-Type: application/json" \
  -d '{"firebase_uid": "test-uid-001"}' | jq
```

**Expected:** `{"detail": "Forbidden"}`, status 403

---

## 2. Auth header validation

All `/v1/me/*` endpoints require `X-Merchant-Id`.

### 2.1 Missing header → 401

```bash
curl -s "$BASE/v1/me" | jq
```

**Expected:** `{"detail": "Missing X-Merchant-Id header"}`, status 401

### 2.2 Malformed UUID → 400

```bash
curl -s "$BASE/v1/me" -H "X-Merchant-Id: not-a-uuid" | jq
```

**Expected:** `{"detail": "Invalid X-Merchant-Id format (must be UUID)"}`, status 400

### 2.3 Valid UUID but unknown merchant → 404

```bash
curl -s "$BASE/v1/me" -H "X-Merchant-Id: 00000000-0000-0000-0000-000000000000" | jq
```

**Expected:** `{"detail": "Merchant not found"}`, status 404

---

## 3. Merchant Profile

### 3.1 GET full profile

```bash
curl -s "$BASE/v1/me" -H "X-Merchant-Id: $MERCHANT_ID" | jq
```

**Expected:** MeResponse with all sections populated (wallets=[], webhook_config=null, etc.)

```json
{
  "profile": {
    "id": "<merchant_id>",
    "firebase_uid": "test-uid-001",
    "email": "merchant@example.com",
    "display_name": "Test Merchant",
    "status": "active",
    ...
  },
  "merchant_settings": {
    "allowed_chains": [],
    "allowed_assets": [],
    "default_chain": null,
    "timezone": null,
    ...
  },
  "wallets": [],
  "webhook_config": null,
  "limits": {
    "max_txs_per_day": 100,
    "max_pending_invoices": 50,
    "max_single_tx_amount_usd": null,
    ...
  },
  "feature_flags": {
    "flags": {},
    ...
  }
}
```

### 3.2 PATCH display_name

```bash
curl -s -X PATCH "$BASE/v1/me" \
  -H "X-Merchant-Id: $MERCHANT_ID" \
  -H "Content-Type: application/json" \
  -d '{"display_name": "Updated Name"}' | jq
```

**Expected:** UserProfileResponse with `display_name: "Updated Name"`

### 3.3 Verify update persisted

```bash
curl -s "$BASE/v1/me" -H "X-Merchant-Id: $MERCHANT_ID" | jq '.profile.display_name'
```

**Expected:** `"Updated Name"`

---

## 4. Merchant Settings

### 4.1 GET settings (empty defaults)

```bash
curl -s "$BASE/v1/me/settings" -H "X-Merchant-Id: $MERCHANT_ID" | jq
```

**Expected:** `allowed_chains: [], allowed_assets: [], default_chain: null`

### 4.2 PATCH settings — add chains and assets

```bash
curl -s -X PATCH "$BASE/v1/me/settings" \
  -H "X-Merchant-Id: $MERCHANT_ID" \
  -H "Content-Type: application/json" \
  -d '{
    "allowed_chains": ["ethereum", "polygon"],
    "allowed_assets": ["USDT", "USDC"],
    "default_chain": "ethereum",
    "timezone": "UTC"
  }' | jq
```

**Expected:** Updated MerchantSettingsResponse with the new values.

### 4.3 Verify settings persisted

```bash
curl -s "$BASE/v1/me/settings" -H "X-Merchant-Id: $MERCHANT_ID" | jq '{allowed_chains, default_chain}'
```

**Expected:** `{"allowed_chains": ["ethereum", "polygon"], "default_chain": "ethereum"}`

### 4.4 Partial update (only timezone)

```bash
curl -s -X PATCH "$BASE/v1/me/settings" \
  -H "X-Merchant-Id: $MERCHANT_ID" \
  -H "Content-Type: application/json" \
  -d '{"timezone": "Europe/Kyiv"}' | jq '.timezone'
```

**Expected:** `"Europe/Kyiv"` — other fields unchanged.

---

## 5. Wallets

### 5.1 GET wallets (empty)

```bash
curl -s "$BASE/v1/me/wallets" -H "X-Merchant-Id: $MERCHANT_ID" | jq
```

**Expected:** `[]`

### 5.2 POST — add first wallet

```bash
curl -s -X POST "$BASE/v1/me/wallets" \
  -H "X-Merchant-Id: $MERCHANT_ID" \
  -H "Content-Type: application/json" \
  -d '{
    "chain": "ethereum",
    "address": "0xAbCdEf1234567890AbCdEf1234567890AbCdEf12",
    "label": "Main ETH wallet",
    "is_default": true
  }' | jq
```

**Expected:** 201, WalletResponse with `id`, `is_default: true`

Save wallet id:
```bash
WALLET_ID="<id from above>"
```

### 5.3 POST — add second wallet

```bash
curl -s -X POST "$BASE/v1/me/wallets" \
  -H "X-Merchant-Id: $MERCHANT_ID" \
  -H "Content-Type: application/json" \
  -d '{
    "chain": "polygon",
    "address": "0xPolygonAddress000000000000000000000000001",
    "label": "Polygon wallet",
    "is_default": false
  }' | jq
```

**Expected:** 201, `is_default: false`

### 5.4 GET wallets — now has two

```bash
curl -s "$BASE/v1/me/wallets" -H "X-Merchant-Id: $MERCHANT_ID" | jq 'length, .[].chain'
```

**Expected:** `2`, `"ethereum"`, `"polygon"`

### 5.5 POST — duplicate wallet → 409

```bash
curl -s -X POST "$BASE/v1/me/wallets" \
  -H "X-Merchant-Id: $MERCHANT_ID" \
  -H "Content-Type: application/json" \
  -d '{
    "chain": "ethereum",
    "address": "0xAbCdEf1234567890AbCdEf1234567890AbCdEf12"
  }' | jq
```

**Expected:** 409 `"Wallet with this chain and address already exists"`

### 5.6 PATCH wallet — update label

```bash
curl -s -X PATCH "$BASE/v1/me/wallets/$WALLET_ID" \
  -H "X-Merchant-Id: $MERCHANT_ID" \
  -H "Content-Type: application/json" \
  -d '{"label": "Primary ETH"}' | jq '.label'
```

**Expected:** `"Primary ETH"`

### 5.7 PATCH wallet — set as non-default

```bash
curl -s -X PATCH "$BASE/v1/me/wallets/$WALLET_ID" \
  -H "X-Merchant-Id: $MERCHANT_ID" \
  -H "Content-Type: application/json" \
  -d '{"is_default": false}' | jq '.is_default'
```

**Expected:** `false`

### 5.8 PATCH unknown wallet → 404

```bash
curl -s -X PATCH "$BASE/v1/me/wallets/00000000-0000-0000-0000-000000000000" \
  -H "X-Merchant-Id: $MERCHANT_ID" \
  -H "Content-Type: application/json" \
  -d '{"label": "ghost"}' | jq
```

**Expected:** 404

### 5.9 DELETE wallet

```bash
curl -s -X DELETE "$BASE/v1/me/wallets/$WALLET_ID" \
  -H "X-Merchant-Id: $MERCHANT_ID" -w "\nHTTP %{http_code}\n"
```

**Expected:** `HTTP 204` (empty body)

### 5.10 DELETE same wallet again → 404

```bash
curl -s -X DELETE "$BASE/v1/me/wallets/$WALLET_ID" \
  -H "X-Merchant-Id: $MERCHANT_ID" | jq
```

**Expected:** 404

---

## 6. Webhook Configuration

### 6.1 GET webhook — not configured yet → 404

```bash
curl -s "$BASE/v1/me/webhook" -H "X-Merchant-Id: $MERCHANT_ID" | jq
```

**Expected:** 404 `"No webhook config. Use PUT /v1/me/webhook to create."`

### 6.2 PUT webhook — create

```bash
curl -s -X PUT "$BASE/v1/me/webhook" \
  -H "X-Merchant-Id: $MERCHANT_ID" \
  -H "Content-Type: application/json" \
  -d '{
    "webhook_url": "https://my-backend.example.com/webhooks/payments",
    "is_enabled": true
  }' | jq
```

**Expected:** WebhookConfigResponse with:
- `webhook_url` set
- `is_enabled: true`
- `secret: "whsec_..."` ← **store this, returned only once**

Save the secret:
```bash
WEBHOOK_SECRET="<whsec_... from above>"
```

### 6.3 GET webhook — secret is null in GET

```bash
curl -s "$BASE/v1/me/webhook" -H "X-Merchant-Id: $MERCHANT_ID" | jq '{webhook_url, is_enabled, secret}'
```

**Expected:** `secret: null` — never returned in GET responses.

### 6.4 PUT webhook again — secret NOT regenerated on update

```bash
curl -s -X PUT "$BASE/v1/me/webhook" \
  -H "X-Merchant-Id: $MERCHANT_ID" \
  -H "Content-Type: application/json" \
  -d '{"webhook_url": "https://my-backend.example.com/webhooks/payments", "is_enabled": false}' | jq '{is_enabled, secret}'
```

**Expected:** `is_enabled: false`, `secret: null` (no new secret generated on update)

### 6.5 Rotate webhook secret

```bash
curl -s -X POST "$BASE/v1/me/webhook/rotate" \
  -H "X-Merchant-Id: $MERCHANT_ID" | jq
```

**Expected:**
```json
{
  "secret": "whsec_<new_value>",
  "webhook_url": "https://...",
  "is_enabled": false
}
```

Note: old secret is now invalid for signature verification.

### 6.6 Rotate without webhook config → 404

Create a fresh merchant first, then:
```bash
curl -s -X POST "$BASE/internal/merchant/init" \
  -H "X-Internal-Secret: $INTERNAL_SECRET" \
  -H "Content-Type: application/json" \
  -d '{"firebase_uid": "test-uid-nowebhook"}' | jq '.merchant_id'

NEW_MERCHANT_ID="<id>"

curl -s -X POST "$BASE/v1/me/webhook/rotate" \
  -H "X-Merchant-Id: $NEW_MERCHANT_ID" | jq
```

**Expected:** 404

---

## 7. Limits (anti-abuse)

### 7.1 GET limits — defaults after init

```bash
curl -s "$BASE/v1/me/limits" -H "X-Merchant-Id: $MERCHANT_ID" | jq
```

**Expected:**
```json
{
  "max_txs_per_day": 100,
  "max_pending_invoices": 50,
  "max_single_tx_amount_usd": null,
  ...
}
```

### 7.2 PATCH limits

```bash
curl -s -X PATCH "$BASE/v1/me/limits" \
  -H "X-Merchant-Id: $MERCHANT_ID" \
  -H "Content-Type: application/json" \
  -d '{
    "max_txs_per_day": 200,
    "max_single_tx_amount_usd": "5000.00"
  }' | jq '{max_txs_per_day, max_single_tx_amount_usd}'
```

**Expected:** `max_txs_per_day: 200`, `max_single_tx_amount_usd: "5000.00"`

### 7.3 PATCH limits — negative value rejected

```bash
curl -s -X PATCH "$BASE/v1/me/limits" \
  -H "X-Merchant-Id: $MERCHANT_ID" \
  -H "Content-Type: application/json" \
  -d '{"max_txs_per_day": -1}' | jq
```

**Expected:** 422 validation error

---

## 8. Feature Flags

### 8.1 GET features — empty

```bash
curl -s "$BASE/v1/me/features" -H "X-Merchant-Id: $MERCHANT_ID" | jq '.flags'
```

**Expected:** `{}`

### 8.2 PATCH features

```bash
curl -s -X PATCH "$BASE/v1/me/features" \
  -H "X-Merchant-Id: $MERCHANT_ID" \
  -H "Content-Type: application/json" \
  -d '{"flags": {"batch_payments": true, "custom_branding": false}}' | jq '.flags'
```

**Expected:** `{"batch_payments": true, "custom_branding": false}`

### 8.3 PATCH features — replace (not merge)

```bash
curl -s -X PATCH "$BASE/v1/me/features" \
  -H "X-Merchant-Id: $MERCHANT_ID" \
  -H "Content-Type: application/json" \
  -d '{"flags": {"new_flag": true}}' | jq '.flags'
```

**Expected:** `{"new_flag": true}` — previous flags are gone (full replace).

---

## 9. Internal API — Config & Capabilities

### 9.1 GET /internal/merchant/{id}/config

```bash
curl -s "$BASE/internal/merchant/$MERCHANT_ID/config" \
  -H "X-Internal-Secret: $INTERNAL_SECRET" | jq
```

**Expected:** Full config including wallets, webhook, limits, chains.

### 9.2 GET /internal/merchant/{id}/capabilities

```bash
curl -s "$BASE/internal/merchant/$MERCHANT_ID/capabilities" \
  -H "X-Internal-Secret: $INTERNAL_SECRET" | jq
```

**Expected:**
```json
{
  "merchant_id": "<id>",
  "status": "active",
  "is_active": true,
  "allowed_chains": ["ethereum", "polygon"],
  "allowed_assets": ["USDT", "USDC"],
  "default_chain": "ethereum"
}
```

### 9.3 Capabilities for unknown merchant → 404

```bash
curl -s "$BASE/internal/merchant/00000000-0000-0000-0000-000000000000/capabilities" \
  -H "X-Internal-Secret: $INTERNAL_SECRET" | jq
```

**Expected:** 404

### 9.4 GET /internal/users/{firebase_uid} — legacy lookup

```bash
curl -s "$BASE/internal/users/test-uid-001" \
  -H "X-Internal-Secret: $INTERNAL_SECRET" | jq '{merchant_id, status}'
```

**Expected:** merchant_id matches MERCHANT_ID, status active.

### 9.5 GET /internal/merchants/{id}/limits

```bash
curl -s "$BASE/internal/merchants/$MERCHANT_ID/limits" \
  -H "X-Internal-Secret: $INTERNAL_SECRET" | jq
```

**Expected:** Limits object.

---

## 10. Full end-to-end flow (happy path)

Run this in order as a smoke test:

```bash
# 1. Bootstrap
RESP=$(curl -s -X POST "$BASE/internal/merchant/init" \
  -H "X-Internal-Secret: $INTERNAL_SECRET" \
  -H "Content-Type: application/json" \
  -d '{"firebase_uid":"e2e-uid-001","email":"e2e@test.com","display_name":"E2E Merchant"}')
echo $RESP | jq .
MERCHANT_ID=$(echo $RESP | jq -r '.merchant_id')

# 2. Get profile
curl -s "$BASE/v1/me" -H "X-Merchant-Id: $MERCHANT_ID" | jq '.profile.email'
# → "e2e@test.com"

# 3. Configure settings
curl -s -X PATCH "$BASE/v1/me/settings" \
  -H "X-Merchant-Id: $MERCHANT_ID" \
  -H "Content-Type: application/json" \
  -d '{"allowed_chains":["ethereum"],"allowed_assets":["USDT"],"default_chain":"ethereum"}' | jq '.default_chain'
# → "ethereum"

# 4. Add wallet
WALLET=$(curl -s -X POST "$BASE/v1/me/wallets" \
  -H "X-Merchant-Id: $MERCHANT_ID" \
  -H "Content-Type: application/json" \
  -d '{"chain":"ethereum","address":"0xE2EAddress00000000000000000000000000001","is_default":true}')
WALLET_ID=$(echo $WALLET | jq -r '.id')

# 5. Configure webhook
WEBHOOK=$(curl -s -X PUT "$BASE/v1/me/webhook" \
  -H "X-Merchant-Id: $MERCHANT_ID" \
  -H "Content-Type: application/json" \
  -d '{"webhook_url":"https://example.com/hook","is_enabled":true}')
echo "Webhook secret (store it):" $(echo $WEBHOOK | jq -r '.secret')

# 6. Check capabilities (internal)
curl -s "$BASE/internal/merchant/$MERCHANT_ID/capabilities" \
  -H "X-Internal-Secret: $INTERNAL_SECRET" | jq '{status, is_active, allowed_chains}'

# 7. Clean up wallet
curl -s -X DELETE "$BASE/v1/me/wallets/$WALLET_ID" \
  -H "X-Merchant-Id: $MERCHANT_ID" -w "HTTP %{http_code}\n"
# → HTTP 204
```

---

## Expected HTTP status codes summary

| Scenario | Code |
|---|---|
| Success (GET) | 200 |
| Success (POST create) | 201 |
| Success (DELETE) | 204 |
| Validation error (bad body) | 422 |
| Missing/invalid X-Merchant-Id | 400 / 401 |
| Missing X-Internal-Secret | 403 |
| Resource not found | 404 |
| Duplicate wallet | 409 |
