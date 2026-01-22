"""Unit tests for ComposerAgent."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch, mock_open
from app.agents.composer import ComposerAgent
from app.entities.task import Task, TaskStatus


@pytest.fixture
def mock_llm():
    """Create a mock LLM provider."""
    llm = AsyncMock()
    llm.generate.return_value = '''{
        "composition_plan": {
            "total_duration": 30,
            "shot_order": [1, 2, 3],
            "transitions": [
                {"from_shot": 1, "to_shot": 2, "type": "fade", "duration": 0.5},
                {"from_shot": 2, "to_shot": 3, "type": "cut", "duration": 0}
            ],
            "audio_plan": {
                "music": "orchestral",
                "sound_effects": []
            },
            "notes": "Test composition plan"
        },
        "technical_specs": {
            "output_resolution": "1920x1080",
            "fps": 30
        }
    }'''
    return llm


@pytest.fixture
def mock_video_processor():
    """Create a mock video processor."""
    processor = AsyncMock()
    processor.is_available.return_value = True
    processor.concatenate_videos.return_value = "/tmp/output.mp4"
    return processor


@pytest.fixture
def mock_storage():
    """Create a mock storage service."""
    storage = AsyncMock()
    storage.upload.return_value = "https://storage.test/final_video.mp4"
    return storage


@pytest.fixture
def composer_agent(mock_llm, mock_video_processor, mock_storage):
    """Create a ComposerAgent instance with mocked dependencies."""
    agent = ComposerAgent()
    agent._llm = mock_llm
    agent._video_processor = mock_video_processor
    agent._storage = mock_storage
    return agent


@pytest.fixture
def sample_task_with_videos():
    """Create a sample task with generated videos."""
    return Task(
        id="test-task-123",
        topic="A journey through the mountains",
        style="cinematic",
        status=TaskStatus.COMPOSING,
        user_id="user-123",
        options={
            "storyboard": {
                "total_scenes": 1,
                "total_shots": 2,
                "scenes": [
                    {
                        "scene_number": 1,
                        "shot_number": 1,
                        "duration": 5,
                    },
                    {
                        "scene_number": 1,
                        "shot_number": 2,
                        "duration": 3,
                    },
                ],
            },
            "generated_videos": [
                {
                    "success": True,
                    "scene_number": 1,
                    "shot_number": 1,
                    "storage_path": "/path/to/video1.mp4",
                    "duration": 5,
                },
                {
                    "success": True,
                    "scene_number": 1,
                    "shot_number": 2,
                    "storage_path": "/path/to/video2.mp4",
                    "duration": 3,
                },
            ],
        },
    )


class TestComposerAgent:
    """Test suite for ComposerAgent."""

    def test_initialization(self):
        """Test agent initialization."""
        agent = ComposerAgent()

        assert agent.name == "composer_agent"
        assert agent.retry_times == 1
        assert agent.retry_delay == 1.0

    @pytest.mark.asyncio
    async def test_execute_success(
        self,
        composer_agent,
        sample_task_with_videos,
        mock_video_processor,
        mock_storage,
    ):
        """Test successful video composition."""
        # Mock file reading for upload
        with patch("builtins.open", mock_open(read_data=b"fake video data")):
            result = await composer_agent.execute(sample_task_with_videos)

        assert result["status"] == "success"
        assert result["total_clips"] == 2
        assert "output_video_url" in result
        assert "composition_plan" in result

        # Verify processor was called
        mock_video_processor.concatenate_videos.assert_called_once()

        # Verify storage was called
        mock_storage.upload.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_ffmpeg_not_available(
        self,
        composer_agent,
        sample_task_with_videos,
    ):
        """Test execution when FFmpeg is not available."""
        composer_agent._video_processor.is_available.return_value = False

        with pytest.raises(RuntimeError, match="FFmpeg is not available"):
            await composer_agent.execute(sample_task_with_videos)

    @pytest.mark.asyncio
    async def test_execute_no_generated_videos(
        self,
        composer_agent,
        mock_video_processor,
    ):
        """Test execution without generated videos."""
        task = Task(
            id="test-task",
            topic="Test",
            status=TaskStatus.COMPOSING,
            user_id="user-123",
            options={"generated_videos": []},
        )

        with pytest.raises(ValueError, match="No generated videos found"):
            await composer_agent.execute(task)

    @pytest.mark.asyncio
    async def test_execute_all_videos_failed(
        self,
        composer_agent,
        mock_video_processor,
    ):
        """Test execution when all videos failed to generate."""
        task = Task(
            id="test-task",
            topic="Test",
            status=TaskStatus.COMPOSING,
            user_id="user-123",
            options={
                "generated_videos": [
                    {"success": False},
                    {"success": False},
                ],
            },
        )

        with pytest.raises(ValueError, match="No successfully generated videos"):
            await composer_agent.execute(task)

    @pytest.mark.asyncio
    async def test_create_composition_plan(
        self,
        composer_agent,
        mock_llm,
    ):
        """Test creating composition plan."""
        storyboard = {"total_scenes": 1, "total_shots": 2}
        videos = [
            {"scene_number": 1, "shot_number": 1, "duration": 5},
            {"scene_number": 1, "shot_number": 2, "duration": 3},
        ]

        plan = await composer_agent._create_composition_plan(
            storyboard,
            videos,
            Task(
                id="test",
                topic="Test",
                status=TaskStatus.COMPOSING,
                user_id="user-123",
            ),
        )

        assert "total_duration" in plan
        assert "shot_order" in plan
        assert "transitions" in plan

    @pytest.mark.asyncio
    async def test_create_composition_plan_fallback(
        self,
        composer_agent,
        mock_llm,
    ):
        """Test composition plan fallback when LLM fails."""
        mock_llm.generate.side_effect = Exception("LLM error")

        storyboard = {"total_scenes": 1, "total_shots": 2}
        videos = [
            {"scene_number": 1, "shot_number": 1, "duration": 5},
            {"scene_number": 1, "shot_number": 2, "duration": 3},
        ]

        plan = await composer_agent._create_composition_plan(
            storyboard,
            videos,
            Task(
                id="test",
                topic="Test",
                status=TaskStatus.COMPOSING,
                user_id="user-123",
            ),
        )

        # Should return default plan
        assert plan["total_duration"] == 8
        assert plan["shot_order"] == [1, 2]
        assert len(plan["transitions"]) == 1

    @pytest.mark.asyncio
    async def test_compose_videos(
        self,
        composer_agent,
        mock_video_processor,
    ):
        """Test video composition."""
        video_paths = ["/path/to/video1.mp4", "/path/to/video2.mp4"]
        composition_plan = {
            "transitions": [
                {"from_shot": 1, "to_shot": 2, "type": "fade", "duration": 0.5}
            ]
        }

        result = await composer_agent._compose_videos(
            video_paths,
            composition_plan,
            "task-123",
        )

        assert result == "/tmp/output.mp4"
        mock_video_processor.concatenate_videos.assert_called_once()

    @pytest.mark.asyncio
    async def test_upload_final_video(
        self,
        composer_agent,
        mock_storage,
    ):
        """Test uploading final video."""
        # Mock file reading
        with patch("builtins.open", mock_open(read_data=b"fake video data")):
            with patch("os.path.exists", return_value=True):
                url = await composer_agent._upload_final_video("/tmp/output.mp4", "task-123")

        assert url == "https://storage.test/final_video.mp4"
        mock_storage.upload.assert_called_once()

    def test_validate_input_valid(self, composer_agent, sample_task_with_videos):
        """Test input validation with valid input."""
        assert composer_agent.validate_input(sample_task_with_videos) is True

    def test_validate_input_no_task(self, composer_agent):
        """Test input validation with no task."""
        assert composer_agent.validate_input(None) is False

    def test_validate_input_no_videos(self, composer_agent):
        """Test input validation without videos."""
        task = Task(
            id="test-task",
            topic="Test",
            status=TaskStatus.COMPOSING,
            user_id="user-123",
            options={},
        )
        assert composer_agent.validate_input(task) is False

    def test_validate_input_all_failed(self, composer_agent):
        """Test input validation when all videos failed."""
        task = Task(
            id="test-task",
            topic="Test",
            status=TaskStatus.COMPOSING,
            user_id="user-123",
            options={
                "generated_videos": [
                    {"success": False},
                    {"success": False},
                ]
            },
        )
        assert composer_agent.validate_input(task) is False

    @pytest.mark.asyncio
    async def test_cleanup_temp_files(self, composer_agent):
        """Test cleanup of temporary files."""
        with patch("os.path.exists", return_value=True):
            with patch("os.remove") as mock_remove:
                await composer_agent._cleanup_temp_files(["/tmp/file1.mp4", "/tmp/file2.mp4"])

        assert mock_remove.call_count == 2

    @pytest.mark.asyncio
    async def test_before_execute_hook(self, composer_agent, sample_task_with_videos):
        """Test before_execute hook."""
        await composer_agent.before_execute(sample_task_with_videos)

    @pytest.mark.asyncio
    async def test_after_execute_hook(
        self,
        composer_agent,
        sample_task_with_videos,
    ):
        """Test after_execute hook."""
        result = {
            "status": "success",
            "output_video_url": "https://storage.test/video.mp4",
        }
        await composer_agent.after_execute(sample_task_with_videos, result)


__all__ = ["TestComposerAgent"]
