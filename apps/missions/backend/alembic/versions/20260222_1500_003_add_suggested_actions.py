"""add suggested actions table

Revision ID: 20260222_1500_003
Revises: 20260222_1400_002
Create Date: 2026-02-22 15:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '20260222_1500_003'
down_revision: Union[str, None] = '20260222_1400_002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create enum types
    op.execute("CREATE TYPE actiontype AS ENUM ('user_action', 'agent_action', 'info_request')")
    op.execute("CREATE TYPE actionpriority AS ENUM ('high', 'medium', 'low')")
    op.execute("CREATE TYPE actionstatus AS ENUM ('pending', 'accepted', 'deferred', 'dismissed', 'completed')")

    # Create suggested_actions table
    op.create_table(
        'suggested_actions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('mission_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('type', postgresql.ENUM('user_action', 'agent_action', 'info_request', name='actiontype'), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('reasoning', sa.Text(), nullable=True),
        sa.Column('priority', postgresql.ENUM('high', 'medium', 'low', name='actionpriority'), nullable=False),
        sa.Column('status', postgresql.ENUM('pending', 'accepted', 'deferred', 'dismissed', 'completed', name='actionstatus'), nullable=False),
        sa.Column('related_goal', sa.Text(), nullable=True),
        sa.Column('suggested_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['mission_id'], ['missions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_suggested_actions_mission_id'), 'suggested_actions', ['mission_id'], unique=False)
    op.create_index(op.f('ix_suggested_actions_status'), 'suggested_actions', ['status'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_suggested_actions_status'), table_name='suggested_actions')
    op.drop_index(op.f('ix_suggested_actions_mission_id'), table_name='suggested_actions')
    op.drop_table('suggested_actions')
    op.execute("DROP TYPE actionstatus")
    op.execute("DROP TYPE actionpriority")
    op.execute("DROP TYPE actiontype")
