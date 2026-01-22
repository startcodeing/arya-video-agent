"""Unit tests for Celery configuration."""

from unittest.mock import MagicMock, patch

import pytest

from app.scheduler.celery_app import celery_app


def test_celery_app_creation():
    """Test that Celery app is created with correct configuration."""
    assert celery_app.main == "video_agent"
    assert celery_app.conf.task_serializer == "json"
    assert celery_app.conf.accept_content == ["json"]
    assert celery_app.conf.result_serializer == "json"


def test_celery_broker_config():
    """Test Celery broker configuration."""
    from app.config import settings

    assert celery_app.conf.broker_url == settings.CELERY_BROKER_URL
    assert celery_app.conf.result_backend == settings.CELERY_RESULT_BACKEND


def test_celery_task_time_limits():
    """Test Celery task time limits."""
    from app.config import settings

    assert celery_app.conf.task_soft_time_limit == settings.CELERY_TASK_SOFT_TIME_LIMIT
    assert celery_app.conf.task_time_limit == settings.CELERY_TASK_TIME_LIMIT


def test_celery_timezone():
    """Test Celery timezone configuration."""
    assert celery_app.conf.timezone == "UTC"
    assert celery_app.conf.enable_utc is True


def test_celery_result_expires():
    """Test Celery result expiration."""
    assert celery_app.conf.result_expires == 3600


def test_celery_worker_settings():
    """Test Celery worker configuration."""
    assert celery_app.conf.worker_prefetch_multiplier == 1
    assert celery_app.conf.worker_max_tasks_per_child == 50


def test_celery_task_queues():
    """Test Celery task queue configuration."""
    queues = celery_app.conf.task_queues
    assert len(queues) == 2

    queue_names = [q.name for q in queues]
    assert "default" in queue_names
    assert "video_generation" in queue_names


def test_celery_task_default_queue():
    """Test Celery default queue configuration."""
    assert celery_app.conf.task_default_queue == "default"
    assert celery_app.conf.task_default_routing_key == "default"


def test_celery_task_routing():
    """Test Celery task routing configuration."""
    task_routes = celery_app.conf.task_routes
    assert "app.scheduler.tasks.video_generation_task" in task_routes

    video_route = task_routes["app.scheduler.tasks.video_generation_task"]
    assert video_route["queue"] == "video_generation"


def test_celery_compression():
    """Test Celery compression settings."""
    assert celery_app.conf.result_compression == "gzip"
    assert celery_app.conf.task_compression == "gzip"


def test_celery_task_decorator():
    """Test that Celery tasks can be decorated."""
    from app.scheduler.tasks import hello_world

    # Check that the task is registered
    assert "app.scheduler.tasks.hello_world" in celery_app.tasks
    assert celery_app.tasks["app.scheduler.tasks.hello_world"].name == "app.scheduler.tasks.hello_world"


def test_celery_task_signature():
    """Test that Celery task has correct signature."""
    from app.scheduler.tasks import hello_world

    # Check that the task is callable
    assert callable(hello_world)
    assert hello_world.name == "app.scheduler.tasks.hello_world"


def test_celery_autodiscovery():
    """Test that Celery autodiscovers tasks."""
    # Check that tasks from app.scheduler are discovered
    assert "app.scheduler.tasks.hello_world" in celery_app.tasks
    assert "app.scheduler.tasks.process_video_generation" in celery_app.tasks
