#!/bin/bash
set -e

# If GOOGLE_APPLICATION_CREDENTIALS contains JSON, write it to a file
if [[ -n "$GOOGLE_APPLICATION_CREDENTIALS" && "$GOOGLE_APPLICATION_CREDENTIALS" == *"{"* ]]; then
  CRED_FILE="/tmp/firebase-credentials.json"
  echo "$GOOGLE_APPLICATION_CREDENTIALS" > "$CRED_FILE"
  export GOOGLE_APPLICATION_CREDENTIALS="$CRED_FILE"
  echo "✓ Wrote Firebase credentials to $CRED_FILE"
fi

# Run migrations if needed
if [[ "${RUN_MIGRATIONS:-false}" == "true" ]]; then
  echo "Running Alembic migrations..."
  alembic upgrade head
fi

# Start the app
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8002}"
