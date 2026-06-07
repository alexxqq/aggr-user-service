"""Wallet business logic."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Wallet
from app.schemas.wallet import WalletUpdate


async def add_wallet(
    db: AsyncSession,
    user_id: UUID,
    chain: str,
    address: str,
    label: str | None = None,
    is_default: bool = False,
) -> Wallet:
    """
    Add a wallet for user. If is_default=True, unset other defaults for this user.
    """
    if is_default:
        result = await db.execute(select(Wallet).where(Wallet.user_id == user_id))
        for w in result.scalars().all():
            w.is_default = False
        await db.flush()

    wallet = Wallet(
        user_id=user_id,
        chain=chain,
        address=address,
        label=label,
        is_default=is_default,
    )
    db.add(wallet)
    await db.flush()
    return wallet


async def get_wallet_by_id(db: AsyncSession, wallet_id: UUID, user_id: UUID) -> Wallet | None:
    """Get wallet by id ensuring it belongs to user."""
    result = await db.execute(
        select(Wallet).where(Wallet.id == wallet_id, Wallet.user_id == user_id)
    )
    return result.scalar_one_or_none()


async def update_wallet(
    db: AsyncSession,
    wallet_id: UUID,
    user_id: UUID,
    payload: WalletUpdate,
) -> Wallet | None:
    """
    Update wallet label and/or is_default flag.
    If is_default is set to True, unsets other defaults for this user.
    Returns None if wallet not found or not owned by user.
    """
    wallet = await get_wallet_by_id(db, wallet_id, user_id)
    if not wallet:
        return None

    if payload.is_default is True:
        result = await db.execute(select(Wallet).where(Wallet.user_id == user_id))
        for w in result.scalars().all():
            w.is_default = False
        await db.flush()

    if payload.label is not None:
        wallet.label = payload.label
    if payload.is_default is not None:
        wallet.is_default = payload.is_default

    await db.flush()
    return wallet


async def delete_wallet(db: AsyncSession, wallet_id: UUID, user_id: UUID) -> bool:
    """Delete wallet if it belongs to user. Returns True if deleted."""
    wallet = await get_wallet_by_id(db, wallet_id, user_id)
    if not wallet:
        return False
    await db.delete(wallet)
    await db.flush()
    return True
