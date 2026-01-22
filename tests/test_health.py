"""Integration tests for health check endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_root_endpoint(client: AsyncClient):
    """Test root endpoint."""
    response = await client.get("/")
    assert response.status_code == 200

    data = response.json()
    assert "name" in data
    assert "version" in data
    assert "status" in data
    assert data["status"] == "running"


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    """Test basic health check endpoint."""
    response = await client.get("/api/v1/health")
    assert response.status_code == 200

    data = response.json()
    assert "status" in data
    assert "app_name" in data
    assert "version" in data
    assert "environment" in data
    assert data["status"] == "healthy"


@pytest.mark.asyncio
async def test_detailed_health_check(client: AsyncClient):
    """Test detailed health check endpoint."""
    response = await client.get("/api/v1/health/detailed")
    assert response.status_code == 200

    data = response.json()
    assert "status" in data
    assert "app_name" in data
    assert "version" in data
    assert "environment" in data
    assert "database_status" in data
    assert "redis_status" in data


@pytest.mark.asyncio
async def test_readiness_check(client: AsyncClient):
    """Test readiness check endpoint."""
    response = await client.get("/api/v1/health/ready")
    assert response.status_code == 200

    data = response.json()
    assert "ready" in data


@pytest.mark.asyncio
async def test_liveness_check(client: AsyncClient):
    """Test liveness check endpoint."""
    response = await client.get("/api/v1/health/live")
    assert response.status_code == 200

    data = response.json()
    assert "alive" in data
