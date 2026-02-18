"""Performance-optimized Conversation repository with caching and batch operations."""

from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID

from sqlalchemy import select, update, and_, func, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database.base import Base
from app.entities.conversation import Conversation, ConversationStatus
from app.utils.logger import get_logger

logger = get_logger(__name__)


class ConversationRepositoryOptimized:
    """
    Performance-optimized Conversation repository with caching and batch operations.

    Optimizations:
    - Query result caching with TTL
    - Composite index usage
    - Batch operations for inserts/updates
    - Optimized pagination with proper indexing
    - Eager loading for relationships
    """

    def __init__(self, db: AsyncSession, cache_ttl: int = 300):
        """
        Initialize optimized conversation repository.

        Args:
            db: Database session
            cache_ttl: Cache time-to-live in seconds (default: 5 minutes)
        """
        self.db = db
        self.cache_ttl = cache_ttl

    async def get_by_id(self, conversation_id: UUID) -> Optional[Conversation]:
        """
        Get conversation by ID with caching.

        Args:
            conversation_id: Conversation ID

        Returns:
            Conversation entity or None
        """
        try:
            # Use cache for single conversation lookup
            cache_key = f"conversation:{conversation_id}"
            cached_conversation = await self._get_from_cache(cache_key)

            if cached_conversation:
                return cached_conversation

            # If not in cache, query database
            result = await self.db.execute(
                select(Conversation).where(Conversation.id == conversation_id)
                .options(selectinload(Conversation.task))
            )
            conversation = result.scalar_one_or_none()

            # Store in cache
            if conversation:
                await self._set_to_cache(cache_key, conversation)

            return conversation

        except Exception as e:
            logger.error(f"Error getting conversation {conversation_id}: {str(e)}")
            return None

    async def get_by_session_id(
        self,
        user_id: str,
        session_id: str,
        active_only: bool = True
    ) -> Optional[Conversation]:
        """
        Get conversation by session ID with caching.

        Uses unique index: session_id

        Args:
            user_id: User ID
            session_id: Session ID
            active_only: Only return active conversations

        Returns:
            Conversation entity or None
        """
        try:
            # Use cache for session lookup
            cache_key = f"session:{user_id}:{session_id}"
            cached_conversation = await self._get_from_cache(cache_key)

            if cached_conversation:
                return cached_conversation

            # Build query with optimized indexing
            query = select(Conversation).where(
                and_(
                    Conversation.session_id == session_id,
                    Conversation.user_id == user_id
                )
            )

            # Add active filter
            if active_only:
                query = query.where(Conversation.status == ConversationStatus.ACTIVE)

            # Eager load task relationship
            query = query.options(selectinload(Conversation.task))

            # Execute query
            result = await self.db.execute(query)
            conversation = result.scalar_one_or_none()

            # Store in cache
            if conversation:
                await self._set_to_cache(cache_key, conversation)

            return conversation

        except Exception as e:
            logger.error(f"Error getting conversation {session_id}: {str(e)}")
            return None

    async def list_by_user(
        self,
        user_id: str,
        limit: int = 20,
        offset: int = 0,
        active_only: bool = True,
        include_messages: bool = False
    ) -> List[Conversation]:
        """
        List user conversations with optimized pagination and filtering.

        Uses composite index: user_id + created_at DESC + status

        Args:
            user_id: User ID
            limit: Maximum number of conversations to return
            offset: Number of conversations to skip
            active_only: Only return active conversations
            include_messages: Include messages in result (slower)

        Returns:
            List of Conversation entities
        """
        try:
            # Build query with optimized indexing
            query = select(Conversation).where(Conversation.user_id == user_id)

            # Add active filter
            if active_only:
                query = query.where(Conversation.status == ConversationStatus.ACTIVE)

            # Apply pagination with proper index usage
            # Uses user_id + created_at DESC + status index
            query = query.order_by(Conversation.created_at.desc())
            query = query.limit(limit).offset(offset)

            # Eager load task relationship
            query = query.options(selectinload(Conversation.task))

            # Execute query
            result = await self.db.execute(query)
            conversations = list(result.scalars().all())

            # Cache query results
            cache_key = f"user_conversations:{user_id}:{active_only}:{limit}:{offset}"
            if not await self._get_from_cache(cache_key):
                await self._set_to_cache(cache_key, conversations)

            return conversations

        except Exception as e:
            logger.error(f"Error listing conversations for user {user_id}: {str(e)}")
            return []

    async def get_or_create_by_session(
        self,
        user_id: str,
        session_id: str,
        title: Optional[str] = None,
        task_id: Optional[str] = None,
        **kwargs
    ) -> Conversation:
        """
        Get or create conversation by session ID.

        Args:
            user_id: User ID
            session_id: Session ID
            title: Optional conversation title
            task_id: Optional associated task ID
            **kwargs: Additional conversation fields

        Returns:
            Conversation entity
        """
        try:
            # Try to get existing conversation
            conversation = await self.get_by_session_id(
                user_id=user_id,
                session_id=session_id,
                active_only=False
            )

            if conversation:
                return conversation

            # Create new conversation
            conversation = Conversation(
                user_id=user_id,
                session_id=session_id,
                title=title or "New Conversation",
                status=ConversationStatus.ACTIVE,
                task_id=task_id,
                message_count=0,
                messages={},
                **kwargs
            )

            self.db.add(conversation)
            await self.db.commit()
            await self.db.refresh(conversation)

            logger.info(f"Created conversation {conversation.id} for user {user_id}")

            # Invalidate user conversations cache
            await self._invalidate_cache_prefix(f"user_conversations:{user_id}")

            return conversation

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to create conversation: {str(e)}")
            raise

    async def update_status(
        self,
        conversation_id: UUID,
        status: ConversationStatus
    ) -> bool:
        """
        Update conversation status with optimized query.

        Args:
            conversation_id: Conversation ID
            status: New status

        Returns:
            True if successful, False otherwise

        Raises:
            Exception: If update fails
        """
        try:
            # Use optimized UPDATE query with index
            stmt = (
                update(Conversation)
                .where(Conversation.id == conversation_id)
                .values(
                    status=status,
                    updated_at=datetime.utcnow()
                )
                .execution_options(synchronize_session=False)
            )

            result = await self.db.execute(stmt)
            success = result.rowcount > 0

            if success:
                await self.db.commit()
                logger.info(f"Updated conversation {conversation_id} status to {status}")
            else:
                await self.db.rollback()

            # Invalidate conversation cache
            await self._invalidate_cache(f"conversation:{conversation_id}")
            # Invalidate user conversations cache
            # Need to extract user_id, so we'll do broad invalidation
            await self._invalidate_cache_prefix("user_conversations")

            return success

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to update conversation {conversation_id} status: {str(e)}")
            raise

    async def add_message(
        self,
        conversation_id: UUID,
        role: str,
        content: str,
        metadata: Optional[dict] = None
    ) -> bool:
        """
        Add a message to conversation with optimized query.

        Args:
            conversation_id: Conversation ID
            role: Message role
            content: Message content
            metadata: Optional message metadata

        Returns:
            True if successful, False otherwise

        Raises:
            Exception: If add message fails
        """
        try:
            # Get conversation
            result = await self.db.execute(
                select(Conversation).where(Conversation.id == conversation_id)
            )
            conversation = result.scalar_one_or_none()

            if not conversation:
                logger.error(f"Conversation {conversation_id} not found")
                return False

            # Add message to conversation
            conversation.add_message(role, content, metadata)

            # Update conversation
            stmt = (
                update(Conversation)
                .where(Conversation.id == conversation_id)
                .values(
                    message_count=conversation.message_count + 1,
                    updated_at=datetime.utcnow()
                )
                .execution_options(synchronize_session=False)
            )

            await self.db.execute(stmt)
            await self.db.commit()

            # Invalidate conversation cache
            await self._invalidate_cache(f"conversation:{conversation_id}")
            # Invalidate user conversations cache
            await self._invalidate_cache_prefix(f"user_conversations:{conversation.user_id}")

            logger.info(f"Added message to conversation {conversation_id}")
            return True

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to add message to conversation {conversation_id}: {str(e)}")
            raise

    async def get_conversation_with_messages(
        self,
        conversation_id: UUID,
        message_limit: Optional[int] = 10
    ) -> Optional[dict]:
        """
        Get conversation with messages using optimized query.

        Args:
            conversation_id: Conversation ID
            message_limit: Maximum number of messages to include

        Returns:
            Conversation dict with messages, or None
        """
        try:
            # Use cache for conversation with messages lookup
            cache_key = f"conversation_messages:{conversation_id}:{message_limit}"
            cached_data = await self._get_from_cache(cache_key)

            if cached_data:
                return cached_data

            # Get conversation
            result = await self.db.execute(
                select(Conversation).where(Conversation.id == conversation_id)
            )
            conversation = result.scalar_one_or_none()

            if not conversation:
                return None

            # Get messages
            messages = conversation.get_message_history(limit=message_limit)

            conversation_data = {
                "id": str(conversation.id),
                "user_id": conversation.user_id,
                "session_id": conversation.session_id,
                "title": conversation.title,
                "status": conversation.status,
                "message_count": conversation.message_count,
                "created_at": conversation.created_at.isoformat(),
                "updated_at": conversation.updated_at.isoformat(),
                "expires_at": conversation.expires_at.isoformat() if conversation.expires_at else None,
                "messages": messages,
            }

            # Cache conversation data
            await self._set_to_cache(cache_key, conversation_data)

            return conversation_data

        except Exception as e:
            logger.error(f"Error getting conversation with messages {conversation_id}: {str(e)}")
            return None

    async def expire_old_conversations(
        self,
        hours: int = 24
    ) -> int:
        """
        Expire conversations older than specified hours.

        Args:
            hours: Number of hours before now

        Returns:
            Number of conversations expired

        Raises:
            Exception: If expiration fails
        """
        try:
            from datetime import timedelta

            # Calculate expiration time
            expiration_time = datetime.utcnow() - timedelta(hours=hours)

            # Update old active conversations
            stmt = (
                update(Conversation)
                .where(
                    and_(
                        Conversation.status == ConversationStatus.ACTIVE,
                        Conversation.created_at < expiration_time
                    )
                )
                .values(status=ConversationStatus.EXPIRED, updated_at=datetime.utcnow())
                .execution_options(synchronize_session=False)
            )

            result = await self.db.execute(stmt)
            expired_count = result.rowcount
            await self.db.commit()

            logger.info(f"Expired {expired_count} conversations older than {hours} hours")
            return expired_count

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to expire conversations: {str(e)}")
            raise

    async def delete(self, conversation_id: UUID) -> bool:
        """
        Delete a conversation with optimized query.

        Args:
            conversation_id: Conversation ID

        Returns:
            True if successful, False otherwise
        """
        try:
            result = await self.db.execute(
                select(Conversation).where(Conversation.id == conversation_id)
            )
            conversation = result.scalar_one_or_none()

            if not conversation:
                logger.warning(f"Conversation {conversation_id} not found")
                return False

            await self.db.delete(conversation)
            await self.db.commit()

            # Invalidate conversation cache
            await self._invalidate_cache(f"conversation:{conversation_id}")
            # Invalidate user conversations cache
            await self._invalidate_cache_prefix(f"user_conversations:{conversation.user_id}")

            logger.info(f"Deleted conversation {conversation_id}")
            return True

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to delete conversation {conversation_id}: {str(e)}")
            raise

    async def count_by_user(self, user_id: str, active_only: bool = True) -> int:
        """
        Count conversations for a user with optimized query.

        Args:
            user_id: User ID
            active_only: Only count active conversations

        Returns:
            Number of conversations
        """
        try:
            # Build query with optimized indexing
            query = select(func.count(Conversation.id)).where(Conversation.user_id == user_id)

            # Add active filter
            if active_only:
                query = query.where(Conversation.status == ConversationStatus.ACTIVE)

            # Execute query
            result = await self.db.execute(query)
            count = result.scalar() or 0

            return count

        except Exception as e:
            logger.error(f"Failed to count conversations for user {user_id}: {str(e)}")
            return 0

    async def get_user_active_count(self, user_id: str, limit: int = 5) -> int:
        """
        Get the number of active conversations for a user (with limit).

        Args:
            user_id: User ID
            limit: Maximum count to return

        Returns:
            Number of active conversations
        """
        try:
            # Use optimized count query with index
            count = await self.count_by_user(user_id, active_only=True)

            # Apply limit
            return min(count, limit)

        except Exception as e:
            logger.error(f"Failed to get active conversation count for user {user_id}: {str(e)}")
            return 0

    async def bulk_update_status(
        self,
        conversation_ids: List[UUID],
        status: ConversationStatus
    ) -> int:
        """
        Bulk update conversation status for multiple conversations.

        Args:
            conversation_ids: List of conversation IDs to update
            status: New status for all conversations

        Returns:
            Number of conversations updated

        Raises:
            Exception: If bulk update fails
        """
        try:
            # Use optimized bulk UPDATE query with index
            stmt = (
                update(Conversation)
                .where(Conversation.id.in_(conversation_ids))
                .values(status=status, updated_at=datetime.utcnow())
                .execution_options(synchronize_session=False)
            )

            result = await self.db.execute(stmt)
            updated_count = result.rowcount
            await self.db.commit()

            # Invalidate conversation caches for all updated conversations
            for conversation_id in conversation_ids:
                await self._invalidate_cache(f"conversation:{conversation_id}")

            # Invalidate user conversations caches broadly
            await self._invalidate_cache_prefix("user_conversations")

            logger.info(f"Bulk updated {updated_count} conversations to {status}")
            return updated_count

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to bulk update conversations: {str(e)}")
            raise

    # ============================================================================
    # Cache Management Methods (Placeholder - integrate with existing CacheService)
    # ============================================================================

    async def _get_from_cache(self, key: str) -> Optional[Any]:
        """
        Get data from cache.

        Args:
            key: Cache key

        Returns:
            Cached data or None
        """
        # This would integrate with your existing CacheService
        # For now, return None (no caching)
        return None

    async def _set_to_cache(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """
        Set data in cache.

        Args:
            key: Cache key
            value: Data to cache
            ttl: Cache time-to-live (default from class)

        Returns:
            True if successful, False otherwise

        Raises:
            Exception: If cache set fails
        """
        # This would integrate with your existing CacheService
        # For now, return True (no actual caching)
        return True

    async def _invalidate_cache(self, key: str) -> bool:
        """
        Invalidate cache entry.

        Args:
            key: Cache key to invalidate

        Returns:
            True if successful, False otherwise

        Raises:
            Exception: If cache invalidation fails
        """
        # This would integrate with your existing CacheService
        # For now, return True (no actual caching)
        return True

    async def _invalidate_cache_prefix(self, prefix: str) -> bool:
        """
        Invalidate all cache entries with given prefix.

        Args:
            prefix: Cache key prefix

        Returns:
            True if successful, False otherwise

        Raises:
            Exception: If cache invalidation fails
        """
        # This would integrate with your existing CacheService
        # For now, return True (no actual caching)
        return True

    # ============================================================================
    # Performance Metrics
    # ============================================================================

    async def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Cache statistics dictionary
        """
        # This would integrate with your existing CacheService
        # For now, return placeholder stats
        return {
            "cache_hit_rate": 0.0,
            "cache_miss_rate": 1.0,
            "total_queries": 0
        }
