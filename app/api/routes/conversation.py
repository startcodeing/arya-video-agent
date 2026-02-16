"""Conversation API routes."""

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas.conversation import (
    ConversationCreate,
    ConversationUpdate,
    ConversationResponse,
    ConversationListResponse,
    MessageCreate,
    ConversationWithMessagesResponse,
)
from app.services.conversation_service import ConversationService
from app.database.session import get_db
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/conversations", tags=["conversations"])


@router.post("/", response_model=ConversationResponse, status_code=201)
async def create_conversation(
    request: ConversationCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new conversation.

    Args:
        request: Conversation creation request

    Returns:
        Created conversation
    """
    conversation_service = ConversationService(db)

    try:
        conversation = await conversation_service.create_conversation(
            user_id="demo_user",  # TODO: Get from auth context
            session_id="session_123",  # TODO: Generate unique session ID
            title=request.title,
            agent_name=request.agent_name,
            context_window=request.context_window,
        )
        return conversation

    except Exception as e:
        logger.error(f"Failed to create conversation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{conversation_id}", response_model=ConversationWithMessagesResponse)
async def get_conversation(
    conversation_id: UUID,
    message_limit: int = Query(10, ge=1, le=100, description="Number of messages to include"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get conversation with messages.

    Args:
        conversation_id: Conversation ID
        message_limit: Maximum number of messages to return

    Returns:
        Conversation with messages

    Raises:
        HTTPException: If conversation not found
    """
    conversation_service = ConversationService(db)

    try:
        conversation_data = await conversation_service.get_conversation_with_messages(
            conversation_id=conversation_id,
            message_limit=message_limit
        )

        if not conversation_data:
            raise HTTPException(status_code=404, detail="Conversation not found")

        return conversation_data

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to get conversation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=ConversationListResponse)
async def list_conversations(
    user_id: str = Query(..., description="User ID"),
    limit: int = Query(20, ge=1, le=50, description="Maximum number of conversations to return"),
    offset: int = Query(0, ge=0, description="Number of conversations to skip"),
    active_only: bool = Query(True, description="Only return active conversations"),
    db: AsyncSession = Depends(get_db),
):
    """
    List conversations for a user.

    Args:
        user_id: User ID
        limit: Maximum number of conversations to return
        offset: Number of conversations to skip
        active_only: Only return active conversations

    Returns:
        List of conversations

    Raises:
        HTTPException: If user_id is not provided
    """
    if not user_id:
        raise HTTPException(status_code=400, detail="user_id is required")

    conversation_service = ConversationService(db)

    try:
        conversations = await conversation_service.get_user_conversations(
            user_id=user_id,
            limit=limit,
            offset=offset,
            active_only=active_only,
        )

        return {
            "conversations": conversations,
            "total": len(conversations),
            "limit": limit,
            "offset": offset,
        }

    except Exception as e:
        logger.error(f"Failed to list conversations: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{conversation_id}/messages", response_model=dict, status_code=201)
async def add_message(
    conversation_id: UUID,
    request: MessageCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    Add a message to conversation.

    Args:
        conversation_id: Conversation ID
        request: Message creation request

    Returns:
        Success status

    Raises:
        HTTPException: If message addition fails
    """
    conversation_service = ConversationService(db)

    try:
        success = await conversation_service.add_message(
            conversation_id=conversation_id,
            role=request.role,
            content=request.content,
            metadata=request.metadata,
        )

        if not success:
            raise HTTPException(status_code=400, detail="Failed to add message")

        return {"status": "success", "message_id": "N/A"}

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to add message: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{conversation_id}", response_model=ConversationResponse)
async def update_conversation(
    conversation_id: UUID,
    request: ConversationUpdate,
    db: AsyncSession = Depends(get_db),
):
    """
    Update conversation metadata.

    Args:
        conversation_id: Conversation ID
        request: Conversation update request

    Returns:
        Updated conversation

    Raises:
        HTTPException: If conversation not found or update fails
    """
    conversation_service = ConversationService(db)

    try:
        # Get existing conversation
        conversation = await conversation_service.get_conversation(conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")

        # Update conversation (simplified, normally would update all fields)
        if request.title is not None:
            # TODO: Implement actual update in service
            pass

        # Return updated conversation
        conversation_data = await conversation_service.get_conversation_with_messages(
            conversation_id=conversation_id,
            message_limit=1
        )

        return conversation_data

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to update conversation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{conversation_id}", response_model=dict)
async def delete_conversation(
    conversation_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Delete a conversation.

    Args:
        conversation_id: Conversation ID

    Returns:
        Success status

    Raises:
        HTTPException: If deletion fails
    """
    conversation_service = ConversationService(db)

    try:
        success = await conversation_service.delete_conversation(conversation_id)

        if not success:
            raise HTTPException(status_code=400, detail="Failed to delete conversation")

        return {"status": "success"}

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to delete conversation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/active/{user_id}", response_model=dict)
async def get_active_conversation_count(
    user_id: str,
    limit: int = Query(5, ge=1, le=10, description="Maximum count to return"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get number of active conversations for a user (with limit).

    Args:
        user_id: User ID
        limit: Maximum count to return

    Returns:
        Active conversation count

    Raises:
        HTTPException: If retrieval fails
    """
    if not user_id:
        raise HTTPException(status_code=400, detail="user_id is required")

    conversation_service = ConversationService(db)

    try:
        count = await conversation_service.get_active_conversation_count(
            user_id=user_id,
            limit=limit,
        )

        return {"active_count": count}

    except Exception as e:
        logger.error(f"Failed to get active conversation count: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
