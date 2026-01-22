"""Resource entity model."""

from enum import Enum
from typing import Optional

from sqlalchemy import ForeignKey, Float, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, TimestampMixin, UUIDMixin


class ResourceType(str, Enum):
    """Resource type enum."""

    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    THUMBNAIL = "thumbnail"


class Resource(Base, UUIDMixin, TimestampMixin):
    """Resource entity for generated media files."""

    __tablename__ = "resources"

    # Foreign key
    task_id: Mapped[str] = mapped_column(
        ForeignKey("tasks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Resource information
    resource_type: Mapped[str] = mapped_column(String(20), nullable=False)
    file_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    file_size: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    mime_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Storage
    storage_provider: Mapped[str] = mapped_column(String(50), default="local", nullable=False)
    storage_key: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    public_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    signed_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    signed_url_expires_at: Mapped[Optional[object]] = mapped_column(nullable=True)

    # Media metadata
    width: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    height: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    duration: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    fps: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    codec: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Generation information
    generation_model: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    generation_prompt: Mapped[Optional[str]] = mapped_column(nullable=True)
    generation_parameters: Mapped[dict] = mapped_column(JSON, default={}, nullable=False)

    # Expiration
    expires_at: Mapped[Optional[object]] = mapped_column(nullable=True)


__all__ = ["Resource", "ResourceType"]
