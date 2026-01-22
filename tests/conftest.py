"""Pytest configuration and fixtures."""

import asyncio
import os
import sys
from pathlib import Path
from typing import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from httpx import AsyncClient

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database.session import init_db, drop_db, close_db
from app.main import app
from app.config import settings
from app.entities.task import Task
from app.entities.script import Script


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def database():
    """Setup database for tests."""
    # Set test database URL if not already set
    if "test" not in settings.DATABASE_URL:
        # For now, we'll use the same database
        # In production, you'd want to use a separate test database
        pass

    # Initialize database
    await init_db()

    yield

    # Cleanup
    await drop_db()
    await close_db()


@pytest_asyncio.fixture
async def client() -> AsyncGenerator:
    """Create HTTP test client."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def sample_task_data() -> dict:
    """Sample task data for testing."""
    return {
        "topic": "A futuristic cityscape with flying cars",
        "style": "futuristic",
        "options": {
            "duration": 60,
            "resolution": "1080p",
            "include_audio": True,
        }
    }


@pytest_asyncio.fixture
async def db_session():
    """Create database session for tests."""
    from app.database.session import AsyncSessionLocal
    from app.entities.task import Task, TaskStatus, TaskPriority
    from app.entities.script import Script

    async with AsyncSessionLocal() as session:
        # Create a sample task
        task = Task(
            user_id="test_user",
            topic="Test task",
            status=TaskStatus.PENDING,
            priority=TaskPriority.NORMAL,
        )
        session.add(task)
        await session.commit()
        await session.refresh(task)

        # Create a sample script
        script = Script(
            task_id=task.id,
            content="Test script content",
            structured_content={"scenes": []},
        )
        session.add(script)
        await session.commit()
        await session.refresh(script)

        # Store task and script for use in tests
        db_session.task = task
        db_session.script = script

        yield session

        # Cleanup
        await session.rollback()


@pytest_asyncio.fixture
async def sample_task(db_session) -> Task:
    """Get sample task for testing."""
    return db_session.task


@pytest_asyncio.fixture
async def sample_script(db_session) -> Script:
    """Get sample script for testing."""
    return db_session.script
