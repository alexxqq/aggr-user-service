"""User and merchant settings business logic."""

import hashlib
import secrets
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import MerchantFeatureFlags, MerchantLimits, MerchantSettings, User, WebhookConfig
from app.models.user import UserStatus
from app.schemas.settings import MerchantSettingsUpdate
from app.schemas.user import UserProfileUpdate

_USER_RELATIONS = [
    selectinload(User.merchant_settings),
    selectinload(User.wallets),
    selectinload(User.webhook_config),
    selectinload(User.merchant_limits),
    selectinload(User.merchant_feature_flags),
]


def _hash_secret(plain: str) -> str:
    """Store-safe hash of webhook secret."""
    return hashlib.sha256(plain.encode()).hexdigest()


def _generate_webhook_secret() -> str:
    """Generate a secret for webhook signing (return plain; caller hashes for storage)."""
    return f"whsec_{secrets.token_hex(32)}"


async def get_user_by_firebase_uid(db: AsyncSession, firebase_uid: str) -> User | None:
    """Load user by Firebase UID with settings, wallets, webhook, limits, feature_flags."""
    result = await db.execute(
        select(User).options(*_USER_RELATIONS).where(User.firebase_uid == firebase_uid)
    )
    return result.scalar_one_or_none()


async def get_user_by_id(db: AsyncSession, user_id: UUID) -> User | None:
    """Load user by primary key with relations."""
    result = await db.execute(
        select(User).options(*_USER_RELATIONS).where(User.id == user_id)
    )
    return result.scalar_one_or_none()


async def init_user(
    db: AsyncSession,
    firebase_uid: str,
    email: str | None = None,
    display_name: str | None = None,
) -> User:
    """
    Create user, merchant_settings, merchant_limits, merchant_feature_flags if not exist (idempotent).
    Handles concurrent init: unique on firebase_uid, re-fetch on conflict.
    """
    existing = await get_user_by_firebase_uid(db, firebase_uid)
    if existing:
        return existing

    try:
        user = User(
            firebase_uid=firebase_uid,
            email=email,
            display_name=display_name,
            status=UserStatus.ACTIVE,
        )
        db.add(user)
        await db.flush()

        settings = MerchantSettings(
            user_id=user.id,
            allowed_chains=["ethereum", "bsc", "tron"],
            allowed_assets=["USDT", "ETH", "BNB", "TRX"],
            default_chain="ethereum",
        )
        db.add(settings)
        await db.flush()

        limits = MerchantLimits(
            user_id=user.id,
            max_txs_per_day=100,
            max_pending_invoices=50,
        )
        db.add(limits)
        await db.flush()

        flags_row = MerchantFeatureFlags(user_id=user.id, flags={})
        db.add(flags_row)
        await db.flush()
        return user
    except IntegrityError:
        await db.rollback()
        existing = await get_user_by_firebase_uid(db, firebase_uid)
        if existing:
            return existing
        raise  # unexpected constraint


async def update_profile(
    db: AsyncSession,
    user_id: UUID,
    payload: UserProfileUpdate,
) -> User:
    """Update user display_name."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one()
    if payload.display_name is not None:
        user.display_name = payload.display_name
    await db.flush()
    return user


async def update_merchant_settings(
    db: AsyncSession,
    user_id: UUID,
    payload: MerchantSettingsUpdate,
) -> MerchantSettings:
    """Update merchant_settings for user."""
    result = await db.execute(
        select(MerchantSettings).where(MerchantSettings.user_id == user_id)
    )
    settings = result.scalar_one()
    if payload.allowed_chains is not None:
        settings.allowed_chains = payload.allowed_chains
    if payload.allowed_assets is not None:
        settings.allowed_assets = payload.allowed_assets
    if payload.default_chain is not None:
        settings.default_chain = payload.default_chain
    if payload.timezone is not None:
        settings.timezone = payload.timezone
    await db.flush()
    return settings


async def upsert_webhook(
    db: AsyncSession,
    user_id: UUID,
    webhook_url: str,
    is_enabled: bool = True,
) -> tuple[WebhookConfig, str | None]:
    """
    Create or update webhook config. Server generates secret; store hash only.
    Returns (config, plain_secret). plain_secret is set only when a new secret was generated (create or first set).
    """
    result = await db.execute(
        select(WebhookConfig).where(WebhookConfig.user_id == user_id)
    )
    config = result.scalar_one_or_none()
    plain_secret: str | None = None
    if config:
        config.webhook_url = webhook_url
        config.is_enabled = is_enabled
        if not config.secret_hash:
            plain_secret = _generate_webhook_secret()
            config.secret_hash = _hash_secret(plain_secret)
            config.secret_plain = plain_secret
        await db.flush()
        return config, plain_secret

    plain_secret = _generate_webhook_secret()
    config = WebhookConfig(
        user_id=user_id,
        webhook_url=webhook_url,
        secret_hash=_hash_secret(plain_secret),
        secret_plain=plain_secret,
        is_enabled=is_enabled,
    )
    db.add(config)
    await db.flush()
    return config, plain_secret


async def rotate_webhook_secret(db: AsyncSession, user_id: UUID) -> tuple[WebhookConfig, str]:
    """Rotate webhook secret: new secret, store hash, set secret_rotated_at. Returns (config, plain_secret)."""
    from sqlalchemy import update
    from datetime import datetime, timezone

    result = await db.execute(
        select(WebhookConfig).where(WebhookConfig.user_id == user_id)
    )
    config = result.scalar_one_or_none()
    if not config:
        raise ValueError("No webhook config to rotate")
    plain = _generate_webhook_secret()
    config.secret_hash = _hash_secret(plain)
    config.secret_plain = plain
    config.secret_rotated_at = datetime.now(timezone.utc)
    await db.flush()
    return config, plain
