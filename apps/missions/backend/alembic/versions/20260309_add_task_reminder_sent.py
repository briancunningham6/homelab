"""add reminder_sent to mission_tasks

Revision ID: add_task_reminder_sent
Revises: add_mission_tasks
Create Date: 2026-03-09
"""
from alembic import op
import sqlalchemy as sa

revision = 'add_task_reminder_sent'
down_revision = 'add_mission_tasks'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'mission_tasks',
        sa.Column('reminder_sent', sa.Boolean(), nullable=False, server_default='false'),
    )


def downgrade() -> None:
    op.drop_column('mission_tasks', 'reminder_sent')
