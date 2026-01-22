"""Unit tests for ImageAgent."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.agents.image import ImageAgent
from app.entities.task import Task, TaskStatus


@pytest.fixture
def mock_llm():
    """Create a mock LLM provider."""
    llm = AsyncMock()
    llm.generate.return_value = '''{
        "enhanced_prompt": "Cinematic wide shot of majestic mountains at sunrise",
        "negative_prompt": "blurry, low quality",
        "style_keywords": ["cinematic", "dramatic"],
        "quality_modifiers": ["high quality", "detailed"],
        "key_elements": ["mountains", "sunrise", "clouds"]
    }'''
    return llm


@pytest.fixture
def mock_image_model():
    """Create a mock image model."""
    model = AsyncMock()
    model.generate.return_value = {
        "url": "https://example.com/generated-image.png",
        "revised_prompt": "Cinematic mountains",
    }
    model.download_image.return_value = b"fake image data"
    return model


@pytest.fixture
def mock_storage():
    """Create a mock storage service."""
    storage = AsyncMock()
    storage.upload.return_value = "https://storage.test/image.png"
    return storage


@pytest.fixture
def image_agent(mock_llm, mock_image_model, mock_storage):
    """Create an ImageAgent instance with mocked dependencies."""
    agent = ImageAgent(max_concurrent=2)
    agent._llm = mock_llm
    agent._image_model = mock_image_model
    agent._storage = mock_storage
    return agent


@pytest.fixture
def sample_task_with_storyboard():
    """Create a sample task with storyboard."""
    return Task(
        id="test-task-123",
        topic="A journey through the mountains",
        style="cinematic",
        status=TaskStatus.IMAGE_GENERATION,
        user_id="user-123",
        options={
            "storyboard": {
                "total_scenes": 1,
                "total_shots": 2,
                "scenes": [
                    {
                        "scene_number": 1,
                        "shot_number": 1,
                        "visual_description": "Wide shot of mountains at sunrise",
                        "duration": 5,
                    },
                    {
                        "scene_number": 1,
                        "shot_number": 2,
                        "visual_description": "Close-up of wildflowers",
                        "duration": 3,
                    },
                ],
            },
        },
    )


class TestImageAgent:
    """Test suite for ImageAgent."""

    def test_initialization(self):
        """Test agent initialization."""
        agent = ImageAgent(max_concurrent=3)

        assert agent.name == "image_agent"
        assert agent.max_concurrent == 3
        assert agent.retry_times == 2

    @pytest.mark.asyncio
    async def test_execute_success(
        self,
        image_agent,
        sample_task_with_storyboard,
        mock_image_model,
        mock_storage,
    ):
        """Test successful image generation."""
        result = await image_agent.execute(sample_task_with_storyboard)

        assert result["status"] == "success"
        assert result["total_shots"] == 2
        assert result["generated_images"] == 2
        assert result["failed_images"] == 0
        assert len(result["images"]) == 2

        # Verify images were generated
        assert mock_image_model.generate.call_count == 2
        assert mock_storage.upload.call_count == 2

    @pytest.mark.asyncio
    async def test_execute_with_failure(
        self,
        image_agent,
        sample_task_with_storyboard,
        mock_image_model,
    ):
        """Test image generation with some failures."""
        # First succeeds, second fails
        mock_image_model.generate.side_effect = [
            {"url": "https://example.com/image1.png"},
            Exception("Generation failed"),
        ]

        result = await image_agent.execute(sample_task_with_storyboard)

        assert result["status"] == "success"
        assert result["generated_images"] == 1
        assert result["failed_images"] == 1

    @pytest.mark.asyncio
    async def test_enhance_prompt(self, image_agent, mock_llm):
        """Test prompt enhancement."""
        result = await image_agent._enhance_prompt(
            "Mountains at sunrise",
            "cinematic",
        )

        assert "enhanced_prompt" in result
        assert "Mountains" in result["enhanced_prompt"]

    @pytest.mark.asyncio
    async def test_enhance_prompt_fallback(self, image_agent, mock_llm):
        """Test prompt enhancement fallback when LLM fails."""
        mock_llm.generate.side_effect = Exception("LLM error")

        result = await image_agent._enhance_prompt(
            "Original description",
            "cinematic",
        )

        # Should fall back to original description
        assert result["enhanced_prompt"] == "Original description"

    @pytest.mark.asyncio
    async def test_generate_single_image(
        self,
        image_agent,
        mock_image_model,
        mock_storage,
    ):
        """Test generating a single image."""
        shot = {
            "scene_number": 1,
            "shot_number": 1,
            "visual_description": "Test shot",
            "duration": 5,
        }

        result = await image_agent._generate_single_image(
            shot,
            "cinematic",
            "task-123",
            0,
        )

        assert result["success"] is True
        assert result["shot_number"] == 1
        assert result["scene_number"] == 1
        assert "storage_path" in result
        assert "url" in result

    @pytest.mark.asyncio
    async def test_generate_single_image_failure(
        self,
        image_agent,
        mock_image_model,
    ):
        """Test single image generation failure."""
        shot = {
            "scene_number": 1,
            "shot_number": 1,
            "visual_description": "Test shot",
            "duration": 5,
        }

        mock_image_model.generate.side_effect = Exception("Generation failed")

        result = await image_agent._generate_single_image(
            shot,
            "cinematic",
            "task-123",
            0,
        )

        assert result["success"] is False
        assert "error" in result

    def test_validate_input_valid(self, image_agent, sample_task_with_storyboard):
        """Test input validation with valid input."""
        assert image_agent.validate_input(sample_task_with_storyboard) is True

    def test_validate_input_no_task(self, image_agent):
        """Test input validation with no task."""
        assert image_agent.validate_input(None) is False

    def test_validate_input_no_storyboard(self, image_agent):
        """Test input validation without storyboard."""
        task = Task(
            id="test-task",
            topic="Test",
            status=TaskStatus.IMAGE_GENERATION,
            user_id="user-123",
            options={},
        )
        assert image_agent.validate_input(task) is False

    def test_validate_input_empty_storyboard(self, image_agent):
        """Test input validation with empty storyboard."""
        task = Task(
            id="test-task",
            topic="Test",
            status=TaskStatus.IMAGE_GENERATION,
            user_id="user-123",
            options={"storyboard": {"scenes": []}},
        )
        assert image_agent.validate_input(task) is False

    @pytest.mark.asyncio
    async def test_before_execute_hook(self, image_agent, sample_task_with_storyboard):
        """Test before_execute hook."""
        await image_agent.before_execute(sample_task_with_storyboard)

    @pytest.mark.asyncio
    async def test_after_execute_hook(
        self,
        image_agent,
        sample_task_with_storyboard,
    ):
        """Test after_execute hook."""
        result = {"status": "success", "generated_images": 2, "total_shots": 2}
        await image_agent.after_execute(sample_task_with_storyboard, result)


__all__ = ["TestImageAgent"]
