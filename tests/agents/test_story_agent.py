"""Unit tests for StoryAgent."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.agents.story import StoryAgent
from app.entities.task import Task, TaskStatus


@pytest.fixture
def mock_llm():
    """Create a mock LLM provider."""
    llm = AsyncMock()

    # Mock script generation response
    script_response = '''{
        "title": "Mountain Journey",
        "logline": "A breathtaking journey through majestic mountain peaks",
        "estimated_duration": 60,
        "scenes": [
            {
                "scene_number": 1,
                "duration": 10,
                "location": "mountain base",
                "time_of_day": "sunrise",
                "visual_description": "Camera pans across misty mountain peaks at dawn",
                "audio": {
                    "dialogue": "",
                    "music": "orchestral, building slowly",
                    "sound_effects": ["wind", "bird calls"]
                },
                "camera_movement": "slow panoramic pan",
                "transition": "fade to next scene",
                "notes": "Establish the scale and beauty"
            }
        ],
        "narrative_arc": {
            "hook": "Stunning aerial shots of mountains",
            "development": "Journey progresses through varied terrain",
            "climax": "Reaching the summit",
            "conclusion": "Contemplative view from the top"
        },
        "total_duration": 60,
        "word_count": 150
    }'''

    # Mock validation response
    validation_response = '''{
        "is_valid": true,
        "overall_score": 8.5,
        "strengths": ["Clear narrative arc", "Strong visual descriptions"],
        "weaknesses": ["Could add more dialogue"],
        "suggestions": ["Consider adding voiceover narration"],
        "duration_match": true,
        "estimated_duration": 60,
        "reasoning": "Well-structured script with good pacing"
    }'''

    llm.generate = AsyncMock(side_effect=[script_response, validation_response])
    return llm


@pytest.fixture
def story_agent(mock_llm):
    """Create a StoryAgent instance with mocked LLM."""
    agent = StoryAgent()
    agent._llm = mock_llm
    return agent


@pytest.fixture
def sample_task():
    """Create a sample task."""
    return Task(
        id="test-task-123",
        topic="A journey through the mountains",
        style="cinematic",
        status=TaskStatus.STORY_GENERATION,
        user_id="user-123",
        options={"duration": 60},
    )


class TestStoryAgent:
    """Test suite for StoryAgent."""

    def test_initialization(self):
        """Test agent initialization."""
        with patch('app.agents.story.model_manager') as mock_mm:
            mock_mm.get_llm_provider.return_value = MagicMock()

            agent = StoryAgent()

            assert agent.name == "story_agent"
            assert agent.retry_times == 2
            assert agent.retry_delay == 1.0

    @pytest.mark.asyncio
    async def test_execute_script_generation(self, story_agent, sample_task, mock_llm):
        """Test script generation execution."""
        result = await story_agent.execute(sample_task)

        assert result["status"] == "success"
        assert "script" in result
        assert "validation" in result

        script = result["script"]
        assert script["title"] == "Mountain Journey"
        assert len(script["scenes"]) > 0
        assert script["estimated_duration"] == 60

        # Verify LLM was called
        assert mock_llm.generate.call_count == 2  # generation + validation

    @pytest.mark.asyncio
    async def test_execute_with_options(self, story_agent, mock_llm):
        """Test execution with task options."""
        task = Task(
            id="test-task-456",
            topic="Ocean adventure",
            status=TaskStatus.STORY_GENERATION,
            user_id="user-123",
            options={
                "style": "documentary",
                "duration": 90,
            },
        )

        mock_llm.generate.side_effect = [
            '{"title": "Ocean", "scenes": [], "estimated_duration": 90}',
            '{"is_valid": true, "overall_score": 8.0}',
        ]

        result = await story_agent.execute(task)

        assert result["status"] == "success"
        assert "script" in result

    @pytest.mark.asyncio
    async def test_refine_script(self, story_agent, mock_llm):
        """Test script refinement."""
        current_script = {
            "title": "Original",
            "scenes": [{"scene_number": 1}],
        }

        mock_llm.generate.return_value = '{"title": "Refined", "scenes": []}'

        refined = await story_agent.refine_script(
            task=Task(
                id="test-task",
                topic="Test",
                status=TaskStatus.STORY_GENERATION,
                user_id="user-123",
            ),
            current_script=current_script,
            feedback="Make it more dramatic",
        )

        assert refined["title"] == "Refined"
        mock_llm.generate.assert_called_once()

    def test_validate_input_valid(self, story_agent, sample_task):
        """Test input validation with valid input."""
        assert story_agent.validate_input(sample_task) is True

    def test_validate_input_no_task(self, story_agent):
        """Test input validation with no task."""
        assert story_agent.validate_input(None) is False

    def test_validate_input_no_topic(self, story_agent):
        """Test input validation with no topic."""
        task = Task(
            id="test-task",
            topic="",
            status=TaskStatus.STORY_GENERATION,
            user_id="user-123",
        )
        assert story_agent.validate_input(task) is False

    def test_validate_input_short_topic(self, story_agent):
        """Test input validation with short topic."""
        task = Task(
            id="test-task",
            topic="Hi",
            status=TaskStatus.STORY_GENERATION,
            user_id="user-123",
        )
        assert story_agent.validate_input(task) is False

    @pytest.mark.asyncio
    async def test_parse_json_response(self, story_agent):
        """Test JSON parsing."""
        json_str = '{"title": "Test", "scenes": []}'
        result = story_agent._parse_json_response(json_str)
        assert result["title"] == "Test"

    @pytest.mark.asyncio
    async def test_parse_json_with_extra_text(self, story_agent):
        """Test JSON parsing with extra text."""
        json_with_text = "Response: {\"title\": \"Test\"} Done"
        result = story_agent._parse_json_response(json_with_text)
        assert result["title"] == "Test"

    @pytest.mark.asyncio
    async def test_script_validation_fallback(self, story_agent, mock_llm):
        """Test script validation fallback when LLM fails."""
        # Script generation succeeds
        mock_llm.generate.side_effect = [
            '{"title": "Test", "scenes": []}',
            Exception("Validation API error"),
        ]

        task = Task(
            id="test-task",
            topic="Test topic for script generation",
            status=TaskStatus.STORY_GENERATION,
            user_id="user-123",
            options={"duration": 60},
        )

        result = await story_agent.execute(task)

        # Should still succeed with basic validation
        assert result["status"] == "success"
        assert result["validation"]["is_valid"] is True
        assert result["validation"]["overall_score"] == 7.0

    @pytest.mark.asyncio
    async def test_before_execute_hook(self, story_agent, sample_task):
        """Test before_execute hook."""
        await story_agent.before_execute(sample_task)

    @pytest.mark.asyncio
    async def test_after_execute_hook(self, story_agent, sample_task):
        """Test after_execute hook."""
        result = {"status": "success", "script": {}}
        await story_agent.after_execute(sample_task, result)


__all__ = ["TestStoryAgent"]
