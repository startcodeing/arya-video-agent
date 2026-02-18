"""Middleware layer for application."""

from app.middleware.prometheus import PrometheusMiddleware

__all__ = [
    "PrometheusMiddleware",
]
