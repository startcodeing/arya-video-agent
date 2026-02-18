"""Prometheus metrics endpoints for scraping."""

import psutil
import os
from typing import Dict, Any

from fastapi import APIRouter, Request
from prometheus_client import generate_latest

from app.services.prometheus_metrics import metrics_service, REGISTRY
from app.services.redis_cache_service import RedisCacheService
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/metrics", tags=["metrics"])


@router.get("/")
async def get_metrics() -> Dict[str, Any]:
    """
    Get all metrics in Prometheus text format.

    Returns:
        Metrics in Prometheus text format
    """
    try:
        # Generate Prometheus text format
        output = generate_latest(REGISTRY)

        # Return metrics as text/plain
        return {
            "metrics": output
        }

    except Exception as e:
        logger.error(f"Error generating metrics: {str(e)}")
        return {
            "metrics": ""
        }


@router.get("/prometheus")
async def get_metrics_prometheus_format() -> str:
    """
    Get metrics in Prometheus format.

    Returns:
        Metrics in Prometheus text format
    """
    try:
        # Generate Prometheus text format
        output = generate_latest(REGISTRY)

        return output

    except Exception as e:
        logger.error(f"Error generating metrics: {str(e)}")
        return ""


@router.get("/stats")
async def get_cache_stats() -> Dict[str, Any]:
    """
    Get cache statistics.

    Returns:
        Cache statistics dictionary
    """
    try:
        stats = await metrics_service.get_cache_stats()

        # Add system metrics
        system_stats = get_system_stats()

        return {
            "cache_stats": stats,
            "system_stats": system_stats,
        }

    except Exception as e:
        logger.error(f"Error getting cache stats: {str(e)}")
        return {
            "error": str(e)
        }


@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """
    Health check for metrics service.

    Returns:
        Health check result dictionary
    """
    try:
        # Check Redis health
        redis_health = await metrics_service.health_check()

        # Get system stats
        system_stats = get_system_stats()

        # Overall health status
        is_healthy = (
            redis_health.get("status", "unhealthy") == "healthy" and
            system_stats.get("cpu_status", "unknown") != "critical"
        )

        return {
            "status": "healthy" if is_healthy else "unhealthy",
            "is_healthy": is_healthy,
            "redis_health": redis_health,
            "system_health": system_stats,
            "timestamp": psutil.get_boot_time(),
        }

    except Exception as e:
        logger.error(f"Error in health check: {str(e)}")
        return {
            "status": "unhealthy",
            "is_healthy": False,
            "error": str(e),
            "timestamp": psutil.get_boot_time(),
        }


def get_system_stats() -> Dict[str, Any]:
    """
    Get system resource statistics.

    Returns:
        System resource statistics dictionary
    """
    try:
        # CPU usage
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_status = "healthy"
        if cpu_percent > 80:
            cpu_status = "warning"
        if cpu_percent > 90:
            cpu_status = "critical"

        # Memory usage
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        memory_status = "healthy"
        if memory_percent > 80:
            memory_status = "warning"
        if memory_percent > 90:
            memory_status = "critical"

        # Disk usage
        disk_stats = {}
        for mount in psutil.disk_partitions():
            if mount.fstype != '':
                try:
                    disk_usage = psutil.disk_usage(mount.mountpoint)
                    disk_percent = disk_usage.percent
                    disk_status = "healthy"
                    if disk_percent > 80:
                        disk_status = "warning"
                    if disk_percent > 90:
                        disk_status = "critical"

                    disk_stats[mount.mountpoint] = {
                        "total": disk_usage.total,
                        "used": disk_usage.used,
                        "free": disk_usage.free,
                        "percent": disk_percent,
                        "status": disk_status,
                    }
                except Exception as e:
                    logger.warning(f"Error getting disk stats for {mount.mountpoint}: {str(e)}")

        # Network stats
        network_stats = {}
        for interface, addrs in psutil.net_if_addrs().items():
            stats = psutil.net_io_counters(pernic=True).get(interface, {})
            network_stats[interface] = {
                "bytes_sent": stats.bytes_sent,
                "bytes_recv": stats.bytes_recv,
                "packets_sent": stats.packets_sent,
                "packets_recv": stats.packets_recv,
            }

        # Process stats
        process_count = len(psutil.pids())

        # Boot time
        boot_time = psutil.get_boot_time()

        return {
            "cpu": {
                "percent": cpu_percent,
                "status": cpu_status,
                "count": psutil.cpu_count(),
            },
            "memory": {
                "total": memory.total,
                "used": memory.used,
                "free": memory.free,
                "available": memory.available,
                "percent": memory_percent,
                "status": memory_status,
            },
            "disk": disk_stats,
            "network": network_stats,
            "processes": {
                "count": process_count,
            },
            "boot_time": boot_time,
            "system_stats": {
                "cpu_status": cpu_status,
                "memory_status": memory_status,
                "disk_status": "warning" if any(s.get("status") == "critical" for s in disk_stats.values()) else "healthy",
            },
        }

    except Exception as e:
        logger.error(f"Error getting system stats: {str(e)}")
        return {
            "error": str(e),
        }
