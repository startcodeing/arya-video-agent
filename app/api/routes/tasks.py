"""Task-related API routes."""

import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas import (
    TaskCreateRequest,
    TaskCreateResponse,
    TaskDetailResponse,
    TaskListResponse,
    TaskResponse,
    VideoDownloadResponse,
    VideoMetadata,
    ThumbnailResponse,
)
from app.core.task_manager import task_manager
from app.database.session import get_db
from app.entities.task import Task, TaskStatus, TaskPriority
from app.services.storage import StorageService
from app.services.video_processor import video_processor
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/tasks", tags=["tasks"])


@router.post("", response_model=TaskCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    request: TaskCreateRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new video generation task.

    Args:
        request: Task creation request
        db: Database session

    Returns:
        Created task information
    """
    try:
        # Create new task
        task = Task(
            user_id="default_user",  # TODO: Get from auth context
            topic=request.topic,
            style=request.style,
            options=request.options or {},
            priority=request.priority,
        )

        # Add to database
        db.add(task)
        await db.commit()
        await db.refresh(task)

        logger.info(f"Created task {task.id} for topic: {request.topic}")

        # Submit to Celery for async processing
        # TODO: Submit to Celery queue
        # from app.scheduler.tasks import process_video_task
        # process_video_task.delay(str(task.id))

        return TaskCreateResponse(
            task_id=task.id,
            status=task.status,
            message="Task created successfully and queued for processing",
            estimated_duration=task.estimated_duration,
        )

    except Exception as e:
        logger.error(f"Failed to create task: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create task: {str(e)}"
        )


@router.get("", response_model=TaskListResponse)
async def list_tasks(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    status: Optional[TaskStatus] = None,
    priority: Optional[TaskPriority] = None,
    user_id: Optional[str] = None,
    sort_by: str = Query(default="created_at", pattern="^(created_at|updated_at|priority|progress)$"),
    sort_order: str = Query(default="desc", pattern="^(asc|desc)$"),
    db: AsyncSession = Depends(get_db),
):
    """
    List tasks with filtering and pagination.

    Args:
        limit: Maximum number of results
        offset: Number of results to skip
        status: Filter by status
        priority: Filter by priority
        user_id: Filter by user ID
        sort_by: Field to sort by
        sort_order: Sort direction
        db: Database session

    Returns:
        Paginated list of tasks
    """
    try:
        # Build query
        query = select(Task)

        # Apply filters
        if status:
            query = query.where(Task.status == status)
        if priority:
            query = query.where(Task.priority == priority)
        if user_id:
            query = query.where(Task.user_id == user_id)

        # Get total count
        count_query = select(Task.id)
        if status:
            count_query = count_query.where(Task.status == status)
        if priority:
            count_query = count_query.where(Task.priority == priority)
        if user_id:
            count_query = count_query.where(Task.user_id == user_id)

        # Execute count
        from sqlalchemy import func
        total_result = await db.execute(select(func.count()).select_from(count_query))
        total = total_result.scalar_one()

        # Apply sorting
        sort_column = getattr(Task, sort_by)
        if sort_order == "desc":
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())

        # Apply pagination
        query = query.limit(limit).offset(offset)

        # Execute query
        result = await db.execute(query)
        tasks = result.scalars().all()

        return TaskListResponse(
            tasks=[TaskResponse.model_validate(task) for task in tasks],
            total=total,
            limit=limit,
            offset=offset,
        )

    except Exception as e:
        logger.error(f"Failed to list tasks: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list tasks: {str(e)}"
        )


@router.get("/{task_id}", response_model=TaskDetailResponse)
async def get_task(
    task_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Get detailed information about a specific task.

    Args:
        task_id: Task UUID
        db: Database session

    Returns:
        Detailed task information
    """
    try:
        # Query task
        result = await db.execute(select(Task).where(Task.id == task_id))
        task = result.scalar_one_or_none()

        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task {task_id} not found"
            )

        return TaskDetailResponse.model_validate(task)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get task {task_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get task: {str(e)}"
        )


