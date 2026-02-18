"""FastAPI application entry point with Prometheus monitoring."""

import time
from contextlib import asynccontextmanager
from typing import Callable

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.utils.logger import setup_logger, get_logger

# Import Prometheus middleware
from app.middleware.prometheus import setup_prometheus_middleware
from app.services.prometheus_metrics import metrics_service, PrometheusMetricsService

# Setup logger
setup_logger(
    log_file=settings.LOG_FILE,
    log_level=settings.LOG_LEVEL,
    rotation=settings.LOG_ROTATION,
    retention=settings.LOG_RETENTION,
)
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager with Prometheus initialization."""
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"Environment: {settings.ENV}")
    logger.info(f"Debug mode: {settings.DEBUG}")

    # Initialize Prometheus metrics service
    try:
        await metrics_service.initialize()
        logger.info("Prometheus metrics service initialized")
    except Exception as e:
        logger.error(f"Failed to initialize Prometheus metrics service: {str(e)}")

    yield

    # Shutdown logic
    logger.info("Shutting down application...")


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI Video Generation Agent System with Prometheus Monitoring",
    docs_url="/api/docs" if settings.DEBUG else None,
    redoc_url="/api/redoc" if settings.DEBUG else None,
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.DEBUG else ["https://your-domain.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add GZip middleware for compression
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Add Prometheus metrics middleware
try:
    setup_prometheus_middleware(app, metrics_path="/metrics")
    logger.info("Prometheus middleware initialized")
except Exception as e:
    logger.error(f"Failed to setup Prometheus middleware: {str(e)}")


@app.middleware("http")
async def request_tracker(request: Request, call_next: Callable):
    """Track requests and log them."""
    start_time = time.time()

    # Process request
    response = await call_next(request)

    # Calculate duration
    duration = time.time() - start_time

    # Log request
    logger.info(
        f"{request.method} {request.url.path} "
        f"- Status: {response.status_code} "
        f"- Duration: {duration:.3f}s"
    )

    # Add timing header
    response.headers["X-Process-Time"] = str(duration)

    return response


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError
) -> JSONResponse:
    """Handle validation errors."""
    logger.warning(f"Validation error on {request.url.path}: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Validation Error",
            "message": exc.errors(),
            "path": str(request.url.path),
        },
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle global exceptions."""
    logger.error(f"Unhandled exception on {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal Server Error",
            "message": str(exc) if settings.DEBUG else "An error occurred",
            "path": str(request.url.path),
        },
    )


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "environment": settings.ENV,
        "monitoring": "prometheus",
        "metrics": "/metrics",
    }


@app.get("/health")
async def health():
    """Health check endpoint with Prometheus metrics."""
    # Check Prometheus health
    prometheus_health = await metrics_service.health_check()

    return {
        "status": prometheus_health.get("status", "unknown"),
        "environment": settings.ENV,
        "app_name": settings.APP_NAME,
        "app_version": settings.APP_VERSION,
        "monitoring": "prometheus",
        "metrics": prometheus_health.get("metrics", {}),
    }


# Import and register routes
from app.api.routes import health, tasks, websocket, conversation  # noqa: E402
app.include_router(health.router, tags=["Health"])
app.include_router(tasks.router, tags=["Tasks"])
app.include_router(websocket.router, tags=["WebSocket"])
app.include_router(conversation.router, tags=["Conversations"])


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )
