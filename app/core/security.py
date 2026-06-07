"""Security helpers: forwarded-header auth (MVP) and internal API protection.

Auth model (MVP):
- External /v1/* endpoints: API Gateway verifies Firebase token, forwards
  X-Merchant-Id (UUID) downstream. This service trusts that header.
- Internal /internal/* endpoints: validated by X-Internal-Secret.
- Firebase SDK kept for optional direct verification; NOT used in routes by default.
"""

import asyncio
from pathlib import Path
from typing import Annotated, Optional
from uuid import UUID

import firebase_admin
from fastapi import Depends, Header, HTTPException, status
from firebase_admin import auth, credentials

from app.core.config import get_settings

_settings = get_settings()
_firebase_app: Optional[firebase_admin.App] = None


def _resolve_credentials_path(path_str: str) -> str:
    """Resolve to absolute path so it works regardless of cwd."""
    p = Path(path_str)
    if not p.is_absolute():
        p = Path.cwd() / p
    return str(p.resolve())


def get_firebase_app() -> firebase_admin.App:
    """Initialize and return Firebase Admin app (singleton)."""
    global _firebase_app
    if _firebase_app is None:
        cred_path = (
            _settings.firebase_credentials_path
            or _settings.google_application_credentials
        )
        if cred_path:
            path = _resolve_credentials_path(cred_path)
            cred = credentials.Certificate(path)
            _firebase_app = firebase_admin.initialize_app(cred)
        else:
            _firebase_app = firebase_admin.initialize_app()
    return _firebase_app


def _verify_id_token_sync(id_token: str, app: firebase_admin.App) -> dict:
    """Sync wrapper for Firebase verify_id_token (runs in thread)."""
    return auth.verify_id_token(id_token, app=app)


async def verify_firebase_token(id_token: str) -> dict:
    """
    Verify Firebase ID token and return decoded claims.
    Raises HTTPException if token is invalid.
    """
    app = get_firebase_app()
    try:
        decoded = await asyncio.to_thread(_verify_id_token_sync, id_token, app)
        return decoded
    except auth.ExpiredIdTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
        )
    except auth.InvalidIdTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=(
                "Invalid or expired token. Ensure FIREBASE_CREDENTIALS_PATH or "
                "GOOGLE_APPLICATION_CREDENTIALS points to your project's service account JSON."
            ),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed",
        ) from e


async def get_firebase_claims(
    authorization: Annotated[Optional[str], Header()] = None,
) -> dict:
    """
    Extract Bearer token, verify with Firebase, return decoded claims.
    Use when you need uid, email, name, etc.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header",
        )
    token = authorization.split(" ", 1)[1].strip()
    decoded = await verify_firebase_token(token)
    if not decoded.get("uid"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token claims",
        )
    return decoded


async def get_current_firebase_uid(
    claims: dict = Depends(get_firebase_claims),
) -> str:
    """Return firebase_uid from verified token claims."""
    return claims["uid"]


async def verify_internal_secret(
    x_internal_secret: Annotated[Optional[str], Header(alias="X-Internal-Secret")] = None,
) -> None:
    """Validate internal service token. Raise 403 if missing or wrong."""
    secret = get_settings().internal_api_secret
    if not secret or x_internal_secret != secret:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden",
        )


async def get_merchant_id_from_header(
    x_merchant_id: Annotated[Optional[str], Header(alias="X-Merchant-Id")] = None,
) -> UUID:
    """
    Extract merchant UUID from X-Merchant-Id header forwarded by API Gateway.
    Gateway is responsible for Firebase token verification; this service trusts the header.
    """
    if not x_merchant_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing X-Merchant-Id header",
        )
    try:
        return UUID(x_merchant_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid X-Merchant-Id format (must be UUID)",
        )
