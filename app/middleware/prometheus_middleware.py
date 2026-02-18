"""Prometheus metrics middleware for FastAPI."""

import time
from typing import Callable
from prometheus_client import Counter, Histogram

from app.services.prometheus_metrics import metrics_service

# HTTP request metrics
http_requests_total = metrics_service.http_requests_total
http_request_duration_seconds = metrics_service.http_request_duration_seconds


class PrometheusMiddleware:
    """
    Prometheus metrics middleware for FastAPI.

    Automatically tracks:
    - HTTP request counts (by method, endpoint, status)
    - HTTP request latency (by method, endpoint)
    - HTTP error counts (by method, endpoint, exception type)
    """

    def __init__(self, app):
        """
        Initialize Prometheus middleware.

        Args:
            app: FastAPI application
        """
        self.app = app

    async def dispatch(self, request, call_next):
        """
        Middleware entry point.

        Args:
            request: FastAPI request
            call_next: Next callable in middleware chain

        Returns:
            Response from next middleware
        """
        start_time = time.time()

        try:
            # Call next middleware
            response = await call_next(request)

            # Calculate request duration
            duration = time.time() - start_time

            # Get request method and path
            method = request.method.lower()
            path = request.url.path

            # Clean path (remove query parameters)
            if '?' in path:
                path = path.split('?')[0]

            # Get status code
            status_code = response.status_code

            # Track metrics
            metrics_service.track_http_request(
                method=method,
                endpoint=path,
                status_code=status_code,
                duration=duration
            )

            return response

        except Exception as e:
            # Calculate request duration
            duration = time.time() - start_time

            # Get request method and path
            method = request.method.lower()
            path = request.url.path

            # Clean path
            if '?' in path:
                path = path.split('?')[0]

            # Track error metrics
            metrics_service.track_http_request(
                method=method,
                endpoint=path,
                status_code=500,  # Internal server error
                duration=duration
            )

            # Re-raise exception
            raise


def setup_prometheus_middleware(app):
    """
    Setup Prometheus metrics middleware for FastAPI.

    Args:
        app: FastAPI application
    """
    middleware = PrometheusMiddleware(app)

    # Add middleware to FastAPI
    app.add_middleware(PrometheusMiddleware, middleware.dispatch)

    # Expose metrics service for use in other parts of the application
    app.state.metrics_service = metrics_service

    return app
