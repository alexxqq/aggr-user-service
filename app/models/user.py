"""User model."""

import uuid
from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import DateTime, Enum, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.core.db import Base


class UserStatus(str, PyEnum):
    """User account status."""

    ACTIVE = "active"
    DISABLED = "disabled"


class User(Base):
    """Merchant user linked to Firebase."""

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    firebase_uid: Mapped[str] = mapped_column(
        String(128),
        unique=True,
        nullable=False,
        index=True,
    )
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    display_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[UserStatus] = mapped_column(
        Enum(UserStatus),
        nullable=False,
        default=UserStatus.ACTIVE,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    merchant_settings = relationship(
        "MerchantSettings",
        back_populates="user",
        uselist=False,
    )
    wallets = relationship("Wallet", back_populates="user")
    webhook_config = relationship(
        "WebhookConfig",
        back_populates="user",
        uselist=False,
    )
    merchant_limits = relationship(
        "MerchantLimits",
        back_populates="user",
        uselist=False,
    )
    merchant_feature_flags = relationship(
        "MerchantFeatureFlags",
        back_populates="user",
        uselist=False,
    )
