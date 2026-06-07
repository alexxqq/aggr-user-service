# Open Questions

> Record ambiguities here. Proceed with the safest MVP assumption and note it.

| # | Question | MVP assumption | Resolved? |
|---|----------|----------------|-----------|
| 1 | Should User Service validate Firebase token directly? | No — Gateway handles it; service trusts X-Merchant-Id header forwarded by Gateway. Firebase SDK kept in security.py but NOT used in routes. | Yes (resolved in MVP) |
| 2 | Wallet uniqueness constraints? | One wallet per (merchant, chain, address) tuple — enforced by DB unique constraint. | Yes |
| 3 | How does API Gateway get merchant_id on first login? | Gateway calls `POST /internal/merchant/init` with firebase_uid after verifying Firebase token. Gets back merchant_id and caches it. | Yes (endpoint implemented) |
| 4 | Should POST /me/init remain as a public endpoint? | Removed from public routes. Bootstrap is now done via `POST /internal/merchant/init` by Gateway. | Yes |
| 5 | ruff/black not installed in project dev deps — hooks will silently skip | Acceptable for MVP. Add ruff to dev-dependencies if formatter enforcement is needed in CI. | No (low priority) |
