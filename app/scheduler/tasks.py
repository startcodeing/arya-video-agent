"""Celery task definitions for async video processing."""

import asyncio
from typing import Dict, Any
from celery import shared_task
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.task_manager import task_manager
from app.core.state_machine import TaskStateMachine, TaskStatus
from app.database.session import async_session_maker
from app.agents.style import StyleAgent
from app.agents.story import StoryAgent
from app.agents.storyboard import StoryboardAgent
from app.agents.image import ImageAgent
from app.agents.video import VideoAgent
from app.agents.composer import ComposerAgent
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Initialize agents
_agents = {
    "style_agent": StyleAgent(),
    "story_agent": StoryAgent(),
    "storyboard_agent": StoryboardAgent(),
    "image_agent": ImageAgent(max_concurrent=3),
    "video_agent": VideoAgent(max_concurrent=2),
    "composer_agent": ComposerAgent(),
}

# Register agents with task manager
for name, agent in _agents.items():
    task_manager.register_agent(name, agent)


@shared_task(
    name="process_video_task",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=600,
    retry_jitter=True,
)
def process_video_task(self, task_id: str) -> Dict[str, Any]:
    """
    Process a video generation task asynchronously.

    This task runs the complete agent pipeline:
    Style -> Story -> Storyboard -> Image -> Video -> Composer

    Args:
        self: Celery task instance
        task_id: Task UUID as string

    Returns:
        Dict containing execution results
    """
    logger.info(f"Processing video task {task_id}")

    # Run async task in sync context
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        result = loop.run_until_complete(_process_task_async(task_id))
        return result
    except Exception as e:
        logger.error(f"Task {task_id} failed: {e}")
        # Update task status
        loop.run_until_complete(_update_task_status(task_id, TaskStatus.FAILED, str(e)))
        raise
    finally:
        loop.close()


async def _process_task_async(task_id: str) -> Dict[str, Any]:
    """
    Async implementation of task processing.

    Args:
        task_id: Task UUID as string

    Returns:
        Dict containing execution results
    """
    async with async_session_maker() as db:
        from sqlalchemy import select
        from app.entities.task import Task
        import uuid

        # Get task from database
        result = await db.execute(select(Task).where(Task.id == uuid.UUID(task_id)))
        task = result.scalar_one_or_none()

        if not task:
            raise ValueError(f"Task {task_id} not found")

        logger.info(f"Starting agent pipeline for task {task_id}")

        # Execute agent pipeline
        try:
            execution_result = await task_manager.execute_task(task, db)

            # Refresh task from database
            await db.refresh(task)

            logger.info(f"Task {task_id} completed with status: {task.status}")

            return {
                "task_id": task_id,
                "status": task.status.value,
                "result": execution_result,
            }

        except Exception as e:
            logger.error(f"Pipeline execution failed for task {task_id}: {e}")

            # Update task with error
            task.status = TaskStatus.FAILED
            task.error_message = str(e)
            await db.commit()

            raise


async def _update_task_status(
    task_id: str,
    status: TaskStatus,
    error_message: str = None
) -> None:
    """
    Update task status in database.

    Args:
        task_id: Task UUID as string
        status: New status
        error_message: Optional error message
    """
    async with async_session_maker() as db:
        from sqlalchemy import select
        from app.entities.task import Task
        import uuid

        result = await db.execute(select(Task).where(Task.id == uuid.UUID(task_id)))
        task = result.scalar_one_or_none()

        if task:
            task.status = status
            if error_message:
                task.error_message = error_message
            await db.commit()


@shared_task(
    name="execute_single_agent",
    bind=True,
    max_retries=2,
)
def execute_single_agent_task(
    self,
    task_id: str,
    agent_name: str,
) -> Dict[str, Any]:
    """
    Execute a single agent for a task.

    Useful for retrying specific steps or debugging.

    Args:
        self: Celery task instance
        task_id: Task UUID as string
        agent_name: Name of agent to execute

    Returns:
        Dict containing execution results
    """
    logger.info(f"Executing agent {agent_name} for task {task_id}")

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        result = loop.run_until_complete(
            _execute_agent_async(task_id, agent_name)
        )
        return result
    except Exception as e:
        logger.error(f"Agent {agent_name} failed for task {task_id}: {e}")
        raise
    finally:
        loop.close()


async def _execute_agent_async(task_id: str, agent_name: str) -> Dict[str, Any]:
    """
    Async implementation of single agent execution.

    Args:
        task_id: Task UUID as string
        agent_name: Name of agent to execute

    Returns:
        Dict containing execution results
    """
    async with async_session_maker() as db:
        from sqlalchemy import select
        from app.entities.task import Task
        import uuid

        result = await db.execute(select(Task).where(Task.id == uuid.UUID(task_id)))
        task = result.scalar_one_or_none()

        if not task:
            raise ValueError(f"Task {task_id} not found")

        # Execute single agent
        agent_result = await task_manager.execute_single_agent(
            task,
            agent_name,
            db,
        )

        return {
            "task_id": task_id,
            "agent": agent_name,
            "result": agent_result,
        }


@shared_task(
    name="send_webhook",
    max_retries=3,
)
def send_webhook_task(
    webhook_url: str,
    payload: Dict[str, Any],
) -> bool:
    """
    Send webhook notification for task completion.

    Args:
        webhook_url: Webhook URL to call
        payload: Webhook payload

    Returns:
        True if successful
    """
    import requests

    try:
        logger.info(f"Sending webhook to {webhook_url}")
        response = requests.post(
            webhook_url,
            json=payload,
            timeout=10,
        )
        response.raise_for_status()
        logger.info(f"Webhook sent successfully: {response.status_code}")
        return True
    except Exception as e:
        logger.error(f"Webhook failed: {e}")
        return False


@shared_task(
    name="cleanup_old_tasks",
)
def cleanup_old_tasks_task(days: int = 7) -> int:
    """
    Clean up old completed/failed tasks.

    Args:
        days: Delete tasks older than this many days

    Returns:
        Number of tasks cleaned up
    """
    logger.info(f"Cleaning up tasks older than {days} days")

    # TODO: Implement cleanup logic
    # - Delete old tasks from database
    # - Delete associated files from storage

    return 0


# Keep the old test task
@shared_task(name="app.scheduler.tasks.hello_world")
def hello_world(name: str = "World") -> str:
    """
    Simple hello world task for testing.

    Args:
        name: Name to greet

    Returns:
        Greeting message
    """
    logger.info(f"Hello, {name}!")
    return f"Hello, {name}!"


__all__ = [
    "process_video_task",
    "execute_single_agent_task",
    "send_webhook_task",
    "cleanup_old_tasks_task",
    "hello_world",
]
