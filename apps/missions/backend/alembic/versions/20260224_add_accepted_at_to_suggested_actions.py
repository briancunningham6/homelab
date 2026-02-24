"""add accepted_at to suggested_actions

Revision ID: add_accepted_at
Revises: 
Create Date: 2024-02-24

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_accepted_at'
down_revision = '20260222_1500_003'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add accepted_at column
    op.add_column('suggested_actions', 
        sa.Column('accepted_at', sa.DateTime(timezone=True), nullable=True)
    )


def downgrade() -> None:
    # Remove accepted_at column
    op.drop_column('suggested_actions', 'accepted_at')
