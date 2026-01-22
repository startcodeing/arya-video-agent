"""Health check endpoints."""

from fastapi import APIRouter
from pydantic import BaseModel

from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter()


class HealthResponse(BaseModel):
    """Health check response model."""

    status: str
    app_name: str
    version: str
    environment: str


class DetailedHealthResponse(HealthResponse):
    """Detailed health check response model."""

    database_status: str
    redis_status: str


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Basic health check endpoint.

    Returns the current health status of the application.
    """
    return HealthResponse(
        status="healthy",
        app_name=settings.APP_NAME,
        version=settings.APP_VERSION,
        environment=settings.ENV,
    )


@router.get("/health/detailed", response_model=DetailedHealthResponse)
async def detailed_health_check():
    """
    Detailed health check endpoint.

    Returns detailed health status including database and Redis connectivity.
    """
    # TODO: Implement actual database and Redis checks
    return DetailedHealthResponse(
        status="healthy",
        app_name=settings.APP_NAME,
        version=settings.APP_VERSION,
        environment=settings.ENV,
        database_status="not_connected",  # Will be updated when DB is configured
        redis_status="not_connected",  # Will be updated when Redis is configured
    )


@router.get("/health/ready")
async def readiness_check():
    """
    Readiness check endpoint.

    Indicates whether the application is ready to handle requests.
    """
    # TODO: Implement actual readiness checks
    return {"ready": True}


@router.get("/health/live")
async def liveness_check():
    """
    Liveness check endpoint.

    Indicates whether the application is running.
    """
    return {"alive": True}
