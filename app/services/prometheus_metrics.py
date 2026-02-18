"""Prometheus metrics collection and monitoring."""

import time
from typing import Dict, Any, Optional, List
from datetime import datetime

from prometheus_client import Counter, Histogram, Gauge, Info, CollectorRegistry
from prometheus_client.core import CollectorRegistry

from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


class PrometheusMetricsService:
    """
    Prometheus metrics service for application monitoring.

    Features:
    - Request counter (for API endpoints)
    - Request latency histogram
    - Error counter
    - Active tasks gauge
    - Cache metrics
    - Database metrics
    - System resource metrics
    - Custom metrics
    """

    def __init__(self, registry: Optional[CollectorRegistry] = None):
        """
        Initialize Prometheus metrics service.

        Args:
            registry: Collector registry (default: REGISTRY)
        """
        self.registry = registry or REGISTRY

        # Request metrics
        self.http_requests_total = Counter(
            'http_requests_total',
            'Total HTTP requests',
            ['method', 'endpoint', 'status'],
            registry=self.registry
        )

        self.http_request_duration_seconds = Histogram(
            'http_request_duration_seconds',
            'HTTP request latencies in seconds',
            ['method', 'endpoint'],
            registry=self.registry
        )

        # Error metrics
        self.http_errors_total = Counter(
            'http_errors_total',
            'Total HTTP errors',
            ['method', 'endpoint', 'exception_type'],
            registry=self.registry
        )

        # Task metrics
        self.tasks_active = Gauge(
            'tasks_active',
            'Number of active tasks',
            ['status'],
            registry=self.registry
        )

        self.tasks_total = Counter(
            'tasks_total',
            'Total tasks processed',
            ['status'],
            registry=self.registry
        )

        self.task_duration_seconds = Histogram(
            'task_duration_seconds',
            'Task processing duration in seconds',
            ['task_type', 'agent'],
            registry=self.registry
        )

        # Agent metrics
        self.agent_requests_total = Counter(
            'agent_requests_total',
            'Total agent requests',
            ['agent_name', 'model', 'status'],
            registry=self.registry
        )

        self.agent_request_duration_seconds = Histogram(
            'agent_request_duration_seconds',
            'Agent request duration in seconds',
            ['agent_name', 'model'],
            registry=self.registry
        )

        # Database metrics
        self.db_queries_total = Counter(
            'db_queries_total',
            'Total database queries',
            ['table', 'operation', 'status'],
            registry=self.registry
        )

        self.db_query_duration_seconds = Histogram(
            'db_query_duration_seconds',
            'Database query duration in seconds',
            ['table', 'operation'],
            registry=self.registry
        )

        self.db_connections_active = Gauge(
            'db_connections_active',
            'Number of active database connections',
            registry=self.registry
        )

        # Cache metrics
        self.cache_requests_total = Counter(
            'cache_requests_total',
            'Total cache requests',
            ['namespace', 'operation', 'status'],
            registry=self.registry
        )

        self.cache_hits_total = Counter(
            'cache_hits_total',
            'Total cache hits',
            ['namespace'],
            registry=self.registry
        )

        self.cache_misses_total = Counter(
            'cache_misses_total',
            'Total cache misses',
            ['namespace'],
            registry=self.registry
        )

        self.cache_hit_rate = Gauge(
            'cache_hit_rate',
            'Cache hit rate (0.0 to 1.0)',
            ['namespace'],
            registry=self.registry
        )

        self.cache_size_bytes = Gauge(
            'cache_size_bytes',
            'Cache size in bytes',
            ['namespace'],
            registry=self.registry
        )

        # System resource metrics
        self.cpu_usage_percent = Gauge(
            'cpu_usage_percent',
            'CPU usage percentage',
            registry=self.registry
        )

        self.memory_usage_bytes = Gauge(
            'memory_usage_bytes',
            'Memory usage in bytes',
            registry=self.registry
        )

        self.disk_usage_bytes = Gauge(
            'disk_usage_bytes',
            'Disk usage in bytes',
            ['mount_point'],
            registry=self.registry
        )

        # Queue metrics
        self.queue_length = Gauge(
            'queue_length',
            'Queue length',
            ['queue_name', 'status'],
            registry=self.registry
        )

        self.queue_messages_processed_total = Counter(
            'queue_messages_processed_total',
            'Total queue messages processed',
            ['queue_name', 'status'],
            registry=self.registry
        )

        logger.info("Prometheus metrics service initialized")

    def track_http_request(
        self,
        method: str,
        endpoint: str,
        status_code: int,
        duration: float
    ) -> None:
        """
        Track HTTP request metrics.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            status_code: HTTP status code
            duration: Request duration in seconds
        """
        try:
            # Increment request counter
            self.http_requests_total.labels(
                method=method,
                endpoint=endpoint,
                status=str(status_code)
            ).inc()

            # Observe request latency
            self.http_request_duration_seconds.labels(
                method=method,
                endpoint=endpoint
            ).observe(duration)

            # If status code is error (>= 400), increment error counter
            if status_code >= 400:
                self.http_errors_total.labels(
                    method=method,
                    endpoint=endpoint,
                    exception_type='http_error'
                ).inc()

        except Exception as e:
            logger.error(f"Error tracking HTTP request: {str(e)}")

    def track_task_created(
        self,
        task_type: str,
        agent: str,
        status: str
    ) -> None:
        """
        Track task creation metrics.

        Args:
            task_type: Task type (style_generation, story_generation, etc.)
            agent: Agent name
            status: Task status
        """
        try:
            # Increment task counter
            self.tasks_total.labels(status=status).inc()
            self.tasks_active.labels(status=status).inc()

        except Exception as e:
            logger.error(f"Error tracking task creation: {str(e)}")

    def track_task_completed(
        self,
        task_type: str,
        agent: str,
        status: str,
        duration: float
    ) -> None:
        """
        Track task completion metrics.

        Args:
            task_type: Task type
            agent: Agent name
            status: Task status
            duration: Task duration in seconds
        """
        try:
            # Increment task counter
            self.tasks_total.labels(status=status).inc()
            # Decrement active task counter
            self.tasks_active.labels(status=status).dec()

            # Observe task duration
            self.task_duration_seconds.labels(
                task_type=task_type,
                agent=agent
            ).observe(duration)

        except Exception as e:
            logger.error(f"Error tracking task completion: {str(e)}")

    def track_agent_request(
        self,
        agent_name: str,
        model: str,
        status: str,
        duration: float
    ) -> None:
        """
        Track agent request metrics.

        Args:
            agent_name: Agent name
            model: Model name
            status: Request status
            duration: Request duration in seconds
        """
        try:
            # Increment agent request counter
            self.agent_requests_total.labels(
                agent_name=agent_name,
                model=model,
                status=status
            ).inc()

            # Observe request latency
            self.agent_request_duration_seconds.labels(
                agent_name=agent_name,
                model=model
            ).observe(duration)

        except Exception as e:
            logger.error(f"Error tracking agent request: {str(e)}")

    def track_db_query(
        self,
        table: str,
        operation: str,
        status: str,
        duration: float
    ) -> None:
        """
        Track database query metrics.

        Args:
            table: Table name
            operation: Query operation (SELECT, INSERT, UPDATE, DELETE)
            status: Query status (success, error)
            duration: Query duration in seconds
        """
        try:
            # Increment query counter
            self.db_queries_total.labels(
                table=table,
                operation=operation,
                status=status
            ).inc()

            # Observe query latency
            self.db_query_duration_seconds.labels(
                table=table,
                operation=operation
            ).observe(duration)

        except Exception as e:
            logger.error(f"Error tracking DB query: {str(e)}")

    def set_db_connections_active(self, count: int) -> None:
        """
        Set active database connections count.

        Args:
            count: Number of active connections
        """
        try:
            self.db_connections_active.set(count)
        except Exception as e:
            logger.error(f"Error setting DB connections count: {str(e)}")

    def track_cache_request(
        self,
        namespace: str,
        operation: str,
        status: str
    ) -> None:
        """
        Track cache request metrics.

        Args:
            namespace: Cache namespace (tasks, conversations, etc.)
            operation: Cache operation (get, set, delete)
            status: Request status (hit, miss, error)
        """
        try:
            # Increment cache request counter
            self.cache_requests_total.labels(
                namespace=namespace,
                operation=operation,
                status=status
            ).inc()

            # If cache hit, increment hit counter
            if status == 'hit':
                self.cache_hits_total.labels(namespace=namespace).inc()
            # If cache miss, increment miss counter
            elif status == 'miss':
                self.cache_misses_total.labels(namespace=namespace).inc()

            # Update hit rate gauge
            hits = self.cache_hits_total.labels(namespace=namespace)._value.get()
            misses = self.cache_misses_total.labels(namespace=namespace)._value.get()
            total = hits + misses

            if total > 0:
                hit_rate = hits / total
                self.cache_hit_rate.labels(namespace=namespace).set(hit_rate)

        except Exception as e:
            logger.error(f"Error tracking cache request: {str(e)}")

    def set_cache_size(self, namespace: str, size_bytes: int) -> None:
        """
        Set cache size in bytes.

        Args:
            namespace: Cache namespace
            size_bytes: Cache size in bytes
        """
        try:
            self.cache_size_bytes.labels(namespace=namespace).set(size_bytes)
        except Exception as e:
            logger.error(f"Error setting cache size: {str(e)}")

    def set_system_metrics(
        self,
        cpu_percent: float,
        memory_bytes: int,
        disk_bytes: Dict[str, int]
    ) -> None:
        """
        Set system resource metrics.

        Args:
            cpu_percent: CPU usage percentage (0-100)
            memory_bytes: Memory usage in bytes
            disk_bytes: Dictionary of mount_point -> disk usage in bytes
        """
        try:
            self.cpu_usage_percent.set(cpu_percent)
            self.memory_usage_bytes.set(memory_bytes)

            for mount_point, usage in disk_bytes.items():
                self.disk_usage_bytes.labels(mount_point=mount_point).set(usage)

        except Exception as e:
            logger.error(f"Error setting system metrics: {str(e)}")

    def set_queue_metrics(
        self,
        queue_name: str,
        length: int,
        status: str = 'pending'
    ) -> None:
        """
        Set queue metrics.

        Args:
            queue_name: Queue name (tasks, notifications, etc.)
            length: Queue length
            status: Queue status (pending, in_progress, failed)
        """
        try:
            self.queue_length.labels(
                queue_name=queue_name,
                status=status
            ).set(length)

        except Exception as e:
            logger.error(f"Error setting queue metrics: {str(e)}")

    def track_queue_message(
        self,
        queue_name: str,
        status: str
    ) -> None:
        """
        Track queue message metrics.

        Args:
            queue_name: Queue name
            status: Message status (processed, failed, rejected)
        """
        try:
            self.queue_messages_processed_total.labels(
                queue_name=queue_name,
                status=status
            ).inc()

        except Exception as e:
            logger.error(f"Error tracking queue message: {str(e)}")

    def get_metrics_text(self) -> str:
        """
        Get all metrics in Prometheus text format.

        Returns:
            Metrics in Prometheus text format
        """
        try:
            from prometheus_client import generate_latest

            output = generate_latest(self.registry)
            return output
        except Exception as e:
            logger.error(f"Error generating metrics text: {str(e)}")
            return ""


# Create default registry instance
REGISTRY = CollectorRegistry()

# Create default metrics service instance
metrics_service = PrometheusMetricsService(registry=REGISTRY)
