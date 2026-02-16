"""Conversation entity model."""

from datetime import datetime
from typing import Optional, List
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin, UUIDMixin


class ConversationStatus(str, Enum):
    """Conversation status enum."""

    ACTIVE = "active"
    ARCHIVED = "archived"
    EXPIRED = "expired"


class Conversation(Base, UUIDMixin, TimestampMixin):
    """Conversation entity for managing user dialogues and session state.

    This model stores conversation metadata and message history for tracking
    user interactions across multiple agent executions.
    """

    __tablename__ = "conversations"

    # User identification
    user_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)

    # Session management
    session_id: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)

    # Task association (optional - conversation can exist without a task)
    task_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("tasks.id"),
        nullable=True,
        index=True
    )

    # Conversation metadata
    title: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    status: Mapped[str] = mapped_column(
        String(50),
        default=ConversationStatus.ACTIVE,
        nullable=False
    )

    # Message history (stored as JSON)
    messages: Mapped[dict] = mapped_column(JSON, default={}, nullable=False)

    # Conversation metadata (stored as JSON)
    metadata: Mapped[dict] = mapped_column(JSON, default={}, nullable=False)

    # Session configuration
    agent_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    context_window: Mapped[int] = mapped_column(Integer, default=10, nullable=False)

    # Message count tracking
    message_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Expiration management
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    task: Mapped[Optional["Task"]] = relationship("Task", back_populates="conversations")

    def __repr__(self) -> str:
        return f"<Conversation(id={self.id}, user_id={self.user_id}, session_id={self.session_id}, status={self.status})>"

    def is_active(self) -> bool:
        """Check if conversation is active."""
        return self.status == ConversationStatus.ACTIVE

    def is_expired(self) -> bool:
        """Check if conversation has expired."""
        if self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at

    def add_message(self, role: str, content: str, metadata: Optional[dict] = None) -> None:
        """
        Add a message to the conversation.

        Args:
            role: Message role (user/agent/system)
            content: Message content
            metadata: Optional message metadata
        """
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow().isoformat(),
        }

        if metadata:
            message["metadata"] = metadata

        self.messages[str(self.message_count)] = message
        self.message_count += 1

    def get_last_message(self) -> Optional[dict]:
        """
        Get the last message in the conversation.

        Returns:
            Last message dict or None
        """
        if self.message_count == 0:
            return None

        last_key = str(self.message_count - 1)
        return self.messages.get(last_key)

    def get_message_history(self, limit: Optional[int] = None) -> List[dict]:
        """
        Get message history.

        Args:
            limit: Maximum number of messages to return (None = all)

        Returns:
            List of message dicts
        """
        if limit is None or limit > self.message_count:
            limit = self.message_count

        message_list = []
        for i in range(limit):
            message = self.messages.get(str(i))
            if message:
                message_list.append(message)

        return message_list

    def update_metadata(self, metadata: dict) -> None:
        """
        Update conversation metadata.

        Args:
            metadata: New metadata dict
        """
        self.metadata.update(metadata)

    def expire(self) -> None:
        """Mark conversation as expired."""
        self.status = ConversationStatus.EXPIRED
