"""Initial schema

Revision ID: 001
Revises:
Create Date: 2026-02-21 19:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create categories table
    op.create_table(
        'categories',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=50), nullable=False),
        sa.Column('display_name', sa.String(length=100), nullable=False),
        sa.Column('color', sa.String(length=7), nullable=True),
        sa.Column('icon', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )

    # Create llm_providers table
    op.create_table(
        'llm_providers',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=50), nullable=False),
        sa.Column('display_name', sa.String(length=100), nullable=False),
        sa.Column('api_key_encrypted', sa.Text(), nullable=True),
        sa.Column('default_model', sa.String(length=100), nullable=True),
        sa.Column('is_enabled', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )

    # Create missions table
    op.create_table(
        'missions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('goals', sa.Text(), nullable=False),
        sa.Column('category_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('llm_provider_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('model_override', sa.String(length=100), nullable=True),
        sa.Column('autonomy_level', sa.String(length=20), nullable=True),
        sa.Column('check_interval', sa.String(length=20), nullable=True),
        sa.Column('last_checked_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('next_check_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['category_id'], ['categories.id'], ),
        sa.ForeignKeyConstraint(['llm_provider_id'], ['llm_providers.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_missions_status', 'missions', ['status'], unique=False)
    op.create_index('idx_missions_next_check', 'missions', ['next_check_at'], unique=False,
                    postgresql_where=sa.text("status = 'active'"))

    # Create mission_files table
    op.create_table(
        'mission_files',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('mission_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('filename', sa.String(length=255), nullable=False),
        sa.Column('original_name', sa.String(length=255), nullable=False),
        sa.Column('mime_type', sa.String(length=100), nullable=True),
        sa.Column('size_bytes', sa.BigInteger(), nullable=True),
        sa.Column('storage_path', sa.Text(), nullable=False),
        sa.Column('extracted_text', sa.Text(), nullable=True),
        sa.Column('parsed_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('uploaded_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['mission_id'], ['missions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_files_mission', 'mission_files', ['mission_id'], unique=False)

    # Create messages table
    op.create_table(
        'messages',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('mission_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('role', sa.String(length=20), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('tool_name', sa.String(length=100), nullable=True),
        sa.Column('tool_input', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('tool_output', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('input_tokens', sa.Integer(), nullable=True),
        sa.Column('output_tokens', sa.Integer(), nullable=True),
        sa.Column('model_used', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['mission_id'], ['missions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_messages_mission', 'messages', ['mission_id', 'created_at'], unique=False)

    # Insert default categories
    op.execute("""
        INSERT INTO categories (id, name, display_name, color, icon) VALUES
        (gen_random_uuid(), 'home', 'Home & Family', '#4A90D9', 'mdi-home'),
        (gen_random_uuid(), 'work', 'Work & Career', '#27AE60', 'mdi-briefcase'),
        (gen_random_uuid(), 'financial', 'Financial', '#F39C12', 'mdi-currency-usd'),
        (gen_random_uuid(), 'health', 'Health & Fitness', '#E74C3C', 'mdi-heart-pulse'),
        (gen_random_uuid(), 'learning', 'Learning & Development', '#9B59B6', 'mdi-school'),
        (gen_random_uuid(), 'other', 'Other', '#95A5A6', 'mdi-dots-horizontal')
    """)

    # Insert default LLM providers (without API keys initially)
    op.execute("""
        INSERT INTO llm_providers (id, name, display_name, default_model, is_enabled) VALUES
        (gen_random_uuid(), 'claude', 'Anthropic Claude', 'claude-sonnet-4-20250514', true),
        (gen_random_uuid(), 'openai', 'OpenAI', 'gpt-4o', true)
    """)


def downgrade() -> None:
    op.drop_index('idx_messages_mission', table_name='messages')
    op.drop_table('messages')
    op.drop_index('idx_files_mission', table_name='mission_files')
    op.drop_table('mission_files')
    op.drop_index('idx_missions_next_check', table_name='missions', postgresql_where=sa.text("status = 'active'"))
    op.drop_index('idx_missions_status', table_name='missions')
    op.drop_table('missions')
    op.drop_table('llm_providers')
    op.drop_table('categories')
