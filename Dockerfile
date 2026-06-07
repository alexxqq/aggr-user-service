# Production-ready Dockerfile for user-service (UV)
FROM python:3.12-slim

WORKDIR /app

# Install UV
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy dependency files first for layer caching
COPY pyproject.toml requirements.txt ./

# Install dependencies (no dev)
RUN uv pip install --system --no-cache -r requirements.txt

# Copy application (.dockerignore excludes .env, .venv, __pycache__)
COPY . .

# Non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8002

ENV PYTHONUNBUFFERED=1

# Copy and make entrypoint executable
COPY --chown=appuser:appuser entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

ENTRYPOINT ["/app/entrypoint.sh"]
