"""Merchant limits business logic."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import MerchantLimits
from app.schemas.limits import MerchantLimitsUpdate

DEFAULT_MAX_TXS_PER_DAY = 100
DEFAULT_MAX_PENDING_INVOICES = 50


async def get_or_create_limits(
    db: AsyncSession,
    user_id: UUID,
) -> MerchantLimits:
    """Get existing limits or create with defaults."""
    result = await db.execute(
        select(MerchantLimits).where(MerchantLimits.user_id == user_id)
    )
    limits = result.scalar_one_or_none()
    if limits:
        return limits
    limits = MerchantLimits(
        user_id=user_id,
        max_txs_per_day=DEFAULT_MAX_TXS_PER_DAY,
        max_pending_invoices=DEFAULT_MAX_PENDING_INVOICES,
    )
    db.add(limits)
    await db.flush()
    return limits


async def update_limits(
    db: AsyncSession,
    user_id: UUID,
    payload: MerchantLimitsUpdate,
) -> MerchantLimits:
    """Update merchant limits."""
    result = await db.execute(
        select(MerchantLimits).where(MerchantLimits.user_id == user_id)
    )
    limits = result.scalar_one_or_none()
    if not limits:
        limits = await get_or_create_limits(db, user_id)
    if payload.max_txs_per_day is not None:
        limits.max_txs_per_day = payload.max_txs_per_day
    if payload.max_pending_invoices is not None:
        limits.max_pending_invoices = payload.max_pending_invoices
    if payload.max_single_tx_amount_usd is not None:
        limits.max_single_tx_amount_usd = payload.max_single_tx_amount_usd
    await db.flush()
    return limits
