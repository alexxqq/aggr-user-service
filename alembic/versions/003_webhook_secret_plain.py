"""Store webhook signing secret in plaintext for HMAC dispatch.

Webhook secrets are signing keys (not passwords). The service needs the
raw secret to compute HMAC-SHA256 signatures on outgoing webhook calls.
The existing secret_hash (SHA-256) column is kept for backward compatibility.

Revision ID: 003
Revises: f0e5e829a6f3
Create Date: 2026-05-31
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "003"
down_revision: Union[str, None] = "f0e5e829a6f3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "webhook_config",
        sa.Column("secret_plain", sa.String(255), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("webhook_config", "secret_plain")
