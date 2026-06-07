"""Merchant feature flags."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


class MerchantFeatureFlags(Base):
    """Per-merchant feature flags (JSONB)."""

    __tablename__ = "merchant_feature_flags"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    flags: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    user = relationship("User", back_populates="merchant_feature_flags")
