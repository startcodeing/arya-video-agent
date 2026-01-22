"""Task entity model."""

from enum import Enum
from typing import Optional

from sqlalchemy import Float, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, TimestampMixin, UUIDMixin


class TaskStatus(str, Enum):
    """Task status enum."""

    PENDING = "pending"
    STYLE_DETECTION = "style_detection"
    STORY_GENERATION = "story_generation"
    STORYBOARD_BREAKDOWN = "storyboard_breakdown"
    IMAGE_GENERATION = "image_generation"
    VIDEO_GENERATION = "video_generation"
    COMPOSING = "composing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"


class TaskPriority(str, Enum):
    """Task priority enum."""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class Task(Base, UUIDMixin, TimestampMixin):
    """Task entity for video generation jobs."""

    __tablename__ = "tasks"

    # User identification
    user_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)

    # Input fields
    topic: Mapped[str] = mapped_column(Text, nullable=False)
    style: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    options: Mapped[dict] = mapped_column(JSON, default={}, nullable=False)

    # Status management
    status: Mapped[str] = mapped_column(
        String(50),
        default=TaskStatus.PENDING,
        nullable=False,
        index=True,
    )
    priority: Mapped[str] = mapped_column(
        String(20),
        default=TaskPriority.NORMAL,
        nullable=False,
    )
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    max_retries: Mapped[int] = mapped_column(Integer, default=3, nullable=False)

    # Progress tracking
    current_agent: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    progress: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    estimated_duration: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    elapsed_duration: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Error handling
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    error_code: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    failed_step: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Output fields
    output_video_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    output_video_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    output_metadata: Mapped[dict] = mapped_column(JSON, default={}, nullable=False)


__all__ = ["Task", "TaskStatus", "TaskPriority"]
