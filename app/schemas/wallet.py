"""Wallet Pydantic schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class WalletBase(BaseModel):
    """Base wallet fields."""

    chain: str = Field(..., max_length=64)
    address: str = Field(..., max_length=255)
    label: str | None = Field(None, max_length=255)
    is_default: bool = False


class WalletResponse(WalletBase):
    """Wallet as returned in API."""

    id: UUID
    user_id: UUID
    created_at: datetime

    model_config = {"from_attributes": True}


class WalletCreate(WalletBase):
    """Payload for POST /me/wallets."""

    pass


class WalletUpdate(BaseModel):
    """Payload for PATCH /me/wallets/{wallet_id}."""

    label: str | None = Field(None, max_length=255)
    is_default: bool | None = None
