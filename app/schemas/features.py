"""Merchant feature flags Pydantic schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class MerchantFeatureFlagsResponse(BaseModel):
    """Feature flags as returned in API."""

    id: UUID
    user_id: UUID
    flags: dict
    updated_at: datetime

    model_config = {"from_attributes": True}


class MerchantFeatureFlagsUpdate(BaseModel):
    """Payload for PATCH /me/features."""

    flags: dict | None = None
