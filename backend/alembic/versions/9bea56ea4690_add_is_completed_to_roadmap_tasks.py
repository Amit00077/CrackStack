"""add is_completed to roadmap_tasks

Revision ID: 9bea56ea4690
Revises: e8302869a07d
Create Date: 2026-06-07 12:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "9bea56ea4690"
down_revision: Union[str, None] = "e8302869a07d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "roadmap_tasks",
        sa.Column("is_completed", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )


def downgrade() -> None:
    op.drop_column("roadmap_tasks", "is_completed")
