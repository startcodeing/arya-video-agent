"""FastAPI Prometheus middleware for metrics collection."""

import time
from typing import Callable
from prometheus_client import Counter, Histogram

from app.services.prometheus_metrics import metrics_service
from app.utils.logger import get_logger

logger = get_logger(__name__)


class PrometheusMiddleware:
    """
    Prometheus middleware for FastAPI metrics collection.

    Automatically tracks:
    - Request counter (method, endpoint, status code)
    - Request latency (method, endpoint)
    - Error counter (method, endpoint, exception type)
    """

    def __init__(self, app, metrics_path: str = "/metrics"):
        """
        Initialize Prometheus middleware.

        Args:
            app: FastAPI application instance
            metrics_path: Path to expose metrics (default: /metrics)
        """
        self.app = app
        self.metrics_path = metrics_path

        # Add metrics endpoint
        @app.get(metrics_path, include_in_schema=False)
        async def metrics_endpoint():
            """Prometheus metrics endpoint."""
            return await metrics_service.get_metrics_text()

        @app.get(metrics_path + "/json", include_in_schema=False)
        async def metrics_json_endpoint():
            """Prometheus metrics endpoint (JSON format)."""
            metrics = await metrics_service.get_cache_metadata()
            return {
                "metrics": metrics,
                "stats": await metrics_service.get_stats(),
            }

        @app.get("/health", include_in_schema=False)
        async def health_endpoint():
            """Health check endpoint with cache stats."""
            from app.services.redis_cache_service import RedisCacheService

            # Check Redis health
            redis_healthy = False
            try:
                redis_service = RedisCacheService()
                redis_healthy = await redis_service.ping()
            except Exception as e:
                logger.error(f"Redis health check failed: {str(e)}")

            return {
                "status": "healthy" if redis_healthy else "degraded",
                "cache": {
                    "status": "healthy" if redis_healthy else "unhealthy",
                "connected": redis_healthy,
                "stats": await metrics_service.get_stats() if redis_healthy else {},
                "metadata": await metrics_service.get_cache_metadata() if redis_healthy else [],
                }
            }

    async def __call__(self, scope, receive: Callable, send: Callable):
        """
        Middleware call for metrics collection.

        Args:
            scope: ASGI scope
            receive: ASGI receive callable
            send: ASGI send callable
        """
        # Start request timer
        start_time = time.perf_counter()

        # Get request method and path
        method = scope["method"]
        path = scope["path"]

        # Extract endpoint from path
        endpoint = self._extract_endpoint(path)

        # Process request
        try:
            # Wait for receive
            await receive()

            # Check if request is for metrics endpoint
            if path.startswith(self.metrics_path) or path == "/health":
                await send()
                return

            # Process request and wait for send
            await send()

            # Record metrics on success
            self._record_request_metrics(method, endpoint, start_time, status_code=200)

        except Exception as exc:
            # Record metrics on error
            self._record_request_metrics(method, endpoint, start_time, status_code=500, exc=exc)

            # Re-raise exception
            raise exc

    def _extract_endpoint(self, path: str) -> str:
        """
        Extract endpoint from request path.

        Args:
            path: Request path

        Returns:
            Endpoint name
        """
        # Remove query parameters
        endpoint = path.split('?')[0]

        # Normalize endpoint
        # Replace path parameters with placeholders
        endpoint = endpoint.replace(r'/\d+', '/{id}')
        endpoint = endpoint.replace(r'/[a-f0-9-]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}', '/{uuid}')
        endpoint = endpoint.replace(r'/[^/]+', '')

        # Remove leading and trailing slashes
        endpoint = endpoint.strip('/')

        return endpoint

    def _record_request_metrics(
        self,
        method: str,
        endpoint: str,
        start_time: float,
        status_code: int,
        exc: Exception = None
    ) -> None:
        """
        Record request metrics.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: Endpoint path
            start_time: Request start time (perf_counter)
            status_code: HTTP status code
            exc: Exception if request failed
        """
        # Calculate request duration
        duration = time.perf_counter() - start_time

        # Track HTTP request
        metrics_service.track_http_request(
            method=method,
            endpoint=endpoint,
            status_code=status_code,
            duration=duration
        )

        # Log slow requests (>1 second)
        if duration > 1.0:
            logger.warning(f"Slow request: {method} {endpoint} took {duration:.3f}s (status={status_code})")

        # Log errors
        if exc:
            logger.error(f"Request error: {method} {endpoint} - {exc}")


def setup_prometheus_middleware(app, metrics_path: str = "/metrics"):
    """
    Setup Prometheus middleware for FastAPI application.

    Args:
        app: FastAPI application instance
        metrics_path: Path to expose metrics (default: /metrics)

    Returns:
        Configured middleware instance
    """
    middleware = PrometheusMiddleware(app, metrics_path=metrics_path)

    # Add middleware to ASGI application
    app.add_middleware(
        PrometheusMiddleware,
        app=app,
    )

    logger.info(f"Prometheus middleware initialized (metrics path: {metrics_path})")

    return middleware
