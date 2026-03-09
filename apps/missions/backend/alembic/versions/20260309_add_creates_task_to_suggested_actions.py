"""add creates_task fields to suggested_actions

Revision ID: add_creates_task_to_suggested_actions
Revises: add_task_reminder_sent
Create Date: 2026-03-09
"""
from alembic import op
import sqlalchemy as sa

revision = 'add_creates_task_to_suggested_actions'
down_revision = 'add_task_reminder_sent'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'suggested_actions',
        sa.Column('creates_task', sa.Boolean(), nullable=False, server_default='false'),
    )
    op.add_column(
        'suggested_actions',
        sa.Column('task_due_date', sa.Date(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column('suggested_actions', 'task_due_date')
    op.drop_column('suggested_actions', 'creates_task')
