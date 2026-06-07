# Test Report

**Last run:** 2026-04-13

## Results

| Suite | Status | Count | Notes |
|-------|--------|-------|-------|
| unit | PASS | 26 | All pass |
| integration | N/A | — | Requires running DB; not yet set up |
| docker-compose config | PASS | — | `docker compose config` exits 0 |
| Python syntax | PASS | — | All changed files compile |

## Command run

```
uv run pytest -q --tb=short
26 passed in 1.01s
```

## Test coverage by area

| Area | Tests |
|------|-------|
| `/v1/me` GET profile | test_me_routes.py |
| `/v1/me` 404 when not found | test_me_routes.py |
| `/v1/me/settings` GET + 404 | test_me_routes.py |
| `/v1/me/wallets` GET empty + with items | test_me_routes.py |
| `/v1/me/wallets/{id}` PATCH 404 | test_me_routes.py |
| `/v1/me/webhook` GET 404 | test_me_routes.py |
| Missing X-Merchant-Id → 401 | test_me_routes.py |
| `/health` 200 | test_me_routes.py |
| `/internal/merchant/{id}/capabilities` | test_internal_capabilities.py |
| `/internal/merchant/{id}/config` | test_internal_capabilities.py |
| Internal 403 without secret | test_internal_capabilities.py |
| Internal 404 unknown merchant | test_internal_capabilities.py |
| Limits schema | test_limits_schema.py |
| Wallet schema (Create + Update) | test_wallet_service.py |
| Internal API legacy paths | test_internal_api.py |

## Failures

None.
