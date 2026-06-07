"""Unit tests for /internal/merchant/{id}/capabilities endpoint."""

import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.db import get_db
from app.main import app

INTERNAL_SECRET = "test-secret"
MERCHANT_ID = uuid.uuid4()


async def _mock_db():
    yield AsyncMock()


@pytest.fixture(autouse=True)
def override_db():
    app.dependency_overrides[get_db] = _mock_db
    yield
    app.dependency_overrides.pop(get_db, None)


@pytest.fixture(autouse=True)
def patch_secret():
    with patch("app.core.security.get_settings") as m:
        m.return_value.internal_api_secret = INTERNAL_SECRET
        yield


def _make_user(status="active", chains=None, assets=None, default_chain=None):
    settings = SimpleNamespace(
        allowed_chains=chains or [],
        allowed_assets=assets or [],
        default_chain=default_chain,
    )
    return SimpleNamespace(
        id=MERCHANT_ID,
        firebase_uid="uid-xyz",
        status=status,
        merchant_settings=settings,
        wallets=[],
        webhook_config=None,
        merchant_limits=None,
    )


@pytest.mark.asyncio
async def test_capabilities_returns_correct_structure():
    """GET /internal/merchant/{id}/capabilities returns status + chains + assets."""
    user = _make_user(chains=["ethereum", "polygon"], assets=["USDT"], default_chain="ethereum")
    with patch("app.api.routes_internal.user_service.get_user_by_id", new_callable=AsyncMock) as m:
        m.return_value = user
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            r = await c.get(
                f"/internal/merchant/{MERCHANT_ID}/capabilities",
                headers={"X-Internal-Secret": INTERNAL_SECRET},
            )
    assert r.status_code == 200
    data = r.json()
    assert data["merchant_id"] == str(MERCHANT_ID)
    assert data["status"] == "active"
    assert data["is_active"] is True
    assert "ethereum" in data["allowed_chains"]
    assert data["default_chain"] == "ethereum"


@pytest.mark.asyncio
async def test_capabilities_disabled_merchant():
    """Disabled merchant returns is_active=False."""
    user = _make_user(status="disabled")
    with patch("app.api.routes_internal.user_service.get_user_by_id", new_callable=AsyncMock) as m:
        m.return_value = user
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            r = await c.get(
                f"/internal/merchant/{MERCHANT_ID}/capabilities",
                headers={"X-Internal-Secret": INTERNAL_SECRET},
            )
    assert r.status_code == 200
    assert r.json()["is_active"] is False


@pytest.mark.asyncio
async def test_capabilities_404_unknown_merchant():
    """GET /internal/merchant/{id}/capabilities returns 404 for unknown merchant."""
    with patch("app.api.routes_internal.user_service.get_user_by_id", new_callable=AsyncMock) as m:
        m.return_value = None
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            r = await c.get(
                f"/internal/merchant/{uuid.uuid4()}/capabilities",
                headers={"X-Internal-Secret": INTERNAL_SECRET},
            )
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_capabilities_403_without_secret():
    """GET /internal/merchant/{id}/capabilities returns 403 without secret."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        r = await c.get(f"/internal/merchant/{MERCHANT_ID}/capabilities")
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_internal_config_path():
    """GET /internal/merchant/{id}/config returns full config."""
    user = _make_user(chains=["ethereum"])
    with patch("app.api.routes_internal.user_service.get_user_by_id", new_callable=AsyncMock) as m:
        m.return_value = user
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            r = await c.get(
                f"/internal/merchant/{MERCHANT_ID}/config",
                headers={"X-Internal-Secret": INTERNAL_SECRET},
            )
    assert r.status_code == 200
    data = r.json()
    assert data["merchant_id"] == str(MERCHANT_ID)
    assert "allowed_chains" in data
