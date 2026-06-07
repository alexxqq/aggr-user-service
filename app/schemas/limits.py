"""Merchant limits Pydantic schemas."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class MerchantLimitsBase(BaseModel):
    """Base limits fields."""

    max_txs_per_day: int | None = None
    max_pending_invoices: int | None = None
    max_single_tx_amount_usd: Decimal | None = None


class MerchantLimitsResponse(MerchantLimitsBase):
    """Limits as returned in API."""

    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class MerchantLimitsUpdate(BaseModel):
    """Payload for PATCH /me/limits."""

    max_txs_per_day: int | None = Field(None, ge=0)
    max_pending_invoices: int | None = Field(None, ge=0)
    max_single_tx_amount_usd: Decimal | None = Field(None, ge=0)
