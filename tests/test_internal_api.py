"""Tests for internal API (no Firebase)."""

import uuid
from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.db import get_db
from app.main import app


async def mock_get_db():
    """Yield a mock session so routes don't need a real DB."""
    yield AsyncMock()


@pytest.fixture
def internal_secret():
    """Secret matching patched config."""
    return "test-internal-secret"


@pytest.fixture(autouse=True)
def patch_internal_secret(internal_secret):
    """Patch get_settings so internal API accepts test secret."""
    with patch("app.core.security.get_settings") as m:
        m.return_value.internal_api_secret = internal_secret
        yield


@pytest.fixture(autouse=True)
def override_get_db():
    """Override get_db so tests don't need a real database."""
    app.dependency_overrides[get_db] = mock_get_db
    yield
    app.dependency_overrides.pop(get_db, None)


@pytest.fixture(autouse=True)
def patch_user_service():
    """Patch user_service so get_user_by_id / get_user_by_firebase_uid return None (404)."""
    with patch("app.api.routes_internal.user_service.get_user_by_id", new_callable=AsyncMock) as m1:
        with patch("app.api.routes_internal.user_service.get_user_by_firebase_uid", new_callable=AsyncMock) as m2:
            m1.return_value = None
            m2.return_value = None
            yield


@pytest.mark.asyncio
async def test_internal_merchant_not_found(internal_secret):
    """GET /internal/merchants/{merchant_id} returns 404 for unknown UUID."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        r = await client.get(
            f"/internal/merchants/{uuid.uuid4()}",
            headers={"X-Internal-Secret": internal_secret},
        )
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_internal_merchant_forbidden_without_secret():
    """GET /internal/merchants/{id} returns 403 without X-Internal-Secret."""
    with patch("app.core.security.get_settings") as m:
        m.return_value.internal_api_secret = "any"
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            r = await client.get(f"/internal/merchants/{uuid.uuid4()}")
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_internal_users_not_found(internal_secret):
    """GET /internal/users/{firebase_uid} returns 404 for unknown UID."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        r = await client.get(
            "/internal/users/unknown-firebase-uid-123",
            headers={"X-Internal-Secret": internal_secret},
        )
    assert r.status_code == 404
