"""Add conversations table

Revision ID: 001_add_conversations
Revises:
    001_add_conversations
Create Date: 2026-02-16 14:55:00

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001_add_conversations'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    """Upgrade schema to add conversations table."""
    op.create_table(
        'conversations',
        sa.Column('id', sa.String(36), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('user_id', sa.String(100), nullable=False, index=True),
        sa.Column('session_id', sa.String(100), nullable=False, unique=True, index=True),
        sa.Column('task_id', sa.String(36), sa.ForeignKey('tasks.id'), nullable=True, index=True),
        sa.Column('title', sa.String(200), nullable=True),
        sa.Column('status', sa.String(50), nullable=False, server_default=sa.text('active')),
        sa.Column('messages', sa.JSON(), nullable=False, server_default='{}'),
        sa.Column('metadata', sa.JSON(), nullable=False, server_default='{}'),
        sa.Column('agent_name', sa.String(100), nullable=True),
        sa.Column('context_window', sa.Integer(), nullable=False, server_default=10),
        sa.Column('message_count', sa.Integer(), nullable=False, server_default=0),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('expires_at', sa.TIMESTAMP(timezone=True), nullable=True),
    )

    # Add indexes
    op.create_index('idx_conversations_user_id', 'conversations', ['user_id'])
    op.create_index('idx_conversations_session_id', 'conversations', ['session_id'])
    op.create_index('idx_conversations_task_id', 'conversations', ['task_id'])
    op.create_index('idx_conversations_status', 'conversations', ['status'])

    # Add foreign key constraint
    op.create_foreign_key('fk_conversations_task_id', 'conversations', 'task_id', 'tasks', 'id')


def downgrade():
    """Downgrade schema to remove conversations table."""
    op.drop_index('idx_conversations_status', 'conversations')
    op.drop_index('idx_conversations_task_id', 'conversations')
    op.drop_index('idx_conversations_session_id', 'conversations')
    op.drop_index('idx_conversations_user_id', 'conversations')

    op.drop_constraint('fk_conversations_task_id', 'conversations', 'task_id')
    op.drop_table('conversations')

    # Drop sequence if exists
    op.execute(sa.text('DROP SEQUENCE IF EXISTS conversations_id_seq'))
