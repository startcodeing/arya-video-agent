"""Unit tests for database entities."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.entities.task import Task, TaskStatus, TaskPriority
from app.entities.script import Script
from app.entities.storyboard import Storyboard
from app.entities.resource import Resource, ResourceType


@pytest.mark.asyncio
async def test_create_task(db_session: AsyncSession):
    """Test creating a task entity."""
    task = Task(
        user_id="test_user",
        topic="A beautiful sunset",
        style="cinematic",
        options={"duration": 30},
        status=TaskStatus.PENDING,
        priority=TaskPriority.NORMAL,
    )

    db_session.add(task)
    await db_session.commit()
    await db_session.refresh(task)

    assert task.id is not None
    assert task.user_id == "test_user"
    assert task.topic == "A beautiful sunset"
    assert task.status == TaskStatus.PENDING


@pytest.mark.asyncio
async def test_task_status_enum():
    """Test task status enum."""
    assert TaskStatus.PENDING == "pending"
    assert TaskStatus.COMPLETED == "completed"
    assert TaskStatus.FAILED == "failed"


@pytest.mark.asyncio
async def test_create_script(db_session: AsyncSession, sample_task: Task):
    """Test creating a script entity."""
    script = Script(
        task_id=sample_task.id,
        title="Test Video",
        synopsis="A test video about sunsets",
        content="Once upon a time...",
        structured_content={"scenes": []},
        style_tags=["cinematic", "dramatic"],
        visual_style="High contrast",
        mood="dramatic",
        total_duration=30,
        scene_count=3,
    )

    db_session.add(script)
    await db_session.commit()
    await db_session.refresh(script)

    assert script.id is not None
    assert script.task_id == sample_task.id
    assert script.title == "Test Video"


@pytest.mark.asyncio
async def test_create_storyboard(db_session: AsyncSession, sample_task: Task, sample_script: Script):
    """Test creating a storyboard entity."""
    storyboard = Storyboard(
        task_id=sample_task.id,
        script_id=sample_script.id,
        sequence_number=1,
        title="Opening Scene",
        description="A beautiful sunset over the ocean",
        dialogue="Welcome to this beautiful journey",
        camera_movement="pan_right",
        shot_type="wide",
        duration=5.0,
        generation_status="pending",
    )

    db_session.add(storyboard)
    await db_session.commit()
    await db_session.refresh(storyboard)

    assert storyboard.id is not None
    assert storyboard.sequence_number == 1
    assert storyboard.duration == 5.0


@pytest.mark.asyncio
async def test_create_resource(db_session: AsyncSession, sample_task: Task):
    """Test creating a resource entity."""
    resource = Resource(
        task_id=sample_task.id,
        resource_type=ResourceType.IMAGE,
        file_name="test_image.png",
        file_path="/storage/test_image.png",
        file_size=1024,
        mime_type="image/png",
        storage_provider="local",
        storage_key="test_image.png",
        public_url="http://localhost/storage/test_image.png",
        width=1920,
        height=1080,
        generation_model="dall-e-3",
    )

    db_session.add(resource)
    await db_session.commit()
    await db_session.refresh(resource)

    assert resource.id is not None
    assert resource.resource_type == ResourceType.IMAGE
    assert resource.width == 1920
    assert resource.height == 1080


@pytest.mark.asyncio
async def test_resource_type_enum():
    """Test resource type enum."""
    assert ResourceType.IMAGE == "image"
    assert ResourceType.VIDEO == "video"
    assert ResourceType.AUDIO == "audio"
    assert ResourceType.THUMBNAIL == "thumbnail"
