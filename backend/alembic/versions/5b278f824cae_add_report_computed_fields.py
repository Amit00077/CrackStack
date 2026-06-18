"""add_report_computed_fields

Revision ID: 5b278f824cae
Revises: f7c3b2a1d4e5
Create Date: 2026-06-15 02:56:29.698316
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '5b278f824cae'
down_revision: Union[str, None] = 'f7c3b2a1d4e5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_index(op.f('ix_roadmap_tasks_assigned_date'), table_name='roadmap_tasks')
    op.drop_index(op.f('ix_roadmap_tasks_user_id'), table_name='roadmap_tasks')

    op.add_column('weekly_reports', sa.Column('week_number', sa.Integer(), nullable=True))
    op.add_column('weekly_reports', sa.Column('letter_grade', sa.String(length=2), nullable=True))
    op.add_column('weekly_reports', sa.Column('verdict', sa.String(length=20), nullable=True))
    op.add_column('weekly_reports', sa.Column('is_current', sa.Boolean(), nullable=True, server_default=sa.text('false')))
    op.add_column('weekly_reports', sa.Column('completed_tasks', sa.Integer(), nullable=True, server_default=sa.text('0')))
    op.add_column('weekly_reports', sa.Column('total_tasks', sa.Integer(), nullable=True, server_default=sa.text('0')))
    op.add_column('weekly_reports', sa.Column('strengths', postgresql.JSONB(astext_type=sa.Text()), nullable=True, server_default=sa.text("'[]'::jsonb")))
    op.add_column('weekly_reports', sa.Column('improvement_areas', postgresql.JSONB(astext_type=sa.Text()), nullable=True, server_default=sa.text("'[]'::jsonb")))
    op.add_column('weekly_reports', sa.Column('recommendations', postgresql.JSONB(astext_type=sa.Text()), nullable=True, server_default=sa.text("'[]'::jsonb")))
    op.add_column('weekly_reports', sa.Column('ai_generated', sa.Boolean(), nullable=True, server_default=sa.text('false')))

    op.execute("""
        UPDATE weekly_reports
        SET week_number = 0,
            letter_grade = 'NA',
            verdict = 'pending',
            is_current = false,
            completed_tasks = 0,
            total_tasks = 0,
            strengths = '[]'::jsonb,
            improvement_areas = '[]'::jsonb,
            recommendations = '[]'::jsonb,
            ai_generated = false
        WHERE week_number IS NULL
    """)

    op.alter_column('weekly_reports', 'week_number', nullable=False)
    op.alter_column('weekly_reports', 'letter_grade', nullable=False)
    op.alter_column('weekly_reports', 'verdict', nullable=False)
    op.alter_column('weekly_reports', 'is_current', nullable=False, server_default=None)
    op.alter_column('weekly_reports', 'completed_tasks', nullable=False, server_default=None)
    op.alter_column('weekly_reports', 'total_tasks', nullable=False, server_default=None)
    op.alter_column('weekly_reports', 'strengths', nullable=False, server_default=None)
    op.alter_column('weekly_reports', 'improvement_areas', nullable=False, server_default=None)
    op.alter_column('weekly_reports', 'recommendations', nullable=False, server_default=None)
    op.alter_column('weekly_reports', 'ai_generated', nullable=False, server_default=None)


def downgrade() -> None:
    op.drop_column('weekly_reports', 'ai_generated')
    op.drop_column('weekly_reports', 'recommendations')
    op.drop_column('weekly_reports', 'improvement_areas')
    op.drop_column('weekly_reports', 'strengths')
    op.drop_column('weekly_reports', 'total_tasks')
    op.drop_column('weekly_reports', 'completed_tasks')
    op.drop_column('weekly_reports', 'is_current')
    op.drop_column('weekly_reports', 'verdict')
    op.drop_column('weekly_reports', 'letter_grade')
    op.drop_column('weekly_reports', 'week_number')
    op.create_index(op.f('ix_roadmap_tasks_user_id'), 'roadmap_tasks', ['user_id'], unique=False)
    op.create_index(op.f('ix_roadmap_tasks_assigned_date'), 'roadmap_tasks', ['assigned_date'], unique=False)
