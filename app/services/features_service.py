"""Merchant feature flags business logic."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import MerchantFeatureFlags
from app.schemas.features import MerchantFeatureFlagsUpdate


async def get_or_create_feature_flags(
    db: AsyncSession,
    user_id: UUID,
) -> MerchantFeatureFlags:
    """Get existing feature flags or create with empty dict."""
    result = await db.execute(
        select(MerchantFeatureFlags).where(MerchantFeatureFlags.user_id == user_id)
    )
    flags_row = result.scalar_one_or_none()
    if flags_row:
        return flags_row
    flags_row = MerchantFeatureFlags(user_id=user_id, flags={})
    db.add(flags_row)
    await db.flush()
    return flags_row


async def update_feature_flags(
    db: AsyncSession,
    user_id: UUID,
    payload: MerchantFeatureFlagsUpdate,
) -> MerchantFeatureFlags:
    """Update feature flags (merge or replace)."""
    flags_row = await get_or_create_feature_flags(db, user_id)
    if payload.flags is not None:
        flags_row.flags = payload.flags
    await db.flush()
    return flags_row
