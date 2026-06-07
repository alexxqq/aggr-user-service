"""Merchant limits (anti-abuse / gas sponsorship)."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


class MerchantLimits(Base):
    """Per-merchant limits for gas sponsorship and anti-abuse."""

    __tablename__ = "merchant_limits"

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
    max_txs_per_day: Mapped[int | None] = mapped_column(Integer, nullable=True)
    max_pending_invoices: Mapped[int | None] = mapped_column(Integer, nullable=True)
    max_single_tx_amount_usd: Mapped[float | None] = mapped_column(
        Numeric(20, 2),
        nullable=True,
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

    user = relationship("User", back_populates="merchant_limits")
