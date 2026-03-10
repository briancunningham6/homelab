"""add app_settings table

Revision ID: add_app_settings
Revises: add_creates_task
Create Date: 2026-03-10
"""
from alembic import op
import sqlalchemy as sa

revision = 'add_app_settings'
down_revision = 'add_creates_task'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'app_settings',
        sa.Column('key', sa.String(100), primary_key=True),
        sa.Column('value_encrypted', sa.Text(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    )

    # Seed the known integration keys with null values
    op.execute("INSERT INTO app_settings (key) VALUES ('tavily_api_key')")


def downgrade() -> None:
    op.drop_table('app_settings')
