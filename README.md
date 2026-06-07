# User Service

Production-ready FastAPI microservice for merchant user configuration in a blockchain payment aggregator. Firebase is used for authentication (ID token verification); user profile and configuration are stored in PostgreSQL.

## Tech stack

- **FastAPI** – API framework
- **PostgreSQL** – primary database
- **SQLAlchemy 2.0 (async)** – ORM with asyncpg
- **Alembic** – migrations
- **Pydantic v2** – validation and settings
- **Firebase Admin SDK** – ID token verification only
- **Docker** – containerized run

## Project structure

```
user-service/
├── app/
│   ├── api/
│   │   ├── routes_me.py      # Authenticated /me endpoints
│   │   └── routes_internal.py # Internal service API
│   ├── core/
│   │   ├── config.py
│   │   ├── db.py
│   │   └── security.py
│   ├── models/
│   ├── schemas/
│   ├── services/
│   └── main.py
├── alembic/
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml
├── requirements.txt
└── README.md
```

## Prerequisites

- Python 3.11+
- [UV](https://docs.astral.sh/uv/) for dependency management
- PostgreSQL 14+
- Firebase project with Admin SDK (service account key for token verification)

## Secrets (do not commit)

- **Never commit** `.env` or Firebase/Google **service account JSON** files. They are listed in `.gitignore` (e.g. `*firebase-adminsdk*.json`).
- On a new machine: copy `.env.example` → `.env`, set `DATABASE_URL` and `INTERNAL_API_SECRET`, then download a **new** service account key from [Firebase Console](https://console.firebase.google.com) → Project settings → Service accounts → Generate new private key, save it locally (e.g. `firebase-service-account.json`) and point `FIREBASE_CREDENTIALS_PATH` or `GOOGLE_APPLICATION_CREDENTIALS` at that path.
- If you ever pushed a key by mistake, revoke it in Google Cloud Console and generate a new key.

## Local setup (UV)

```bash
# From repo root
cd user-service

# Create virtualenv and install deps with UV
uv venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
uv pip install -r requirements.txt

# Copy env example and set variables
cp .env.example .env
# Edit .env: DATABASE_URL, FIREBASE_CREDENTIALS_PATH, INTERNAL_API_SECRET
```

## Environment variables

See `.env.example`. Main ones:

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | PostgreSQL URL, e.g. `postgresql+asyncpg://user:password@localhost:5432/user_service_db` |
| `FIREBASE_CREDENTIALS_PATH` | Path to Firebase service account JSON (or use `GOOGLE_APPLICATION_CREDENTIALS`) |
| `INTERNAL_API_SECRET` | Secret for internal service-to-service calls (header `X-Internal-Secret`) |

## Alembic migrations

```bash
# Ensure .env is set (DATABASE_URL must be set)
# Use sync URL for Alembic: postgresql://user:password@localhost:5432/user_service_db
# (env.py converts async URL to sync automatically)

# Create a new revision
alembic revision -m "description"

# Upgrade to latest
alembic upgrade head

# Downgrade one step
alembic downgrade -1
```

First run: `alembic upgrade head` applies the initial schema. Migration `002` adds `merchant_limits`, `merchant_feature_flags`, and `webhook_config.secret_rotated_at`.

## Run locally

```bash
# Terminal 1 – PostgreSQL (or use docker-compose only for postgres)
docker compose up -d postgres
# Wait for healthy, then:
alembic upgrade head

# Terminal 2 – App
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

API: http://localhost:8000  
Docs: http://localhost:8000/docs

## Run with Docker

```bash
# Build and run app + Postgres
docker compose up -d

# Apply migrations (run once, from host or inside container)
docker compose exec user-service alembic upgrade head

# Logs
docker compose logs -f user-service
```

## API overview

### Authenticated (Firebase Bearer token)

- **GET /me** – Full config (profile, merchant_settings, wallets, webhook_config, limits, feature_flags). **Auto-inits** user if missing.
- **POST /me/init** – Create user, settings, limits, feature_flags if not exist (idempotent).
- **PATCH /me/profile** – Update `display_name`.
- **PATCH /me/settings** – Update `allowed_chains`, `allowed_assets`, `default_chain`, `timezone`.
- **GET /me/limits**, **PATCH /me/limits** – Anti-abuse limits (max_txs_per_day, max_pending_invoices, etc.).
- **GET /me/features**, **PATCH /me/features** – Feature flags (JSONB).
- **POST /me/wallets**, **DELETE /me/wallets/{wallet_id}** – Payout wallets.
- **GET /me/webhook** – Webhook config (URL, enabled; secret never returned).
- **PUT /me/webhook** – Create or update webhook; **server generates secret**, returned **once** in response.
- **POST /me/webhook/rotate** – Rotate webhook secret; new secret returned once.

All `/me` requests require header: `Authorization: Bearer <Firebase ID token>`.

### Internal (service token, no Firebase)

Use **merchant_id** (UUID = `users.id`) for stable service-to-service contracts.

- **GET /internal/merchants/{merchant_id}** – Full config: status, settings, wallets, webhook_url, webhook_enabled, **limits**.  
  Header: `X-Internal-Secret: <INTERNAL_API_SECRET>`.
- **GET /internal/merchants/{merchant_id}/limits** – Limits only (e.g. before sponsoring gas).
- **GET /internal/users/{firebase_uid}** – Resolve firebase_uid → merchant_id + config (legacy).

### Health

- **GET /health** – Returns `{"status": "ok"}`.

## License

Proprietary / internal use.
