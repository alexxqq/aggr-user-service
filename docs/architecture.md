# User Service Architecture

## Overview

FastAPI service responsible for merchant identity, configuration, and capabilities.
Acts as the source of truth for merchant state within the aggregator platform.

## Layer structure

```
app/
├── api/           # FastAPI routers (HTTP boundary)
├── core/          # Config, DB session, security helpers
├── models/        # SQLAlchemy ORM models
├── schemas/       # Pydantic request/response schemas
├── services/      # Business logic
└── repositories/  # DB access layer
```

## Auth flow

```
Client → API Gateway (verifies Firebase token)
       → User Service (trusts X-Merchant-Id / forwarded headers)
```

Internal service-to-service calls use `X-Internal-Secret`.

## Database

PostgreSQL via SQLAlchemy + Alembic.

Tables: `merchants`, `merchant_settings`, `wallets`, `webhook_configs`, `merchant_limits`, `merchant_features`

## Key design decisions

- No Firebase SDK calls inside this service
- No payment or blockchain logic here
- Repositories handle all DB access; services handle business rules