@router.get("/{task_id}/status")
async def get_task_status(
    task_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Get current status of a task (lightweight endpoint).

    Args:
        task_id: Task UUID
        db: Database session

    Returns:
        Task status information
    """
    try:
        # Query task
        result = await db.execute(
            select(Task.id, Task.status, Task.progress, Task.current_agent, Task.error_message)
            .where(Task.id == task_id)
        )
        task_data = result.first()

        if not task_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task {task_id} not found"
            )

        return {
            "task_id": task_data[0],
            "status": task_data[1],
            "progress": task_data[2],
            "current_agent": task_data[3],
            "error_message": task_data[4],
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get task status {task_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get task status: {str(e)}"
        )


@router.post("/{task_id}/cancel", status_code=status.HTTP_202_ACCEPTED)
async def cancel_task(
    task_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Cancel a running or pending task.

    Args:
        task_id: Task UUID
        db: Database session

    Returns:
        Cancellation confirmation
    """
    try:
        # Query task
        result = await db.execute(select(Task).where(Task.id == task_id))
        task = result.scalar_one_or_none()

        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task {task_id} not found"
            )

        # Check if task can be cancelled
        from app.core.state_machine import TaskStateMachine
        if TaskStateMachine.is_terminal(task.status):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot cancel task in {task.status} status"
            )

        # Update status to cancelled
        task.status = TaskStatus.CANCELLED

        await db.commit()
        await db.refresh(task)

        logger.info(f"Task {task_id} cancelled")

        return {
            "task_id": task_id,
            "status": task.status,
            "message": "Task cancelled successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to cancel task {task_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cancel task: {str(e)}"
        )


@router.post("/{task_id}/retry", status_code=status.HTTP_202_ACCEPTED)
async def retry_task(
    task_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Retry a failed task.

    Args:
        task_id: Task UUID
        db: Database session

    Returns:
        Retry confirmation
    """
    try:
        # Query task
        result = await db.execute(select(Task).where(Task.id == task_id))
        task = result.scalar_one_or_none()

        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task {task_id} not found"
            )

        # Check if task can be retried
        if task.status != TaskStatus.FAILED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only failed tasks can be retried"
            )

        if task.retry_count >= task.max_retries:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Task has reached maximum retry limit ({task.max_retries})"
            )

        # Increment retry count
        task.retry_count += 1
        task.status = TaskStatus.RETRYING
        task.error_message = None
        task.error_code = None
        task.failed_step = None

        await db.commit()
        await db.refresh(task)

        # Re-submit to Celery
        # TODO: Submit to Celery queue
        # from app.scheduler.tasks import process_video_task
        # process_video_task.delay(str(task.id))

        logger.info(f"Task {task_id} queued for retry (attempt {task.retry_count})")

        return {
            "task_id": task_id,
            "status": task.status,
            "retry_count": task.retry_count,
            "message": "Task queued for retry"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retry task {task_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retry task: {str(e)}"
        )


@router.get("/{task_id}/video", response_model=VideoDownloadResponse)
async def download_video(
    task_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Get download URL for the generated video.

    Args:
        task_id: Task UUID
        db: Database session

    Returns:
        Video download information
    """
    try:
        # Query task
        result = await db.execute(select(Task).where(Task.id == task_id))
        task = result.scalar_one_or_none()

        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task {task_id} not found"
            )

        # Check if task is completed
        if task.status != TaskStatus.COMPLETED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Video not available. Task status: {task.status}"
            )

        if not task.output_video_url:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Video output not found"
            )

        # Get video metadata if available
        metadata = VideoMetadata(
            duration=task.output_metadata.get("duration", 0),
            width=task.output_metadata.get("width"),
            height=task.output_metadata.get("height"),
            fps=task.output_metadata.get("fps"),
        )

        return VideoDownloadResponse(
            task_id=task.id,
            video_url=task.output_video_url,
            metadata=metadata,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get video download {task_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get video download: {str(e)}"
        )


@router.get("/{task_id}/thumbnail", response_model=ThumbnailResponse)
async def get_thumbnail(
    task_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Get thumbnail image for the video.

    Args:
        task_id: Task UUID
        db: Database session

    Returns:
        Thumbnail image information
    """
    try:
        # Query task
        result = await db.execute(select(Task).where(Task.id == task_id))
        task = result.scalar_one_or_none()

        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task {task_id} not found"
            )

        # Check if task is completed
        if task.status != TaskStatus.COMPLETED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Thumbnail not available. Task status: {task.status}"
            )

        # Get thumbnail URL from output metadata
        thumbnail_url = task.output_metadata.get("thumbnail_url")
        if not thumbnail_url:
            # Try to generate thumbnail from video
            if task.output_video_path:
                # TODO: Generate thumbnail using FFmpeg
                # For now, return video URL as fallback
                thumbnail_url = task.output_video_url
            else:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Thumbnail not found"
                )

        return ThumbnailResponse(
            task_id=task.id,
            thumbnail_url=thumbnail_url,
            width=1920,  # TODO: Get actual dimensions
            height=1080,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get thumbnail {task_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get thumbnail: {str(e)}"
        )


__all__ = ["router"]
