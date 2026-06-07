"""Unit tests for /v1/me endpoints (no real DB, no Firebase)."""

import uuid
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.db import get_db
from app.core.security import get_merchant_id_from_header
from app.main import app

MERCHANT_ID = uuid.uuid4()
INTERNAL_SECRET = "test-secret"


def _make_user(
    merchant_id=None,
    status="active",
    wallets=None,
    webhook=None,
    settings=None,
    limits=None,
    features=None,
):
    """Build a minimal User-like object."""
    now = datetime.now(timezone.utc)
    u = SimpleNamespace(
        id=merchant_id or MERCHANT_ID,
        firebase_uid="uid-abc",
        email="test@example.com",
        display_name="Test Merchant",
        status=status,
        created_at=now,
        updated_at=now,
        merchant_settings=settings,
        wallets=wallets or [],
        webhook_config=webhook,
        merchant_limits=limits,
        merchant_feature_flags=features,
    )
    return u


async def _mock_db():
    yield AsyncMock()


def _override_merchant_id():
    """Override get_merchant_id_from_header to return MERCHANT_ID."""
    return MERCHANT_ID


@pytest.fixture(autouse=True)
def override_db():
    app.dependency_overrides[get_db] = _mock_db
    yield
    app.dependency_overrides.pop(get_db, None)


@pytest.fixture(autouse=True)
def override_merchant_header():
    app.dependency_overrides[get_merchant_id_from_header] = _override_merchant_id
    yield
    app.dependency_overrides.pop(get_merchant_id_from_header, None)


@pytest.mark.asyncio
async def test_me_get_returns_full_profile():
    """GET /v1/me returns MeResponse when merchant exists."""
    user = _make_user()
    with patch("app.api.routes_me.user_service.get_user_by_id", new_callable=AsyncMock) as m:
        m.return_value = user
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            r = await c.get("/v1/me", headers={"X-Merchant-Id": str(MERCHANT_ID)})
    assert r.status_code == 200
    data = r.json()
    assert data["profile"]["email"] == "test@example.com"
    assert data["wallets"] == []


@pytest.mark.asyncio
async def test_me_get_404_when_not_found():
    """GET /v1/me returns 404 when merchant doesn't exist."""
    with patch("app.api.routes_me.user_service.get_user_by_id", new_callable=AsyncMock) as m:
        m.return_value = None
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            r = await c.get("/v1/me", headers={"X-Merchant-Id": str(MERCHANT_ID)})
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_me_get_settings_returns_settings():
    """GET /v1/me/settings returns settings when present."""
    now = datetime.now(timezone.utc)
    settings = SimpleNamespace(
        id=uuid.uuid4(),
        user_id=MERCHANT_ID,
        allowed_chains=["ethereum"],
        allowed_assets=["USDT"],
        default_chain="ethereum",
        timezone="UTC",
        created_at=now,
        updated_at=now,
    )
    user = _make_user(settings=settings)
    with patch("app.api.routes_me.user_service.get_user_by_id", new_callable=AsyncMock) as m:
        m.return_value = user
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            r = await c.get("/v1/me/settings", headers={"X-Merchant-Id": str(MERCHANT_ID)})
    assert r.status_code == 200
    data = r.json()
    assert data["allowed_chains"] == ["ethereum"]
    assert data["default_chain"] == "ethereum"


@pytest.mark.asyncio
async def test_me_get_settings_404_when_no_settings():
    """GET /v1/me/settings returns 404 if merchant has no settings."""
    user = _make_user(settings=None)
    with patch("app.api.routes_me.user_service.get_user_by_id", new_callable=AsyncMock) as m:
        m.return_value = user
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            r = await c.get("/v1/me/settings", headers={"X-Merchant-Id": str(MERCHANT_ID)})
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_me_get_wallets_empty():
    """GET /v1/me/wallets returns empty list."""
    user = _make_user(wallets=[])
    with patch("app.api.routes_me.user_service.get_user_by_id", new_callable=AsyncMock) as m:
        m.return_value = user
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            r = await c.get("/v1/me/wallets", headers={"X-Merchant-Id": str(MERCHANT_ID)})
    assert r.status_code == 200
    assert r.json() == []


@pytest.mark.asyncio
async def test_me_get_wallets_with_wallet():
    """GET /v1/me/wallets returns wallets."""
    now = datetime.now(timezone.utc)
    wallet = SimpleNamespace(
        id=uuid.uuid4(),
        user_id=MERCHANT_ID,
        chain="ethereum",
        address="0xABC",
        label="main",
        is_default=True,
        created_at=now,
    )
    user = _make_user(wallets=[wallet])
    with patch("app.api.routes_me.user_service.get_user_by_id", new_callable=AsyncMock) as m:
        m.return_value = user
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            r = await c.get("/v1/me/wallets", headers={"X-Merchant-Id": str(MERCHANT_ID)})
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 1
    assert data[0]["chain"] == "ethereum"
    assert data[0]["address"] == "0xABC"


@pytest.mark.asyncio
async def test_me_patch_wallet_not_found():
    """PATCH /v1/me/wallets/{id} returns 404 if wallet not found."""
    user = _make_user()
    with patch("app.api.routes_me.user_service.get_user_by_id", new_callable=AsyncMock) as mu:
        mu.return_value = user
        with patch("app.api.routes_me.wallet_service.update_wallet", new_callable=AsyncMock) as mw:
            mw.return_value = None
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
                r = await c.patch(
                    f"/v1/me/wallets/{uuid.uuid4()}",
                    json={"label": "new-label"},
                    headers={"X-Merchant-Id": str(MERCHANT_ID)},
                )
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_me_get_webhook_404_when_not_configured():
    """GET /v1/me/webhook returns 404 when no webhook configured."""
    user = _make_user(webhook=None)
    with patch("app.api.routes_me.user_service.get_user_by_id", new_callable=AsyncMock) as m:
        m.return_value = user
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            r = await c.get("/v1/me/webhook", headers={"X-Merchant-Id": str(MERCHANT_ID)})
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_me_missing_merchant_id_header():
    """GET /v1/me returns 401 when X-Merchant-Id header is missing."""
    app.dependency_overrides.pop(get_merchant_id_from_header, None)
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            r = await c.get("/v1/me")
        assert r.status_code == 401
    finally:
        app.dependency_overrides[get_merchant_id_from_header] = _override_merchant_id


@pytest.mark.asyncio
async def test_health_endpoint():
    """GET /health returns 200."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        r = await c.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}
