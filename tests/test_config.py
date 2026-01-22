"""Unit tests for configuration."""

import os
import pytest
from pydantic import ValidationError

from app.config import Settings


def test_default_settings():
    """Test default settings values."""
    # Create settings with minimal required fields
    settings = Settings(
        OPENAI_API_KEY="test-key",
        SECRET_KEY="test-secret",
        JWT_SECRET_KEY="test-jwt-secret",
    )

    assert settings.APP_NAME == "Video Agent API"
    assert settings.APP_VERSION == "1.0.0"
    assert settings.DEBUG is False
    assert settings.ENV == "production"
    assert settings.HOST == "0.0.0.0"
    assert settings.PORT == 8000


def test_database_url_default():
    """Test default database URL."""
    settings = Settings(
        OPENAI_API_KEY="test-key",
        SECRET_KEY="test-secret",
        JWT_SECRET_KEY="test-jwt-secret",
    )

    assert "postgresql+asyncpg://" in settings.DATABASE_URL
    assert settings.DB_POOL_SIZE == 20
    assert settings.DB_MAX_OVERFLOW == 10


def test_redis_url_default():
    """Test default Redis URL."""
    settings = Settings(
        OPENAI_API_KEY="test-key",
        SECRET_KEY="test-secret",
        JWT_SECRET_KEY="test-jwt-secret",
    )

    assert settings.REDIS_URL == "redis://localhost:6379/0"
    assert settings.REDIS_CACHE_TTL == 3600


def test_celery_configuration():
    """Test Celery configuration."""
    settings = Settings(
        OPENAI_API_KEY="test-key",
        SECRET_KEY="test-secret",
        JWT_SECRET_KEY="test-jwt-secret",
    )

    assert settings.CELERY_BROKER_URL == "redis://localhost:6379/0"
    assert settings.CELERY_RESULT_BACKEND == "redis://localhost:6379/1"
    assert settings.CELERY_TASK_SOFT_TIME_LIMIT == 600
    assert settings.CELERY_TASK_TIME_LIMIT == 660


def test_model_settings():
    """Test model configuration."""
    settings = Settings(
        OPENAI_API_KEY="test-key",
        SECRET_KEY="test-secret",
        JWT_SECRET_KEY="test-jwt-secret",
    )

    assert settings.DEFAULT_LLM_MODEL == "gpt-4"
    assert settings.DEFAULT_IMAGE_MODEL == "dall-e-3"
    assert settings.DEFAULT_VIDEO_MODEL == "runway-gen3"


def test_storage_settings():
    """Test storage configuration."""
    settings = Settings(
        OPENAI_API_KEY="test-key",
        SECRET_KEY="test-secret",
        JWT_SECRET_KEY="test-jwt-secret",
    )

    assert settings.STORAGE_PROVIDER == "local"
    assert settings.LOCAL_STORAGE_PATH == "./storage"
    assert settings.MAX_UPLOAD_SIZE == 100 * 1024 * 1024


def test_task_settings():
    """Test task configuration."""
    settings = Settings(
        OPENAI_API_KEY="test-key",
        SECRET_KEY="test-secret",
        JWT_SECRET_KEY="test-jwt-secret",
    )

    assert settings.MAX_RETRY_TIMES == 3
    assert settings.TASK_TIMEOUT == 1800
    assert settings.MAX_CONCURRENT_TASKS_PER_USER == 5
    assert settings.MAX_CONCURRENT_GENERATIONS == 5


def test_log_settings():
    """Test logging configuration."""
    settings = Settings(
        OPENAI_API_KEY="test-key",
        SECRET_KEY="test-secret",
        JWT_SECRET_KEY="test-jwt-secret",
    )

    assert settings.LOG_LEVEL == "INFO"
    assert settings.LOG_FILE == "./logs/app.log"
    assert settings.LOG_ROTATION == "10 MB"
    assert settings.LOG_RETENTION == "30 days"


def test_environment_override():
    """Test environment variable override."""
    # Set environment variable
    os.environ["DEBUG"] = "True"
    os.environ["OPENAI_API_KEY"] = "env-key"

    try:
        settings = Settings(
            SECRET_KEY="test-secret",
            JWT_SECRET_KEY="test-jwt-secret",
        )

        assert settings.DEBUG is True
        assert settings.OPENAI_API_KEY == "env-key"
    finally:
        # Clean up
        del os.environ["DEBUG"]
        del os.environ["OPENAI_API_KEY"]


def test_ffmpeg_settings():
    """Test FFmpeg configuration."""
    settings = Settings(
        OPENAI_API_KEY="test-key",
        SECRET_KEY="test-secret",
        JWT_SECRET_KEY="test-jwt-secret",
    )

    assert settings.FFMPEG_PATH == "ffmpeg"
    assert settings.OUTPUT_VIDEO_CODEC == "libx264"
    assert settings.OUTPUT_AUDIO_CODEC == "aac"
    assert settings.OUTPUT_FPS == 30
    assert settings.OUTPUT_RESOLUTION == "1920:1080"


def test_security_settings():
    """Test security configuration."""
    settings = Settings(
        OPENAI_API_KEY="test-key",
        SECRET_KEY="my-secret-key",
        JWT_SECRET_KEY="my-jwt-secret",
    )

    assert settings.SECRET_KEY == "my-secret-key"
    assert settings.JWT_SECRET_KEY == "my-jwt-secret"
    assert settings.JWT_ALGORITHM == "HS256"
    assert settings.JWT_EXPIRATION_HOURS == 24
