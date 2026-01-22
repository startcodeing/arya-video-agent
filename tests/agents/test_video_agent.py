"""Unit tests for VideoAgent."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.agents.video import VideoAgent
from app.entities.task import Task, TaskStatus


@pytest.fixture
def mock_llm():
    """Create a mock LLM provider."""
    llm = AsyncMock()
    llm.generate.return_value = '''{
        "enhanced_prompt": "Slow cinematic pan across mountain landscape",
        "motion_description": "smooth camera movement from left to right",
        "camera_movement": "slow pan",
        "pacing": "slow",
        "key_moments": ["mountains appear at 0s", "clouds move at 2s"]
    }'''
    return llm


@pytest.fixture
def mock_video_model():
    """Create a mock video model."""
    model = AsyncMock()
    model.generate.return_value = {
        "id": "video-gen-123",
        "url": "https://example.com/generated-video.mp4",
        "status": "completed",
    }
    model.generate_from_image.return_value = {
        "id": "video-gen-456",
        "url": "https://example.com/video-from-image.mp4",
        "status": "completed",
    }
    model.get_generation_status.return_value = {
        "id": "video-gen-123",
        "status": "completed",
        "url": "https://example.com/generated-video.mp4",
        "progress": 100,
    }
    model.download_video.return_value = b"fake video data"
    return model


@pytest.fixture
def mock_storage():
    """Create a mock storage service."""
    storage = AsyncMock()
    storage.upload.return_value = "https://storage.test/video.mp4"
    return storage


@pytest.fixture
def video_agent(mock_llm, mock_video_model, mock_storage):
    """Create a VideoAgent instance with mocked dependencies."""
    agent = VideoAgent(max_concurrent=2)
    agent._llm = mock_llm
    agent._video_model = mock_video_model
    agent._storage = mock_storage
    return agent


@pytest.fixture
def sample_task_with_videos():
    """Create a sample task with storyboard and generated images."""
    return Task(
        id="test-task-123",
        topic="A journey through the mountains",
        style="cinematic",
        status=TaskStatus.VIDEO_GENERATION,
        user_id="user-123",
        options={
            "storyboard": {
                "total_scenes": 1,
                "total_shots": 2,
                "scenes": [
                    {
                        "scene_number": 1,
                        "shot_number": 1,
                        "visual_description": "Wide shot of mountains",
                        "duration": 5,
                    },
                    {
                        "scene_number": 1,
                        "shot_number": 2,
                        "visual_description": "Close-up of flowers",
                        "duration": 3,
                    },
                ],
            },
            "generated_images": [
                {
                    "success": True,
                    "scene_number": 1,
                    "shot_number": 1,
                    "url": "https://storage.test/image1.png",
                    "storage_path": "/path/to/image1.png",
                    "prompt": "Enhanced prompt 1",
                },
                {
                    "success": True,
                    "scene_number": 1,
                    "shot_number": 2,
                    "url": "https://storage.test/image2.png",
                    "storage_path": "/path/to/image2.png",
                    "prompt": "Enhanced prompt 2",
                },
            ],
        },
    )


class TestVideoAgent:
    """Test suite for VideoAgent."""

    def test_initialization(self):
        """Test agent initialization."""
        agent = VideoAgent(max_concurrent=3)

        assert agent.name == "video_agent"
        assert agent.max_concurrent == 3
        assert agent.retry_times == 2

    @pytest.mark.asyncio
    async def test_execute_success(
        self,
        video_agent,
        sample_task_with_videos,
        mock_video_model,
        mock_storage,
    ):
        """Test successful video generation."""
        result = await video_agent.execute(sample_task_with_videos)

        assert result["status"] == "success"
        assert result["total_shots"] == 2
        assert result["generated_videos"] == 2
        assert result["failed_videos"] == 0
        assert len(result["videos"]) == 2

        # Verify videos were generated
        assert mock_video_model.generate_from_image.call_count == 2
        assert mock_storage.upload.call_count == 2

    @pytest.mark.asyncio
    async def test_execute_with_failure(
        self,
        video_agent,
        sample_task_with_videos,
        mock_video_model,
    ):
        """Test video generation with some failures."""
        # First succeeds, second fails
        mock_video_model.generate_from_image.side_effect = [
            {"id": "video-1", "url": "https://example.com/video1.mp4"},
            Exception("Generation failed"),
        ]

        result = await video_agent.execute(sample_task_with_videos)

        assert result["status"] == "success"
        assert result["generated_videos"] == 1
        assert result["failed_videos"] == 1

    @pytest.mark.asyncio
    async def test_enhance_prompt(self, video_agent, mock_llm):
        """Test prompt enhancement."""
        result = await video_agent._enhance_prompt(
            "Wide shot of mountains",
            "Mountains with dramatic lighting",
            "cinematic",
            5,
        )

        assert "enhanced_prompt" in result
        assert "motion_description" in result

    @pytest.mark.asyncio
    async def test_enhance_prompt_fallback(self, video_agent, mock_llm):
        """Test prompt enhancement fallback when LLM fails."""
        mock_llm.generate.side_effect = Exception("LLM error")

        result = await video_agent._enhance_prompt(
            "Original description",
            "",
            "cinematic",
            5,
        )

        # Should fall back to original description
        assert result["enhanced_prompt"] == "Original description"

    @pytest.mark.asyncio
    async def test_generate_single_video_with_image(
        self,
        video_agent,
        mock_video_model,
        mock_storage,
    ):
        """Test generating video from image."""
        shot = {
            "scene_number": 1,
            "shot_number": 1,
            "visual_description": "Wide shot of mountains",
            "duration": 5,
        }

        images_dict = {
            (1, 1): {
                "url": "https://storage.test/image1.png",
                "prompt": "Enhanced prompt",
            }
        }

        result = await video_agent._generate_single_video(
            shot,
            images_dict,
            "cinematic",
            "task-123",
            0,
        )

        assert result["success"] is True
        assert result["shot_number"] == 1
        assert "storage_path" in result
        assert "url" in result

        # Verify generate_from_image was called
        mock_video_model.generate_from_image.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_single_video_text_to_video(
        self,
        video_agent,
        mock_video_model,
        mock_storage,
    ):
        """Test generating video without image (text-to-video)."""
        shot = {
            "scene_number": 1,
            "shot_number": 1,
            "visual_description": "Wide shot of mountains",
            "duration": 5,
        }

        images_dict = {}  # No image available

        result = await video_agent._generate_single_video(
            shot,
            images_dict,
            "cinematic",
            "task-123",
            0,
        )

        assert result["success"] is True

        # Verify generate (text-to-video) was called
        mock_video_model.generate.assert_called_once()

    @pytest.mark.asyncio
    async def test_wait_for_video_completion(
        self,
        video_agent,
        mock_video_model,
    ):
        """Test waiting for video completion."""
        mock_video_model.get_generation_status.return_value = {
            "id": "video-123",
            "status": "completed",
            "url": "https://example.com/video.mp4",
        }

        url = await video_agent._wait_for_video_completion("video-123")

        assert url == "https://example.com/video.mp4"

    @pytest.mark.asyncio
    async def test_wait_for_video_completion_timeout(
        self,
        video_agent,
        mock_video_model,
    ):
        """Test timeout when waiting for video completion."""
        # Status never completes
        mock_video_model.get_generation_status.return_value = {
            "id": "video-123",
            "status": "processing",
        }

        with pytest.raises(TimeoutError, match="timed out"):
            await video_agent._wait_for_video_completion(
                "video-123",
                max_wait=2,
                poll_interval=1,
            )

    @pytest.mark.asyncio
    async def test_wait_for_video_completion_failed(
        self,
        video_agent,
        mock_video_model,
    ):
        """Test when video generation fails."""
        mock_video_model.get_generation_status.return_value = {
            "id": "video-123",
            "status": "failed",
            "error": "Generation error",
        }

        with pytest.raises(RuntimeError, match="Generation error"):
            await video_agent._wait_for_video_completion("video-123")

    def test_validate_input_valid(self, video_agent, sample_task_with_videos):
        """Test input validation with valid input."""
        assert video_agent.validate_input(sample_task_with_videos) is True

    def test_validate_input_no_task(self, video_agent):
        """Test input validation with no task."""
        assert video_agent.validate_input(None) is False

    def test_validate_input_no_storyboard(self, video_agent):
        """Test input validation without storyboard."""
        task = Task(
            id="test-task",
            topic="Test",
            status=TaskStatus.VIDEO_GENERATION,
            user_id="user-123",
            options={},
        )
        assert video_agent.validate_input(task) is False

    def test_validate_input_no_generated_videos(self, video_agent):
        """Test input validation without generated videos."""
        task = Task(
            id="test-task",
            topic="Test",
            status=TaskStatus.VIDEO_GENERATION,
            user_id="user-123",
            options={
                "storyboard": {"scenes": [{"scene_number": 1, "shot_number": 1}]},
            },
        )
        assert video_agent.validate_input(task) is False

    @pytest.mark.asyncio
    async def test_before_execute_hook(self, video_agent, sample_task_with_videos):
        """Test before_execute hook."""
        await video_agent.before_execute(sample_task_with_videos)

    @pytest.mark.asyncio
    async def test_after_execute_hook(
        self,
        video_agent,
        sample_task_with_videos,
    ):
        """Test after_execute hook."""
        result = {"status": "success", "generated_videos": 2, "total_shots": 2}
        await video_agent.after_execute(sample_task_with_videos, result)


__all__ = ["TestVideoAgent"]
