"""Conversation service for managing user dialogues."""

from typing import List, Optional
from uuid import UUID

from app.database.conversation_repository import ConversationRepository
from app.entities.conversation import Conversation, ConversationStatus
from app.utils.logger import get_logger

logger = get_logger(__name__)


class ConversationService:
    """
    Service for managing conversations.

    Provides high-level operations for conversations including:
    - Creating conversations
    - Managing messages
    - Handling session expiration
    - Conversation search and filtering
    """

    def __init__(self, conversation_repo: ConversationRepository):
        """
        Initialize conversation service.

        Args:
            conversation_repo: Conversation repository instance
        """
        self._repo = conversation_repo

    async def create_conversation(
        self,
        user_id: str,
        session_id: str,
        title: Optional[str] = None,
        task_id: Optional[str] = None,
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
        """
        conversation = await self._repo.create(
            user_id=user_id,
            session_id=session_id,
            title=title or "New Conversation",
            task_id=task_id,
            **kwargs
        )

        logger.info(f"Created conversation {conversation.id} for user {user_id}")
        return conversation

    async def get_conversation(
        self,
        conversation_id: UUID
    ) -> Optional[Conversation]:
        """
        Get conversation by ID.

        Args:
            conversation_id: Conversation ID

        Returns:
            Conversation entity or None
        """
        return await self._repo.get_by_id(conversation_id)

    async def get_or_create_session(
        self,
        user_id: str,
        session_id: str,
        title: Optional[str] = None,
        **kwargs
    ) -> Conversation:
        """
        Get existing session or create a new one.

        Args:
            user_id: User ID
            session_id: Session ID
            title: Optional conversation title
            **kwargs: Additional conversation fields

        Returns:
            Conversation entity
        """
        conversation = await self._repo.get_by_session_id(
            session_id=session_id,
            user_id=user_id
        )

        if not conversation:
            logger.info(f"Creating new conversation for session {session_id}")
            return await self.create_conversation(
                user_id=user_id,
                session_id=session_id,
                title=title,
                **kwargs
            )

        return conversation

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
            role: Message role (user/agent/system)
            content: Message content
            metadata: Optional message metadata

        Returns:
            True if successful, False otherwise

        Raises:
            Exception: If add message fails
        """
        return await self._repo.add_message(
            conversation_id=conversation_id,
            role=role,
            content=content,
            metadata=metadata
        )

    async def get_conversation_messages(
        self,
        conversation_id: UUID,
        limit: Optional[int] = None
    ) -> List[dict]:
        """
        Get messages from conversation.

        Args:
            conversation_id: Conversation ID
            limit: Maximum number of messages to return

        Returns:
            List of message dicts
        """
        conversation = await self._repo.get_by_id(conversation_id)

        if not conversation:
            logger.warning(f"Conversation {conversation_id} not found")
            return []

        return conversation.get_message_history(limit=limit)

    async def get_last_message(
        self,
        conversation_id: UUID
    ) -> Optional[dict]:
        """
        Get the last message from conversation.

        Args:
            conversation_id: Conversation ID

        Returns:
            Last message dict or None
        """
        conversation = await self._repo.get_by_id(conversation_id)

        if not conversation:
            return None

        return conversation.get_last_message()

    async def get_conversation_with_messages(
        self,
        conversation_id: UUID,
        message_limit: Optional[int] = 10
    ) -> Optional[dict]:
        """
        Get conversation with messages.

        Args:
            conversation_id: Conversation ID
            message_limit: Maximum number of messages to include

        Returns:
            Conversation dict with messages, or None
        """
        conversation = await self.get_conversation(conversation_id)

        if not conversation:
            return None

        messages = conversation.get_message_history(limit=message_limit)

        return {
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

    async def get_user_conversations(
        self,
        user_id: str,
        limit: int = 20,
        offset: int = 0,
        active_only: bool = True
    ) -> List[Conversation]:
        """
        Get conversations for a user.

        Args:
            user_id: User ID
            limit: Maximum number of conversations to return
            offset: Offset for pagination
            active_only: Only return active conversations

        Returns:
            List of Conversation entities
        """
        return await self._repo.list_by_user(
            user_id=user_id,
            limit=limit,
            offset=offset,
            active_only=active_only
        )

    async def expire_conversation(
        self,
        conversation_id: UUID
    ) -> bool:
        """
        Expire a conversation.

        Args:
            conversation_id: Conversation ID

        Returns:
            True if successful, False otherwise
        """
        result = await self._repo.update_status(
            conversation_id=conversation_id,
            status=ConversationStatus.EXPIRED
        )

        if result:
            logger.info(f"Conversation {conversation_id} expired")
        return True
        return False

    async def delete_conversation(
        self,
        conversation_id: UUID
    ) -> bool:
        """
        Delete a conversation.

        Args:
            conversation_id: Conversation ID

        Returns:
            True if successful, False otherwise
        """
        result = await self._repo.delete(conversation_id)

        if result:
            logger.info(f"Conversation {conversation_id} deleted")
        return True
        return False

    async def get_active_conversation_count(
        self,
        user_id: str,
        limit: int = 5
    ) -> int:
        """
        Get number of active conversations for a user (with limit).

        Args:
            user_id: User ID
            limit: Maximum count to return

        Returns:
            Number of active conversations
        """
        return await self._repo.get_user_active_count(
            user_id=user_id,
            limit=limit
        )

    async def expire_old_conversations(
        self,
        hours: int = 24
    ) -> int:
        """
        Expire old conversations.

        Args:
            hours: Number of hours before now

        Returns:
            Number of conversations expired
        """
        return await self._repo.expire_old_conversations(hours=hours)

    async def get_user_conversation_count(
        self,
        user_id: str,
        active_only: bool = True
    ) -> int:
        """
        Get total conversation count for a user.

        Args:
            user_id: User ID
            active_only: Only count active conversations

        Returns:
            Total number of conversations
        """
        return await self._repo.count_by_user(
            user_id=user_id,
            active_only=active_only
        )
