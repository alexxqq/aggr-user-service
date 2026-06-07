"""Webhook config Pydantic schemas. Server generates secret; plain returned only on create/rotate."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class WebhookConfigResponse(BaseModel):
    """Webhook config as returned in API. Never includes secret_hash. Optional secret only on create/rotate."""

    id: UUID
    user_id: UUID
    webhook_url: str
    is_enabled: bool
    created_at: datetime
    updated_at: datetime
    secret: str | None = None  # Only set when just created or rotated; never in GET

    model_config = {"from_attributes": True}


class WebhookConfigUpsert(BaseModel):
    """Payload for PUT /me/webhook. Server generates secret; client does not send it."""

    webhook_url: str = Field(..., max_length=2048)
    is_enabled: bool = True


class WebhookRotateResponse(BaseModel):
    """Response for POST /me/webhook/rotate. Plain secret returned once."""

    secret: str
    webhook_url: str
    is_enabled: bool
