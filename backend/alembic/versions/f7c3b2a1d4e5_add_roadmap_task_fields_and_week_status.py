"""add roadmap task fields and week status

Revision ID: f7c3b2a1d4e5
Revises: 9bea56ea4690
Create Date: 2026-06-10 12:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f7c3b2a1d4e5"
down_revision: Union[str, None] = "9bea56ea4690"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "roadmap_tasks",
        sa.Column("goal_id", sa.UUID(as_uuid=False), nullable=True),
    )
    op.add_column(
        "roadmap_tasks",
        sa.Column("user_id", sa.UUID(as_uuid=False), nullable=True),
    )
    op.add_column(
        "roadmap_tasks",
        sa.Column("day_offset", sa.Integer(), nullable=True),
    )
    op.add_column(
        "roadmap_tasks",
        sa.Column("assigned_date", sa.Date(), nullable=True),
    )
    op.create_foreign_key(
        "fk_roadmap_tasks_goal_id",
        "roadmap_tasks", "goals",
        ["goal_id"], ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "fk_roadmap_tasks_user_id",
        "roadmap_tasks", "users",
        ["user_id"], ["id"],
        ondelete="CASCADE",
    )
    op.create_index(op.f("ix_roadmap_tasks_assigned_date"), "roadmap_tasks", ["assigned_date"], unique=False)
    op.create_index(op.f("ix_roadmap_tasks_user_id"), "roadmap_tasks", ["user_id"], unique=False)
    op.add_column(
        "roadmap_weeks",
        sa.Column("start_date", sa.Date(), nullable=True),
    )
    op.add_column(
        "roadmap_weeks",
        sa.Column("status", sa.String(length=20), nullable=False, server_default=sa.text("'pending'")),
    )


def downgrade() -> None:
    op.drop_column("roadmap_weeks", "status")
    op.drop_column("roadmap_weeks", "start_date")
    op.drop_index(op.f("ix_roadmap_tasks_user_id"), table_name="roadmap_tasks")
    op.drop_index(op.f("ix_roadmap_tasks_assigned_date"), table_name="roadmap_tasks")
    op.drop_constraint("fk_roadmap_tasks_user_id", "roadmap_tasks", type_="foreignkey")
    op.drop_constraint("fk_roadmap_tasks_goal_id", "roadmap_tasks", type_="foreignkey")
    op.drop_column("roadmap_tasks", "assigned_date")
    op.drop_column("roadmap_tasks", "day_offset")
    op.drop_column("roadmap_tasks", "user_id")
    op.drop_column("roadmap_tasks", "goal_id")
