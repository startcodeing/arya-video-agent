"""Prometheus configuration for metrics collection."""

from prometheus_client import Counter, Histogram, Gauge, Info, CollectorRegistry
from prometheus_fastapi_instrumentator import Instrumentator
from app.services.prometheus_metrics import PrometheusMetricsService

# Create default registry
REGISTRY = CollectorRegistry()

# Create metrics service
metrics_service = PrometheusMetricsService(registry=REGISTRY)

# Create FastAPI instrumentator
instrumentator = Instrumentator(
    should_group_status_codes=False,
    should_ignore_untemplated=True,
    should_instrument_requests_inprogress=True,
    excluded_handlers=["/metrics", "/health"],
    env_var_name="ENVIRONMENT",
    in_str_name="release",
    in_str_name="production",
)

__all__ = [
    "REGISTRY",
    "metrics_service",
    "instrumentator",
]
