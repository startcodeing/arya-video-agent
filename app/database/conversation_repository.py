"""Conversation repository for database operations."""

from typing import List, Optional
from uuid import UUID

from sqlalchemy import select, update, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.expression import func

from app.database.base import Base
from app.entities.conversation import Conversation, ConversationStatus
from app.utils.logger import get_logger

logger = get_logger(__name__)


class ConversationRepository:
    """
    Repository for managing Conversation entities.

    Handles database operations for conversations including:
    - CRUD operations
    - Query methods
    - Expiration management
    """

    def __init__(self, db: AsyncSession):
        """
        Initialize conversation repository.

        Args:
            db: Database session
        """
        self.db = db

    async def create(
        self,
        user_id: str,
        session_id: str,
        title: Optional[str] = None,
        task_id: Optional[str] = None
        **kwargs
    ) -> Conversation:
        """
        Create a new conversation.

        Args:
            user_id: User ID
            session_id: Session ID
            title: Optional conversation title
            task_id: Optional associated task ID
            **kwargs: Additional conversation fields

        Returns:
            Created Conversation entity

        Raises:
            Exception: If creation fails
        """
        try:
            conversation = Conversation(
                user_id=user_id,
                session_id=session_id,
                title=title,
                task_id=task_id,
                status=ConversationStatus.ACTIVE,
                agent_name=kwargs.get('agent_name'),
                context_window=kwargs.get('context_window', 10),
                message_count=0,
                **kwargs
            )

            self.db.add(conversation)
            await self.db.commit()
            await self.db.refresh(conversation)

            logger.info(f"Created conversation {conversation.id} for user {user_id}")
            return conversation

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to create conversation: {str(e)}")
            raise

    async def get_by_id(self, conversation_id: UUID) -> Optional[Conversation]:
        """
        Get conversation by ID.

        Args:
            conversation_id: Conversation ID

        Returns:
            Conversation entity or None
        """
        try:
            result = await self.db.execute(
                select(Conversation).where(Conversation.id == conversation_id)
            )
            return result.scalar_one_or_none()

        except Exception as e:
            logger.error(f"Failed to get conversation {conversation_id}: {str(e)}")
            return None

    async def get_by_session_id(
        self,
        session_id: str,
        user_id: str,
        active_only: bool = True
    ) -> Optional[Conversation]:
        """
        Get conversation by session ID.

        Args:
            session_id: Session ID
            user_id: User ID
            active_only: Only return active conversations

        Returns:
            Conversation entity or None
        """
        try:
            query = select(Conversation).where(
                and_(
                    Conversation.session_id == session_id,
                    Conversation.user_id == user_id
                )
            )

            if active_only:
                query = query.where(Conversation.status == ConversationStatus.ACTIVE)

            result = await self.db.execute(query)
            return result.scalar_one_or_none()

        except Exception as e:
            logger.error(f"Failed to get conversation {session_id}: {str(e)}")
            return None

    async def list_by_user(
        self,
        user_id: str,
        limit: int = 50,
        offset: int = 0,
        active_only: bool = True
    ) -> List[Conversation]:
        """
        List conversations for a user.

        Args:
            user_id: User ID
            limit: Maximum number of conversations to return
            offset: Offset for pagination
            active_only: Only return active conversations

        Returns:
            List of Conversation entities
        """
        try:
            query = select(Conversation).where(Conversation.user_id == user_id)

            if active_only:
                query = query.where(Conversation.status == ConversationStatus.ACTIVE)

            query = query.order_by(Conversation.created_at.desc())
            query = query.offset(offset).limit(limit)

            result = await self.db.execute(query)
            return list(result.scalars().all())

        except Exception as e:
            logger.error(f"Failed to list conversations for user {user_id}: {str(e)}")
            return []

    async def get_or_create_by_session(
        self,
        user_id: str,
        session_id: str,
        **kwargs
    ) -> Conversation:
        """
        Get or create conversation by session ID.

        Args:
            user_id: User ID
            session_id: Session ID
            **kwargs: Additional conversation fields

        Returns:
            Conversation entity
        """
        conversation = await self.get_by_session_id(session_id, user_id)

        if not conversation:
            logger.info(f"Creating new conversation for session {session_id}")
            return await self.create(user_id=user_id, session_id=session_id, **kwargs)

        return conversation

    async def update_status(
        self,
        conversation_id: UUID,
        status: ConversationStatus
    ) -> bool:
        """
        Update conversation status.

        Args:
            conversation_id: Conversation ID
            status: New status

        Returns:
            True if successful, False otherwise

        Raises:
            Exception: If update fails
        """
        try:
            result = await self.db.execute(
                update(Conversation)
                .where(Conversation.id == conversation_id)
                .values(status=status, updated_at=func.now())
                .execution_options(synchronize_session=False)
            )

            if result.rowcount > 0:
                await self.db.commit()
                logger.info(f"Updated conversation {conversation_id} status to {status}")
                return True
            return False

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
        Add a message to conversation.

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
            conversation = await self.get_by_id(conversation_id)
            if not conversation:
                logger.error(f"Conversation {conversation_id} not found")
                return False

            # Add message to conversation
            conversation.add_message(role, content, metadata)

            # Update conversation
            await self.db.execute(
                update(Conversation)
                .where(Conversation.id == conversation_id)
                .values(
                    message_count=conversation.message_count + 1,
                    updated_at=func.now()
                )
                .execution_options(synchronize_session=False)
            )

            await self.db.commit()
            logger.info(f"Added message to conversation {conversation_id}")
            return True

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to add message to conversation {conversation_id}: {str(e)}")
            raise

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
            result = await self.db.execute(
                update(Conversation)
                .where(
                    and_(
                        Conversation.status == ConversationStatus.ACTIVE,
                        Conversation.created_at < expiration_time
                    )
                )
                .values(
                    status=ConversationStatus.EXPIRED,
                    updated_at=func.now()
                )
            )

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
        Delete a conversation.

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

            logger.info(f"Deleted conversation {conversation_id}")
            return True

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to delete conversation {conversation_id}: {str(e)}")
            raise

    async def count_by_user(self, user_id: str, active_only: bool = True) -> int:
        """
        Count conversations for a user.

        Args:
            user_id: User ID
            active_only: Only count active conversations

        Returns:
            Number of conversations
        """
        try:
            query = select(func.count(Conversation.id)).where(Conversation.user_id == user_id)

            if active_only:
                query = query.where(Conversation.status == ConversationStatus.ACTIVE)

            result = await self.db.execute(query)
            return result.scalar() or 0

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
            query = select(func.count(Conversation.id)).where(
                and_(
                    Conversation.user_id == user_id,
                    Conversation.status == ConversationStatus.ACTIVE
                )
            )

            result = await self.db.execute(query)
            return min(result.scalar() or 0, limit)

        except Exception as e:
            logger.error(f"Failed to get active conversation count for user {user_id}: {str(e)}")
            return 0
