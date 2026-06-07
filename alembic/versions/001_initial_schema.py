"""Initial schema: users, merchant_settings, wallets, webhook_config.

Revision ID: 001
Revises:
Create Date: 2025-02-24

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("firebase_uid", sa.String(128), nullable=False),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("display_name", sa.String(255), nullable=True),
        sa.Column(
            "status",
            sa.Enum("ACTIVE", "DISABLED", name="userstatus"),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_users_firebase_uid"),
        "users",
        ["firebase_uid"],
        unique=True,
    )

    op.create_table(
        "merchant_settings",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "allowed_chains",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column(
            "allowed_assets",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column("default_chain", sa.String(64), nullable=True),
        sa.Column("timezone", sa.String(64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", name="merchant_settings_user_id_key"),
    )

    op.create_table(
        "wallets",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("chain", sa.String(64), nullable=False),
        sa.Column("address", sa.String(255), nullable=False),
        sa.Column("label", sa.String(255), nullable=True),
        sa.Column("is_default", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "user_id",
            "chain",
            "address",
            name="uq_wallets_user_chain_address",
        ),
    )

    op.create_table(
        "webhook_config",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("webhook_url", sa.String(2048), nullable=False),
        sa.Column("secret_hash", sa.String(255), nullable=True),
        sa.Column("is_enabled", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", name="webhook_config_user_id_key"),
    )


def downgrade() -> None:
    op.drop_table("webhook_config")
    op.drop_table("wallets")
    op.drop_table("merchant_settings")
    op.drop_index(op.f("ix_users_firebase_uid"), table_name="users")
    op.drop_table("users")
    op.execute("DROP TYPE userstatus")
