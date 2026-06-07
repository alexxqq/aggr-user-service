# User Service Acceptance Checklist

## Domain boundaries

- [x] User Service stores merchant identity/config only
- [x] No product or invoice logic exists here
- [x] No blockchain execution logic exists here
- [x] No private key storage exists here

## Data model

- [x] merchants (users) table exists
- [x] merchant_settings table exists
- [x] wallets table exists
- [x] webhook_config table exists
- [x] merchant_limits table exists
- [x] merchant_feature_flags table exists

## API

- [x] GET /health returns 200
- [x] GET /v1/me returns merchant profile
- [x] PATCH /v1/me updates merchant profile
- [x] GET /v1/me/settings returns settings
- [x] PATCH /v1/me/settings updates settings
- [x] GET /v1/me/wallets returns wallet list
- [x] POST /v1/me/wallets creates wallet
- [x] PATCH /v1/me/wallets/{wallet_id} updates wallet
- [x] DELETE /v1/me/wallets/{wallet_id} removes wallet
- [x] GET /v1/me/webhook returns webhook config
- [x] PUT /v1/me/webhook sets webhook config
- [x] GET /internal/merchant/{merchant_id}/config returns full config
- [x] GET /internal/merchant/{merchant_id}/capabilities returns capabilities
- [x] POST /internal/merchant/init bootstraps merchant from Gateway

## Security

- [x] Internal endpoints validate X-Internal-Secret
- [x] Public endpoints rely on X-Merchant-Id forwarded by Gateway (not Firebase directly)
- [x] Service does not validate Firebase token directly (Firebase SDK kept but not used in routes)

## Quality

- [x] Alembic migrations exist (2 migrations, cover all 6 tables)
- [x] Unit tests pass (26/26)
- [ ] Integration tests pass (DB needed — not yet set up)
- [ ] Docker startup works end-to-end (requires Postgres; config valid)
- [x] Docs updated (architecture.md, api_contract.md, test_report.md, open_questions.md)
