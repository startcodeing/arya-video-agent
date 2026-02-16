"""Pydantic schemas for API requests and responses."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, ConfigDict

from app.entities.task import TaskStatus, TaskPriority


# ============================================================================
# Request Schemas
# ============================================================================

class TaskCreateRequest(BaseModel):
    """Schema for creating a new video generation task."""

    topic: str = Field(
        ...,
        min_length=3,
        max_length=1000,
        description="Topic/theme for the video",
        examples=["A journey through the Swiss Alps"]
    )

    style: Optional[str] = Field(
        None,
        max_length=100,
        description="Desired video style (optional, will auto-detect if not provided)",
        examples=["cinematic", "documentary", "animated"]
    )

    options: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Additional options for video generation",
        examples=[
            {
                "duration": 60,
                "aspect_ratio": "16:9",
                "target_audience": "general"
            }
        ]
    )

    priority: Optional[TaskPriority] = Field(
        default=TaskPriority.NORMAL,
        description="Task priority level"
    )

    webhook_url: Optional[str] = Field(
        None,
        max_length=500,
        description="Webhook URL to receive task completion notification"
    )

    @field_validator('topic')
    @classmethod
    def validate_topic(cls, v: str) -> str:
        """Validate topic is not empty or just whitespace."""
        if not v or not v.strip():
            raise ValueError('Topic cannot be empty')
        return v.strip()

    @field_validator('webhook_url')
    @classmethod
    def validate_webhook_url(cls, v: Optional[str]) -> Optional[str]:
        """Validate webhook URL format if provided."""
        if v:
            from urllib.parse import urlparse
            try:
                result = urlparse(v)
                if not all([result.scheme, result.netloc]):
                    raise ValueError('Invalid webhook URL format')
                if result.scheme not in ['http', 'https']:
                    raise ValueError('Webhook URL must use HTTP or HTTPS')
            except Exception as e:
                raise ValueError(f'Invalid webhook URL: {e}')
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "topic": "A journey through the Swiss Alps",
                    "style": "cinematic",
                    "options": {"duration": 60},
                    "priority": "normal"
                }
            ]
        }
    }


class TaskListQuery(BaseModel):
    """Schema for task list query parameters."""

    limit: int = Field(
        default=20,
        ge=1,
        le=100,
        description="Maximum number of tasks to return"
    )

    offset: int = Field(
        default=0,
        ge=0,
        description="Number of tasks to skip"
    )

    status: Optional[TaskStatus] = Field(
        None,
        description="Filter by task status"
    )

    priority: Optional[TaskPriority] = Field(
        None,
        description="Filter by task priority"
    )

    user_id: Optional[str] = Field(
        None,
        max_length=100,
        description="Filter by user ID"
    )

    sort_by: str = Field(
        default="created_at",
        pattern="^(created_at|updated_at|priority|progress)$",
        description="Field to sort by"
    )

    sort_order: str = Field(
        default="desc",
        pattern="^(asc|desc)$",
        description="Sort order (ascending or descending)"
    )


# ============================================================================
# Response Schemas
# ============================================================================

class TaskResponse(BaseModel):
    """Schema for task response."""

    id: UUID = Field(..., description="Unique task identifier")
    user_id: str = Field(..., description="User who created the task")
    topic: str = Field(..., description="Task topic")
    style: Optional[str] = Field(None, description="Video style")
    status: TaskStatus = Field(..., description="Current task status")
    priority: TaskPriority = Field(..., description="Task priority")
    progress: float = Field(..., ge=0, le=100, description="Progress percentage")
    current_agent: Optional[str] = Field(None, description="Currently executing agent")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    retry_count: int = Field(..., ge=0, description="Number of retry attempts")
    elapsed_duration: int = Field(..., ge=0, description="Elapsed time in seconds")
    output_video_url: Optional[str] = Field(None, description="Final video URL")
    created_at: datetime = Field(..., description="Task creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    model_config = ConfigDict(from_attributes=True)


class TaskDetailResponse(TaskResponse):
    """Schema for detailed task response with additional info."""

    options: Dict[str, Any] = Field(default_factory=dict, description="Task options")
    output_metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Output video metadata"
    )
    estimated_duration: Optional[int] = Field(
        None,
        description="Estimated total duration in seconds"
    )
    failed_step: Optional[str] = Field(None, description="Step where task failed")
    error_code: Optional[str] = Field(None, description="Error code if failed")


class TaskListResponse(BaseModel):
    """Schema for task list response."""

    tasks: List[TaskResponse] = Field(..., description="List of tasks")
    total: int = Field(..., ge=0, description="Total number of tasks")
    limit: int = Field(..., ge=1, le=100, description="Results per page")
    offset: int = Field(..., ge=0, description="Number of results skipped")


class TaskCreateResponse(BaseModel):
    """Schema for task creation response."""

    task_id: UUID = Field(..., description="Created task ID")
    status: TaskStatus = Field(..., description="Initial task status")
    message: str = Field(..., description="Response message")
    estimated_duration: Optional[int] = Field(
        None,
        description="Estimated completion time in seconds"
    )


class ProgressUpdate(BaseModel):
    """Schema for task progress update."""

    task_id: UUID = Field(..., description="Task identifier")
    status: TaskStatus = Field(..., description="Current status")
    progress: float = Field(..., ge=0, le=100, description="Progress percentage")
    current_agent: Optional[str] = Field(None, description="Current agent")
    message: Optional[str] = Field(None, description="Status message")
    timestamp: datetime = Field(default_factory=datetime.now, description="Update timestamp")


class ErrorResponse(BaseModel):
    """Schema for error responses."""

    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    path: Optional[str] = Field(None, description="Request path")
    timestamp: datetime = Field(default_factory=datetime.now, description="Error timestamp")


class HealthResponse(BaseModel):
    """Schema for health check response."""

    status: str = Field(..., description="Service status")
    version: str = Field(..., description="API version")
    database: str = Field(..., description="Database connection status")
    redis: str = Field(..., description="Redis connection status")
    celery: str = Field(..., description="Celery worker status")


# ============================================================================
# Video-specific Schemas
# ============================================================================

class VideoMetadata(BaseModel):
    """Schema for video metadata."""

    duration: float = Field(..., gt=0, description="Video duration in seconds")
    width: Optional[int] = Field(None, gt=0, description="Video width")
    height: Optional[int] = Field(None, gt=0, description="Video height")
    fps: Optional[int] = Field(None, gt=0, description="Frames per second")
    codec: Optional[str] = Field(None, description="Video codec")
    file_size: Optional[int] = Field(None, ge=0, description="File size in bytes")


class VideoDownloadResponse(BaseModel):
    """Schema for video download response."""

    task_id: UUID = Field(..., description="Task identifier")
    video_url: str = Field(..., description="Video download URL")
    metadata: VideoMetadata = Field(..., description="Video metadata")
    expires_at: Optional[datetime] = Field(None, description="URL expiration time")


class ThumbnailResponse(BaseModel):
    """Schema for thumbnail response."""

    task_id: UUID = Field(..., description="Task identifier")
    thumbnail_url: str = Field(..., description="Thumbnail image URL")
    width: int = Field(..., gt=0, description="Thumbnail width")
    height: int = Field(..., gt=0, description="Thumbnail height")


# ============================================================================
# WebSocket Schemas
# ============================================================================

class WebSocketMessage(BaseModel):
    """Base schema for WebSocket messages."""

    type: str = Field(..., description="Message type")
    data: Dict[str, Any] = Field(default_factory=dict, description="Message data")
    timestamp: datetime = Field(default_factory=datetime.now, description="Message timestamp")


class WebSocketAuth(BaseModel):
    """Schema for WebSocket authentication."""

    token: Optional[str] = Field(None, description="Authentication token")
    task_id: Optional[UUID] = Field(None, description="Task ID to subscribe")


class WebSocketConnectionRequest(BaseModel):
    """Schema for WebSocket connection request."""

    task_ids: List[UUID] = Field(
        ...,
        min_length=1,
        max_length=10,
        description="List of task IDs to subscribe to"
    )


# ============================================================================
# Webhook Schemas
# ============================================================================

class WebhookPayload(BaseModel):
    """Schema for webhook payload."""

    event: str = Field(..., description="Event type")
    task_id: UUID = Field(..., description="Task identifier")
    status: TaskStatus = Field(..., description="Task status")
    timestamp: datetime = Field(default_factory=datetime.now, description="Event timestamp")
    data: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional event data"
    )


# ============================================================================
# Export all schemas
# ============================================================================

__all__ = [
    # Request schemas
    "TaskCreateRequest",
    "TaskListQuery",
    "WebSocketAuth",
    "WebSocketConnectionRequest",
    # Response schemas
    "TaskResponse",
    "TaskDetailResponse",
    "TaskListResponse",
    "TaskCreateResponse",
    "ProgressUpdate",
    "ErrorResponse",
    "HealthResponse",
    "VideoMetadata",
    "VideoDownloadResponse",
    "ThumbnailResponse",
    "WebSocketMessage",
    "WebhookPayload",
]


# ============================================================================
# Conversation Schemas
# ============================================================================

class MessageCreate(BaseModel):
    """Schema for creating a new message."""
    role: str = Field(..., min_length=1, description="Message role (user/agent/system)")
    content: str = Field(..., min_length=1, description="Message content")
    metadata: Optional[dict] = Field(None, description="Optional metadata")


class ConversationCreate(BaseModel):
    """Schema for creating a new conversation."""
    title: Optional[str] = Field(None, max_length=200, description="Conversation title")
    agent_name: Optional[str] = Field(None, max_length=100, description="Initial agent name")
    context_window: Optional[int] = Field(10, ge=1, le=50, description="Context window size")
    task_id: Optional[str] = Field(None, description="Associated task ID")
    metadata: Optional[dict] = Field(None, description="Optional conversation metadata")


class ConversationUpdate(BaseModel):
    """Schema for updating a conversation."""
    title: Optional[str] = Field(None, max_length=200)
    status: Optional[str] = Field(None, description="Conversation status")
    metadata: Optional[dict] = Field(None)


class ConversationResponse(BaseModel):
    """Schema for conversation response."""
    id: str = Field(..., description="Conversation ID")
    user_id: str = Field(..., description="User ID")
    session_id: str = Field(..., description="Session ID")
    title: Optional[str] = Field(None, description="Conversation title")
    status: str = Field(..., description="Conversation status")
    agent_name: Optional[str] = Field(None, description="Current agent name")
    message_count: int = Field(..., description="Total message count")
    context_window: int = Field(..., description="Context window size")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    expires_at: Optional[datetime] = Field(None, description="Expiration timestamp")

    class Config:
        from_attributes = True


class ConversationListResponse(BaseModel):
    """Schema for conversation list response."""
    conversations: List[ConversationResponse] = Field(..., description="List of conversations")
    total: int = Field(..., ge=0, description="Total number of conversations")


class MessageResponse(BaseModel):
    """Schema for message response."""
    id: str = Field(..., description="Message index")
    role: str = Field(..., description="Message role")
    content: str = Field(..., description="Message content")
    timestamp: str = Field(..., description="Message timestamp")
    metadata: Optional[dict] = Field(None, description="Optional metadata")


class ConversationWithMessagesResponse(ConversationResponse):
    """Schema for conversation with messages."""
    messages: List[MessageResponse] = Field(..., description="List of messages")


# Update __all__ to include conversation schemas
__all__ = [
    # Request schemas
    "TaskCreateRequest",
    "TaskListQuery",
    "WebSocketAuth",
    "WebSocketConnectionRequest",
    # Response schemas
    "TaskResponse",
    "TaskDetailResponse",
    "TaskListResponse",
    "TaskCreateResponse",
    "ProgressUpdate",
    "ErrorResponse",
    "HealthResponse",
    "VideoMetadata",
    "VideoDownloadResponse",
    "ThumbnailResponse",
    "WebSocketMessage",
    "WebhookPayload",
    # Conversation schemas
    "MessageCreate",
    "ConversationCreate",
    "ConversationUpdate",
    "ConversationResponse",
    "ConversationListResponse",
    "MessageResponse",
    "ConversationWithMessagesResponse",
]
