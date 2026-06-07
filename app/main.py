"""FastAPI application entrypoint."""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes_internal import router as internal_router
from app.api.routes_me import router as me_router
from app.core.config import get_settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/shutdown lifecycle."""
    yield
    # Add any cleanup (e.g. close pool) if needed


def create_app() -> FastAPI:
    """Application factory."""
    settings = get_settings()
    app = FastAPI(
        title="User Service",
        description="Merchant user configuration for blockchain payment aggregator",
        version="0.1.0",
        lifespan=lifespan,
    )
    app.include_router(me_router)
    app.include_router(internal_router)
    return app


app = create_app()


@app.get("/health")
async def health():
    """Liveness/readiness probe."""
    return {"status": "ok"}
