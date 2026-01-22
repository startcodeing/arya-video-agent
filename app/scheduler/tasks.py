"""Celery task definitions."""

from celery import shared_task
from app.utils.logger import get_logger

logger = get_logger(__name__)


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


@shared_task(name="app.scheduler.tasks.process_video_generation")
def process_video_generation(task_id: str) -> dict:
    """
    Process video generation task.

    This is a placeholder for the actual video generation logic
    that will be implemented in later weeks.

    Args:
        task_id: Task ID

    Returns:
        Processing result
    """
    logger.info(f"Processing video generation for task: {task_id}")
    # TODO: Implement actual video generation logic
    return {"task_id": task_id, "status": "completed"}


__all__ = ["hello_world", "process_video_generation"]
