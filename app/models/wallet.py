"""Wallet model."""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


class Wallet(Base):
    """User wallet per chain/address."""

    __tablename__ = "wallets"
    __table_args__ = (
        UniqueConstraint("user_id", "chain", "address", name="uq_wallets_user_chain_address"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    chain: Mapped[str] = mapped_column(String(64), nullable=False)
    address: Mapped[str] = mapped_column(String(255), nullable=False)
    label: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_default: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
    )

    user = relationship("User", back_populates="wallets")
