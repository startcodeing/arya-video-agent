"""Storyboard entity model."""

from typing import Optional

from sqlalchemy import ForeignKey, Float, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, TimestampMixin, UUIDMixin


class Storyboard(Base, UUIDMixin, TimestampMixin):
    """Storyboard entity for video shots."""

    __tablename__ = "storyboards"

    # Foreign keys
    task_id: Mapped[str] = mapped_column(
        ForeignKey("tasks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    script_id: Mapped[str] = mapped_column(
        ForeignKey("scripts.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Storyboard information
    sequence_number: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    dialogue: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Visual information
    camera_movement: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    shot_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    duration: Mapped[float] = mapped_column(Float, default=3.0, nullable=False)

    # Generation status
    first_frame_image_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey("resources.id", ondelete="SET NULL"),
        nullable=True,
    )
    video_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey("resources.id", ondelete="SET NULL"),
        nullable=True,
    )
    generation_status: Mapped[str] = mapped_column(
        String(50),
        default="pending",
        nullable=False,
    )

    # Enhanced information
    composition_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    lighting: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    color_palette: Mapped[list] = mapped_column(JSON, default=[], nullable=False)

    # Timestamp
    generated_at: Mapped[Optional[object]] = mapped_column(nullable=True)


__all__ = ["Storyboard"]
