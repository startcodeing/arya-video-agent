"""Schemas for conversation API endpoints."""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class MessageCreate(BaseModel):
    """Schema for creating a new message."""

    role: str = Field(..., description="Message role (user/agent/system)")
    content: str = Field(..., min_length=1, description="Message content")
    metadata: Optional[dict] = Field(None, description="Optional metadata")


class ConversationCreate(BaseModel):
    """Schema for creating a new conversation."""

    title: Optional[str] = Field(None, max_length=200, description="Conversation title")
    agent_name: Optional[str] = Field(None, max_length=100, description="Initial agent name")
    context_window: Optional[int] = Field(10, ge=1, le=50, description="Context window size")
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
    total: int = Field(..., description="Total number of conversations")


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
