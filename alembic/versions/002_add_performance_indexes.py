"""Add performance optimization indexes to database

Revision ID: 002_add_performance_indexes
Revises:
    001_add_conversations
Create Date: 2026-02-18 10:30:00

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

# revision identifiers, used by Alembic.
revision = '002_add_performance_indexes'
down_revision = '001_add_conversations'
branch_labels = None
depends_on = None


def upgrade():
    """Add performance optimization indexes to database tables.

    This migration adds composite indexes and performance-critical indexes
    to optimize query performance for the video generation system.
    """

    # ============================================================================
    # Tasks table indexes
    # ============================================================================

    # User task pagination index (user_id + created_at + status)
    # Optimizes: GET /tasks?user_id=xxx&status=xxx
    op.create_index(
        'idx_tasks_user_created_status',
        'tasks',
        ['user_id', sa.text('created_at DESC'), 'status'],
        unique=False
    )

    # Task priority index (user_id + priority + created_at)
    # Optimizes: GET /tasks?user_id=xxx&priority=xxx
    op.create_index(
        'idx_tasks_user_priority_created',
        'tasks',
        ['user_id', 'priority', sa.text('created_at DESC')],
        unique=False
    )

    # Task status filter index (status + created_at)
    # Optimizes: GET /tasks?status=xxx
    op.create_index(
        'idx_tasks_status_created',
        'tasks',
        ['status', sa.text('created_at DESC')],
        unique=False
    )

    # ============================================================================
    # Conversations table indexes
    # ============================================================================

    # User conversation pagination index (user_id + created_at + status)
    # Optimizes: GET /conversations?user_id=xxx&status=xxx
    op.create_index(
        'idx_conversations_user_created_status',
        'conversations',
        ['user_id', sa.text('created_at DESC'), 'status'],
        unique=False
    )

    # Conversation task association index (user_id + task_id)
    # Optimizes: GET /conversations?user_id=xxx&task_id=xxx
    op.create_index(
        'idx_conversations_user_task',
        'conversations',
        ['user_id', 'task_id'],
        unique=False
    )

    # Active conversation index (user_id + status + updated_at)
    # Optimizes: GET /conversations?user_id=xxx&status=active
    op.create_index(
        'idx_conversations_user_status_updated',
        'conversations',
        ['user_id', 'status', sa.text('updated_at DESC')],
        unique=False
    )

    # ============================================================================
    # Scripts table indexes
    # ============================================================================

    # Task script index (task_id + created_at)
    # Optimizes: GET /scripts?task_id=xxx
    op.create_index(
        'idx_scripts_task_created',
        'scripts',
        ['task_id', sa.text('created_at DESC')],
        unique=False
    )

    # Script status index (status + created_at)
    # Optimizes: GET /scripts?status=xxx
    op.create_index(
        'idx_scripts_status_created',
        'scripts',
        ['status', sa.text('created_at DESC')],
        unique=False
    )

    # ============================================================================
    # Storyboards table indexes
    # ============================================================================

    # Task shot index (task_id + sequence_number + created_at)
    # Optimizes: GET /storyboards?task_id=xxx
    op.create_index(
        'idx_storyboards_task_sequence_created',
        'storyboards',
        ['task_id', 'sequence_number', sa.text('created_at DESC')],
        unique=False
    )

    # Task shot status index (task_id + generation_status + created_at)
    # Optimizes: GET /storyboards?task_id=xxx&generation_status=xxx
    op.create_index(
        'idx_storyboards_task_status_created',
        'storyboards',
        ['task_id', 'generation_status', sa.text('created_at DESC')],
        unique=False
    )

    # Script shot association index (script_id + created_at)
    # Optimizes: GET /storyboards?script_id=xxx
    op.create_index(
        'idx_storyboards_script_created',
        'storyboards',
        ['script_id', sa.text('created_at DESC')],
        unique=False
    )

    # ============================================================================
    # Resources table indexes
    # ============================================================================

    # Task resource type index (task_id + resource_type + created_at)
    # Optimizes: GET /resources?task_id=xxx&resource_type=xxx
    op.create_index(
        'idx_resources_task_type_created',
        'resources',
        ['task_id', 'resource_type', sa.text('created_at DESC')],
        unique=False
    )

    # Task resource generation status index (task_id + generation_status + created_at)
    # Optimizes: GET /resources?task_id=xxx&generation_status=xxx
    op.create_index(
        'idx_resources_task_status_created',
        'resources',
        ['task_id', 'generation_status', sa.text('created_at DESC')],
        unique=False
    )

    # ============================================================================
    # Performance optimization indexes
    # ============================================================================

    # Created_at desc indexes for all tables (optimizes pagination)
    op.create_index(
        'idx_tasks_created_at',
        'tasks',
        [sa.text('created_at DESC')],
        unique=False
    )

    op.create_index(
        'idx_conversations_created_at',
        'conversations',
        [sa.text('created_at DESC')],
        unique=False
    )

    op.create_index(
        'idx_scripts_created_at',
        'scripts',
        [sa.text('created_at DESC')],
        unique=False
    )

    op.create_index(
        'idx_storyboards_created_at',
        'storyboards',
        [sa.text('created_at DESC')],
        unique=False
    )

    op.create_index(
        'idx_resources_created_at',
        'resources',
        [sa.text('created_at DESC')],
        unique=False
    )

    # Updated_at desc indexes for active data filtering
    op.create_index(
        'idx_tasks_updated_at',
        'tasks',
        [sa.text('updated_at DESC')],
        unique=False
    )

    op.create_index(
        'idx_conversations_updated_at',
        'conversations',
        [sa.text('updated_at DESC')],
        unique=False
    )


def downgrade():
    """Remove performance optimization indexes from database tables.

    This migration removes all the composite indexes and performance indexes
    added in the upgrade step.
    """

    # ============================================================================
    # Remove Tasks table indexes
    # ============================================================================

    op.drop_index('idx_tasks_user_created_status', 'tasks')
    op.drop_index('idx_tasks_user_priority_created', 'tasks')
    op.drop_index('idx_tasks_status_created', 'tasks')
    op.drop_index('idx_tasks_created_at', 'tasks')
    op.drop_index('idx_tasks_updated_at', 'tasks')

    # ============================================================================
    # Remove Conversations table indexes
    # ============================================================================

    op.drop_index('idx_conversations_user_created_status', 'conversations')
    op.drop_index('idx_conversations_user_task', 'conversations')
    op.drop_index('idx_conversations_user_status_updated', 'conversations')
    op.drop_index('idx_conversations_created_at', 'conversations')
    op.drop_index('idx_conversations_updated_at', 'conversations')

    # ============================================================================
    # Remove Scripts table indexes
    # ============================================================================

    op.drop_index('idx_scripts_task_created', 'scripts')
    op.drop_index('idx_scripts_status_created', 'scripts')
    op.drop_index('idx_scripts_created_at', 'scripts')

    # ============================================================================
    # Remove Storyboards table indexes
    # ============================================================================

    op.drop_index('idx_storyboards_task_sequence_created', 'storyboards')
    op.drop_index('idx_storyboards_task_status_created', 'storyboards')
    op.drop_index('idx_storyboards_script_created', 'storyboards')
    op.drop_index('idx_storyboards_created_at', 'storyboards')

    # ============================================================================
    # Remove Resources table indexes
    # ============================================================================

    op.drop_index('idx_resources_task_type_created', 'resources')
    op.drop_index('idx_resources_task_status_created', 'resources')
    op.drop_index('idx_resources_created_at', 'resources')
