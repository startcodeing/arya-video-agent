"""Unit tests for AgentContext."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.core.context import AgentContext
from app.entities.task import Task, TaskStatus
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.fixture
def mock_db_session():
    """Create a mock database session."""
    session = AsyncMock(spec=AsyncSession)
    return session


@pytest.fixture
def sample_task():
    """Create a sample task."""
    return Task(
        id="test-task-123",
        topic="Test video topic",
        status=TaskStatus.PENDING,
        style="cinematic"
    )


class TestAgentContext:
    """Test suite for AgentContext."""

    def test_initialization(self, mock_db_session):
        """Test context initialization."""
        context = AgentContext(db=mock_db_session, task_id="test-task-123")

        assert context.db == mock_db_session
        assert context.task_id == "test-task-123"
        assert context._shared_data == {}
        assert context._cache is not None
        assert context._storage is not None

    @pytest.mark.asyncio
    async def test_get_task(self, mock_db_session, sample_task):
        """Test getting task from database."""
        # Mock the database query
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = sample_task
        mock_db_session.execute.return_value = mock_result

        context = AgentContext(db=mock_db_session, task_id=sample_task.id)

        task = await context.get_task()

        assert task.id == sample_task.id
        assert task.topic == sample_task.topic
        assert task.status == sample_task.status

    @pytest.mark.asyncio
    async def test_get_task_not_found(self, mock_db_session):
        """Test getting task that doesn't exist."""
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db_session.execute.return_value = mock_result

        context = AgentContext(db=mock_db_session, task_id="nonexistent-task")

        task = await context.get_task()

        assert task is None

    @pytest.mark.asyncio
    async def test_update_task_status(self, mock_db_session):
        """Test updating task status."""
        mock_result = AsyncMock()
        mock_task = Task(
            id="test-task-123",
            topic="Test",
            status=TaskStatus.PENDING
        )
        mock_result.scalar_one_or_none.return_value = mock_task
        mock_db_session.execute.return_value = mock_result

        context = AgentContext(db=mock_db_session, task_id="test-task-123")

        await context.update_task_status(
            status=TaskStatus.STORY_GENERATION,
            message="Story generation started"
        )

        assert mock_task.status == TaskStatus.STORY_GENERATION
        mock_db_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_set_shared_data(self, mock_db_session):
        """Test setting shared data."""
        context = AgentContext(db=mock_db_session, task_id="test-task-123")

        context.set("script", {"scenes": ["scene1", "scene2"]})
        context.set("style", "cinematic")

        assert context.get("script") == {"scenes": ["scene1", "scene2"]}
        assert context.get("style") == "cinematic"

    @pytest.mark.asyncio
    async def test_get_shared_data_default(self, mock_db_session):
        """Test getting shared data with default value."""
        context = AgentContext(db=mock_db_session, task_id="test-task-123")

        # Get non-existent key with default
        value = context.get("nonexistent", default="default_value")

        assert value == "default_value"

    @pytest.mark.asyncio
    async def test_has_shared_data(self, mock_db_session):
        """Test checking if shared data exists."""
        context = AgentContext(db=mock_db_session, task_id="test-task-123")

        assert context.has("key1") is False

        context.set("key1", "value1")
        assert context.has("key1") is True

    @pytest.mark.asyncio
    async def test_delete_shared_data(self, mock_db_session):
        """Test deleting shared data."""
        context = AgentContext(db=mock_db_session, task_id="test-task-123")

        context.set("temp", "value")
        assert context.has("temp") is True

        context.delete("temp")
        assert context.has("temp") is False

    @pytest.mark.asyncio
    async def test_clear_shared_data(self, mock_db_session):
        """Test clearing all shared data."""
        context = AgentContext(db=mock_db_session, task_id="test-task-123")

        context.set("key1", "value1")
        context.set("key2", "value2")
        assert len(context._shared_data) == 2

        context.clear()
        assert len(context._shared_data) == 0

    @pytest.mark.asyncio
    async def test_cache_operations(self, mock_db_session):
        """Test cache get/set operations."""
        context = AgentContext(db=mock_db_session, task_id="test-task-123")

        # Mock cache service
        context._cache.get = AsyncMock(return_value=None)
        context._cache.set = AsyncMock()

        # Test cache set
        await context.cache_set("test_key", {"data": "test"}, ttl=3600)
        context._cache.set.assert_called_once()

        # Test cache get
        await context.cache_get("test_key")
        context._cache.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_cache_delete(self, mock_db_session):
        """Test cache delete operation."""
        context = AgentContext(db=mock_db_session, task_id="test-task-123")

        context._cache.delete = AsyncMock()

        await context.cache_delete("test_key")
        context._cache.delete.assert_called_once_with("test_key")

    @pytest.mark.asyncio
    async def test_save_script(self, mock_db_session):
        """Test saving script to database."""
        from app.entities.script import Script

        mock_result = AsyncMock()
        mock_task = Task(
            id="test-task-123",
            topic="Test",
            status=TaskStatus.STORY_GENERATION
        )
        mock_result.scalar_one_or_none.return_value = mock_task
        mock_db_session.execute.return_value = mock_result

        context = AgentContext(db=mock_db_session, task_id="test-task-123")

        script_data = {
            "title": "Test Script",
            "scenes": [{"text": "Scene 1"}]
        }

        script = await context.save_script(script_data)

        assert isinstance(script, Script)
        assert script.title == "Test Script"
        mock_db_session.add.assert_called()
        mock_db_session.commit.assert_called()
        mock_db_session.refresh.assert_called()

    @pytest.mark.asyncio
    async def test_get_script(self, mock_db_session):
        """Test getting script from database."""
        from app.entities.script import Script

        mock_result = AsyncMock()
        mock_script = Script(
            id="script-123",
            task_id="test-task-123",
            title="Test Script",
            content='{"scenes": []}'
        )
        mock_result.scalar_one_or_none.return_value = mock_script
        mock_db_session.execute.return_value = mock_result

        context = AgentContext(db=mock_db_session, task_id="test-task-123")

        script = await context.get_script()

        assert script is not None
        assert script.id == "script-123"

    @pytest.mark.asyncio
    async def test_save_storyboard(self, mock_db_session):
        """Test saving storyboard to database."""
        from app.entities.storyboard import Storyboard

        mock_result = AsyncMock()
        mock_task = Task(
            id="test-task-123",
            topic="Test",
            status=TaskStatus.STORYBOARD_BREAKDOWN
        )
        mock_result.scalar_one_or_none.return_value = mock_task
        mock_db_session.execute.return_value = mock_result

        context = AgentContext(db=mock_db_session, task_id="test-task-123")

        storyboard_data = {
            "scenes": [
                {
                    "scene_number": 1,
                    "description": "Test scene",
                    "duration": 5
                }
            ]
        }

        storyboard = await context.save_storyboard(storyboard_data)

        assert isinstance(storyboard, Storyboard)
        mock_db_session.add.assert_called()
        mock_db_session.commit.assert_called()
        mock_db_session.refresh.assert_called()

    @pytest.mark.asyncio
    async def test_get_storyboard(self, mock_db_session):
        """Test getting storyboard from database."""
        from app.entities.storyboard import Storyboard

        mock_result = AsyncMock()
        mock_storyboard = Storyboard(
            id="storyboard-123",
            task_id="test-task-123",
            scene_count=3,
            scenes='[]'
        )
        mock_result.scalar_one_or_none.return_value = mock_storyboard
        mock_db_session.execute.return_value = mock_result

        context = AgentContext(db=mock_db_session, task_id="test-task-123")

        storyboard = await context.get_storyboard()

        assert storyboard is not None
        assert storyboard.id == "storyboard-123"

    @pytest.mark.asyncio
    async def test_storage_upload(self, mock_db_session):
        """Test uploading file via storage service."""
        context = AgentContext(db=mock_db_session, task_id="test-task-123")

        context._storage.upload = AsyncMock(return_value="https://storage.test/file.mp4")

        url = await context.storage_upload(
            file_path="videos/test.mp4",
            content=b"fake video content"
        )

        assert url == "https://storage.test/file.mp4"
        context._storage.upload.assert_called_once()

    @pytest.mark.asyncio
    async def test_publish_event(self, mock_db_session):
        """Test publishing event."""
        context = AgentContext(db=mock_db_session, task_id="test-task-123")

        # Mock logger
        with patch.object(context._logger, 'info') as mock_log:
            await context.publish_event(
                event_type="task.status_changed",
                data={"status": "processing"}
            )

            mock_log.assert_called_once()
            args = mock_log.call_args[0]
            assert "task.status_changed" in args[0]

    @pytest.mark.asyncio
    async def test_get_all_data(self, mock_db_session):
        """Test getting all shared data."""
        context = AgentContext(db=mock_db_session, task_id="test-task-123")

        context.set("key1", "value1")
        context.set("key2", {"nested": "data"})

        all_data = context.get_all()

        assert len(all_data) == 2
        assert all_data["key1"] == "value1"
        assert all_data["key2"] == {"nested": "data"}


__all__ = ["TestAgentContext"]
