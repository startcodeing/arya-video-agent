"""Database layer for repository pattern."""

from app.database.base import Base
from app.database.session import get_db
from app.database.task_repository import TaskRepository
from app.database.script_repository import ScriptRepository
from app.database.storyboard_repository import StoryboardRepository
from app.database.resource_repository import ResourceRepository
from app.database.conversation_repository import ConversationRepository

# Optimized repositories
from app.database.task_repository_optimized import TaskRepositoryOptimized
from app.database.conversation_repository_optimized import ConversationRepositoryOptimized
from app.database.script_repository_optimized import ScriptRepositoryOptimized
from app.database.storyboard_repository_optimized import StoryboardRepositoryOptimized
from app.database.resource_repository_optimized import ResourceRepositoryOptimized

__all__ = [
    "Base",
    "get_db",
    # Original repositories
    "TaskRepository",
    "ScriptRepository",
    "StoryboardRepository",
    "ResourceRepository",
    "ConversationRepository",
    # Optimized repositories
    "TaskRepositoryOptimized",
    "ConversationRepositoryOptimized",
    "ScriptRepositoryOptimized",
    "StoryboardRepositoryOptimized",
    "ResourceRepositoryOptimized",
]
