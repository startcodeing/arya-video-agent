"""Celery application configuration."""

from celery import Celery

from app.config import settings

# Create Celery app
celery_app = Celery(
    "video_agent",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

# Celery configuration
celery_app.conf.update(
    # Task settings
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    # Task time limits
    task_soft_time_limit=settings.CELERY_TASK_SOFT_TIME_LIMIT,
    task_time_limit=settings.CELERY_TASK_TIME_LIMIT,
    # Task result settings
    result_expires=3600,  # Results expire after 1 hour
    # Worker settings
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=50,
    # Task routing
    task_routes={
        "app.scheduler.tasks.video_generation_task": {
            "queue": "video_generation",
        },
    },
    # Task queues
    task_queues=[
        {
            "name": "default",
            "routing_key": "default",
        },
        {
            "name": "video_generation",
            "routing_key": "video_generation",
        },
    ],
    # Task default queue
    task_default_queue="default",
    # Task default routing key
    task_default_routing_key="default",
    # Result compression
    result_compression="gzip",
    # Task compression
    task_compression="gzip",
)

# Auto-discover tasks from all scheduler modules
celery_app.autodiscover_tasks(["app.scheduler"])


__all__ = ["celery_app"]
