# User Service Scope

## Purpose

User Service is the merchant identity and configuration registry.

## Owns

- merchant profile
- merchant status
- merchant capabilities
- payout wallets
- webhook configuration
- merchant limits
- feature flags

## Must not own

- products
- paywalls
- invoices
- payment intents
- payment analytics
- blockchain transactions
- private keys

## MVP entities

- Merchant
- MerchantSettings
- Wallet
- WebhookConfig
- MerchantLimits
- MerchantFeatures

## MVP endpoints

- GET /health
- GET /v1/me
- PATCH /v1/me
- GET /v1/me/settings
- PATCH /v1/me/settings
- GET /v1/me/wallets
- POST /v1/me/wallets
- PATCH /v1/me/wallets/{wallet_id}
- DELETE /v1/me/wallets/{wallet_id}
- GET /v1/me/webhook
- PUT /v1/me/webhook
- GET /internal/merchant/{merchant_id}/config
- GET /internal/merchant/{merchant_id}/capabilities

## Auth assumptions

- External auth context is forwarded by API Gateway
- Gateway verifies Firebase token; User Service trusts forwarded headers
- Internal endpoints use X-Internal-Secret for MVP
- User Service does not validate Firebase tokens directly

## Done criteria

- Service runs in Docker
- Database migrations exist and apply cleanly
- Core endpoints work
- Tests cover main flows
- Docs are up to date
