"""Unit tests for ConversationService."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from app.services.conversation_service import ConversationService
from app.database.conversation_repository import ConversationRepository
from app.entities.conversation import Conversation, ConversationStatus
from app.utils.logger import get_logger

logger = get_logger(__name__)


@pytest.fixture
def mock_conversation_repo():
    """Create a mock conversation repository."""
    repo = AsyncMock()

    # Mock create method
    async def create_conversation(user_id, session_id, **kwargs):
        conversation = Conversation(
            id=uuid4(),
            user_id=user_id,
            session_id=session_id,
            status=ConversationStatus.ACTIVE,
            message_count=0,
            **kwargs
        )
        return conversation

    repo.create = create_conversation

    # Mock get_by_id method
    async def get_conversation(conversation_id):
        return Conversation(
            id=conversation_id,
            user_id="test_user",
            session_id="test_session",
            status=ConversationStatus.ACTIVE,
            message_count=2,
            messages={
                "0": {
                    "role": "user",
                    "content": "Hello",
                    "timestamp": "2026-02-16T10:00:00Z",
                },
                "1": {
                    "role": "agent",
                    "content": "Hi! How can I help you?",
                    "timestamp": "2026-02-16T10:00:10Z",
                }
            }
        )

    repo.get_by_id = get_conversation

    return repo


@pytest.fixture
def conversation_service(mock_conversation_repo):
    """Create a conversation service instance."""
    return ConversationService(mock_conversation_repo)


class TestConversationService:
    """Test suite for ConversationService."""

    @pytest.mark.asyncio
    async def test_create_conversation(self, conversation_service):
        """Test conversation creation."""
        user_id = "test_user"
        session_id = "test_session"
        title = "Test Conversation"

        conversation = await conversation_service.create_conversation(
            user_id=user_id,
            session_id=session_id,
            title=title
        )

        assert conversation is not None
        assert conversation.user_id == user_id
        assert conversation.session_id == session_id
        assert conversation.title == title
        assert conversation.status == ConversationStatus.ACTIVE
        assert conversation.message_count == 0

    @pytest.mark.asyncio
    async def test_get_conversation(self, conversation_service):
        """Test getting a conversation by ID."""
        conversation_id = uuid4()

        conversation_data = await conversation_service.get_conversation_with_messages(
            conversation_id=conversation_id,
            message_limit=10
        )

        assert conversation_data is not None
        assert "id" in conversation_data
        assert "user_id" in conversation_data
        assert "session_id" in conversation_data
        assert "status" in conversation_data
        assert "messages" in conversation_data

    @pytest.mark.asyncio
    async def test_get_or_create_session(self, conversation_service):
        """Test getting or creating a session."""
        user_id = "test_user"
        session_id = "test_session"

        # First call should create
        conversation = await conversation_service.get_or_create_session(
            user_id=user_id,
            session_id=session_id,
            title="Test Session"
        )

        assert conversation is not None
        assert conversation.session_id == session_id

        # Second call should return existing
        conversation2 = await conversation_service.get_or_create_session(
            user_id=user_id,
            session_id=session_id
        )

        assert conversation.id == conversation2.id

    @pytest.mark.asyncio
    async def test_add_message(self, conversation_service):
        """Test adding a message to conversation."""
        conversation = await conversation_service.create_conversation(
            user_id="test_user",
            session_id="test_session"
        )

        conversation_id = conversation.id
        role = "user"
        content = "Hello"
        metadata = {"test": True}

        result = await conversation_service.add_message(
            conversation_id=conversation_id,
            role=role,
            content=content,
            metadata=metadata
        )

        assert result == True

    @pytest.mark.asyncio
    async def test_get_conversation_messages(self, conversation_service):
        """Test getting conversation messages."""
        conversation = await conversation_service.create_conversation(
            user_id="test_user",
            session_id="test_session"
        )

        # Add some messages
        await conversation_service.add_message(
            conversation_id=conversation.id,
            role="user",
            content="Hello"
        )
        await conversation_service.add_message(
            conversation_id=conversation.id,
            role="agent",
            content="Hi!"
        )

        # Get messages
        messages = await conversation_service.get_conversation_messages(
            conversation_id=conversation.id,
            limit=10
        )

        assert len(messages) == 2
        assert messages[0]["role"] == "user"
        assert messages[0]["content"] == "Hello"
        assert messages[1]["role"] == "agent"
        assert messages[1]["content"] == "Hi!"

    @pytest.mark.asyncio
    async def test_get_user_conversations(self, conversation_service):
        """Test getting user conversations."""
        user_id = "test_user"

        # Create multiple conversations
        await conversation_service.create_conversation(
            user_id=user_id,
            session_id="session1"
        )
        await conversation_service.create_conversation(
            user_id=user_id,
            session_id="session2"
        )

        conversations = await conversation_service.get_user_conversations(
            user_id=user_id,
            limit=20
        )

        assert len(conversations) >= 2
        assert all(conv.user_id == user_id for conv in conversations)

    @pytest.mark.asyncio
    async def test_expire_conversation(self, conversation_service):
        """Test expiring a conversation."""
        conversation = await conversation_service.create_conversation(
            user_id="test_user",
            session_id="test_session"
        )

        conversation_id = conversation.id

        # Expire conversation
        result = await conversation_service.expire_conversation(
            conversation_id=conversation_id
        )

        assert result == True

    @pytest.mark.asyncio
    async def test_delete_conversation(self, conversation_service):
        """Test deleting a conversation."""
        conversation = await conversation_service.create_conversation(
            user_id="test_user",
            session_id="test_session"
        )

        conversation_id = conversation.id

        # Delete conversation
        result = await conversation_service.delete_conversation(
            conversation_id=conversation_id
        )

        assert result == True

    @pytest.mark.asyncio
    async def test_get_active_conversation_count(self, conversation_service):
        """Test getting active conversation count."""
        user_id = "test_user"

        # Create active conversations
        await conversation_service.create_conversation(
            user_id=user_id,
            session_id="active1"
        )
        await conversation_service.create_conversation(
            user_id=user_id,
            session_id="active2"
        )

        count = await conversation_service.get_active_conversation_count(
            user_id=user_id,
            limit=5
        )

        assert count == 2

    @pytest.mark.asyncio
    async def test_get_last_message(self, conversation_service):
        """Test getting last message from conversation."""
        conversation = await conversation_service.create_conversation(
            user_id="test_user",
            session_id="test_session"
        )

        # Add messages
        await conversation_service.add_message(
            conversation_id=conversation.id,
            role="user",
            content="First"
        )
        await conversation_service.add_message(
            conversation_id=conversation.id,
            role="agent",
            content="Second"
        )

        # Get last message
        last_message = await conversation_service.get_last_message(
            conversation_id=conversation.id
        )

        assert last_message is not None
        assert last_message["content"] == "Second"

    @pytest.mark.asyncio
    async def test_conversation_errors(self, conversation_service):
        """Test conversation service error handling."""
        user_id = "test_user"
        session_id = "test_session"

        # Test invalid conversation ID
        invalid_id = uuid4()

        conversation_data = await conversation_service.get_conversation_with_messages(
            conversation_id=invalid_id
        )

        assert conversation_data is None

        # Test get_or_create with empty user_id
        from fastapi import HTTPException

        try:
            await conversation_service.get_or_create_session(
                user_id="",
                session_id=session_id
            )
            assert False, "Should have raised exception"
        except HTTPException as e:
            assert e.status_code == 400
