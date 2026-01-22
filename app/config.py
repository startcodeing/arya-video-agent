"""Application configuration using Pydantic Settings."""

from typing import Optional, List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="allow"
    )

    # Application Configuration
    APP_NAME: str = "Video Agent API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENV: str = "production"  # development, staging, production

    # Server Configuration
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Database Configuration
    DATABASE_URL: str = "postgresql+asyncpg://user:password@localhost/video_agent"
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 10

    # Redis Configuration
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_CACHE_TTL: int = 3600  # 1 hour

    # Celery Configuration
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/1"
    CELERY_TASK_SOFT_TIME_LIMIT: int = 600  # 10 minutes
    CELERY_TASK_TIME_LIMIT: int = 660  # 11 minutes

    # Model API Configuration
    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    RUNWAY_API_KEY: Optional[str] = None
    STABILITY_API_KEY: Optional[str] = None

    # Model Configuration
    DEFAULT_LLM_MODEL: str = "gpt-4"
    DEFAULT_IMAGE_MODEL: str = "dall-e-3"
    DEFAULT_VIDEO_MODEL: str = "runway-gen3"

    # Storage Configuration
    STORAGE_PROVIDER: str = "local"  # local, oss, s3
    LOCAL_STORAGE_PATH: str = "./storage"
    OSS_ACCESS_KEY_ID: Optional[str] = None
    OSS_ACCESS_KEY_SECRET: Optional[str] = None
    OSS_BUCKET: Optional[str] = None
    OSS_ENDPOINT: Optional[str] = None

    # File Configuration
    MAX_UPLOAD_SIZE: int = 100 * 1024 * 1024  # 100MB
    ALLOWED_VIDEO_FORMATS: List[str] = ["mp4", "webm", "mov"]
    ALLOWED_IMAGE_FORMATS: List[str] = ["jpg", "jpeg", "png", "webp"]

    # FFmpeg Configuration
    FFMPEG_PATH: str = "ffmpeg"
    FFPROBE_PATH: str = "ffprobe"
    OUTPUT_VIDEO_CODEC: str = "libx264"
    OUTPUT_AUDIO_CODEC: str = "aac"
    OUTPUT_VIDEO_BITRATE: str = "5M"
    OUTPUT_AUDIO_BITRATE: str = "192k"
    OUTPUT_FPS: int = 30
    OUTPUT_RESOLUTION: str = "1920:1080"

    # Task Configuration
    MAX_RETRY_TIMES: int = 3
    TASK_TIMEOUT: int = 1800  # 30 minutes
    MAX_CONCURRENT_TASKS_PER_USER: int = 5
    MAX_CONCURRENT_GENERATIONS: int = 5

    # Cost Control
    COST_CURRENCY: str = "USD"
    DEFAULT_DAILY_BUDGET: float = 50.0

    # Webhook Configuration
    WEBHOOK_TIMEOUT: int = 10
    WEBHOOK_MAX_RETRIES: int = 3

    # Log Configuration
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "./logs/app.log"
    LOG_ROTATION: str = "10 MB"
    LOG_RETENTION: str = "30 days"

    # Monitor Configuration
    PROMETHEUS_ENABLED: bool = True
    PROMETHEUS_PORT: int = 9090

    # Security Configuration
    SECRET_KEY: str = "your-secret-key-change-this-in-production"
    JWT_SECRET_KEY: str = "your-jwt-secret-key"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 24


# Global settings instance
settings = Settings()

__all__ = ["Settings", "settings"]
