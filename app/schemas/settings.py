"""Merchant settings Pydantic schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class MerchantSettingsBase(BaseModel):
    """Base merchant settings."""

    allowed_chains: list[str] = Field(default_factory=list)
    allowed_assets: list[str] = Field(default_factory=list)
    default_chain: str | None = None
    timezone: str | None = None


class MerchantSettingsResponse(MerchantSettingsBase):
    """Merchant settings as returned in API."""

    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class MerchantSettingsUpdate(BaseModel):
    """Payload for PATCH /me/settings."""

    allowed_chains: list[str] | None = None
    allowed_assets: list[str] | None = None
    default_chain: str | None = None
    timezone: str | None = None
