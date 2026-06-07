"""Merchant settings model."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


class MerchantSettings(Base):
    """Per-user merchant configuration."""

    __tablename__ = "merchant_settings"

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
    allowed_chains: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    allowed_assets: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    default_chain: Mapped[str | None] = mapped_column(String(64), nullable=True)
    timezone: Mapped[str | None] = mapped_column(String(64), nullable=True)
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

    user = relationship("User", back_populates="merchant_settings")
