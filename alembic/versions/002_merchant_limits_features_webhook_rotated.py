"""Add merchant_limits, merchant_feature_flags, webhook secret_rotated_at.

Revision ID: 002
Revises: 001
Create Date: 2025-02-24

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "merchant_limits",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("max_txs_per_day", sa.Integer(), nullable=True),
        sa.Column("max_pending_invoices", sa.Integer(), nullable=True),
        sa.Column("max_single_tx_amount_usd", sa.Numeric(20, 2), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", name="merchant_limits_user_id_key"),
    )

    op.create_table(
        "merchant_feature_flags",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("flags", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", name="merchant_feature_flags_user_id_key"),
    )

    op.add_column(
        "webhook_config",
        sa.Column("secret_rotated_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("webhook_config", "secret_rotated_at")
    op.drop_table("merchant_feature_flags")
    op.drop_table("merchant_limits")
