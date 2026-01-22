"""Script entity model."""

from typing import Optional

from sqlalchemy import ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, TimestampMixin, UUIDMixin


class Script(Base, UUIDMixin, TimestampMixin):
    """Script entity for generated video scripts."""

    __tablename__ = "scripts"

    # Foreign key
    task_id: Mapped[str] = mapped_column(
        ForeignKey("tasks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Script content
    title: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    synopsis: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    structured_content: Mapped[dict] = mapped_column(JSON, default={}, nullable=False)

    # Style information
    style_tags: Mapped[list] = mapped_column(JSON, default=[], nullable=False)
    visual_style: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    mood: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Metadata
    total_duration: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    scene_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Model information
    llm_model: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    llm_tokens_used: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)


__all__ = ["Script"]
