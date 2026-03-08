"""add notes to missions

Revision ID: add_notes_to_missions
Revises: add_accepted_at
Create Date: 2026-03-06
"""
from alembic import op
import sqlalchemy as sa

revision = 'add_notes_to_missions'
down_revision = 'add_accepted_at'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('missions', sa.Column('notes', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('missions', 'notes')
