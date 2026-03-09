"""add mission tasks table

Revision ID: add_mission_tasks
Revises: add_notes_to_missions
Create Date: 2026-03-09
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = 'add_mission_tasks'
down_revision = 'add_notes_to_missions'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'mission_tasks',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('mission_id', UUID(as_uuid=True), sa.ForeignKey('missions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('title', sa.Text(), nullable=False),
        sa.Column('due_date', sa.Date(), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='open'),
        sa.Column('sort_order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_mission_tasks_mission_id', 'mission_tasks', ['mission_id'])


def downgrade() -> None:
    op.drop_index('ix_mission_tasks_mission_id', 'mission_tasks')
    op.drop_table('mission_tasks')
