"""User-related Pydantic schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.user import UserStatus


class UserProfileBase(BaseModel):
    """Base user profile fields."""

    email: str | None = None
    display_name: str | None = None
    status: UserStatus = UserStatus.ACTIVE


class UserProfileResponse(UserProfileBase):
    """User profile as returned in API."""

    id: UUID
    firebase_uid: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class UserProfileUpdate(BaseModel):
    """Payload for PATCH /me/profile."""

    display_name: str | None = Field(None, max_length=255)


class UserProfileCreate(BaseModel):
    """Minimal fields for user creation (from Firebase claims)."""

    firebase_uid: str
    email: str | None = None
    display_name: str | None = None
