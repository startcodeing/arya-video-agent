"""Unit tests for StyleAgent."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.agents.style import StyleAgent
from app.entities.task import Task, TaskStatus


@pytest.fixture
def mock_llm():
    """Create a mock LLM provider."""
    llm = AsyncMock()

    # Mock style detection response
    detection_response = '''{
        "style": "cinematic",
        "reasoning": "The topic suggests a dramatic, film-like presentation would be most effective",
        "visual_elements": ["dramatic lighting", "smooth camera movements", "professional color grading"],
        "color_palette": "warm tones with high contrast",
        "mood": "dramatic and engaging",
        "camera_style": "smooth tracking shots with selective focus"
    }'''

    # Mock validation response
    validation_response = '''{
        "is_appropriate": true,
        "confidence": 0.95,
        "suggestions": [],
        "reasoning": "The cinematic style is well-suited for this topic"
    }'''

    llm.generate = AsyncMock(side_effect=[detection_response, validation_response])
    return llm


@pytest.fixture
def style_agent(mock_llm):
    """Create a StyleAgent instance with mocked LLM."""
    agent = StyleAgent()
    agent._llm = mock_llm
    return agent


@pytest.fixture
def sample_task():
    """Create a sample task."""
    return Task(
        id="test-task-123",
        topic="A journey through the mountains",
        status=TaskStatus.STYLE_DETECTION,
        user_id="user-123",
    )


class TestStyleAgent:
    """Test suite for StyleAgent."""

    def test_initialization(self):
        """Test agent initialization."""
        with patch('app.agents.style.model_manager') as mock_mm:
            mock_mm.get_llm_provider.return_value = MagicMock()

            agent = StyleAgent()

            assert agent.name == "style_agent"
            assert agent.retry_times == 2
            assert agent.retry_delay == 1.0

    @pytest.mark.asyncio
    async def test_execute_style_detection(self, style_agent, sample_task, mock_llm):
        """Test style detection execution."""
        result = await style_agent.execute(sample_task)

        assert result["status"] == "success"
        assert result["style"] == "cinematic"
        assert result["auto_detected"] is True
        assert "reasoning" in result
        assert "visual_elements" in result
        assert "color_palette" in result

        # Verify LLM was called
        mock_llm.generate.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_with_predefined_style(self, style_agent, mock_llm):
        """Test execution with predefined style."""
        task = Task(
            id="test-task-456",
            topic="A journey through the mountains",
            style="documentary",
            status=TaskStatus.STYLE_DETECTION,
            user_id="user-123",
        )

        result = await style_agent.execute(task)

        assert result["status"] == "success"
        assert result["style"] == "documentary"
        assert result["auto_detected"] is False
        assert result["is_appropriate"] is True

    @pytest.mark.asyncio
    async def test_parse_json_response(self, style_agent):
        """Test JSON parsing."""
        # Valid JSON
        json_str = '{"style": "cinematic", "mood": "dramatic"}'
        result = style_agent._parse_json_response(json_str)
        assert result["style"] == "cinematic"

        # JSON with extra text
        json_with_text = "Here's the result: {\"style\": \"cinematic\"} End of response"
        result = style_agent._parse_json_response(json_with_text)
        assert result["style"] == "cinematic"

    @pytest.mark.asyncio
    async def test_parse_json_invalid(self, style_agent):
        """Test JSON parsing with invalid input."""
        with pytest.raises(ValueError):
            style_agent._parse_json_response("This is not JSON at all")

    def test_validate_input_valid(self, style_agent, sample_task):
        """Test input validation with valid input."""
        assert style_agent.validate_input(sample_task) is True

    def test_validate_input_no_task(self, style_agent):
        """Test input validation with no task."""
        assert style_agent.validate_input(None) is False

    def test_validate_input_no_topic(self, style_agent):
        """Test input validation with no topic."""
        task = Task(
            id="test-task",
            topic="",
            status=TaskStatus.STYLE_DETECTION,
            user_id="user-123",
        )
        assert style_agent.validate_input(task) is False

    def test_validate_input_short_topic(self, style_agent):
        """Test input validation with short topic."""
        task = Task(
            id="test-task",
            topic="Hi",
            status=TaskStatus.STYLE_DETECTION,
            user_id="user-123",
        )
        assert style_agent.validate_input(task) is False

    @pytest.mark.asyncio
    async def test_before_execute_hook(self, style_agent, sample_task):
        """Test before_execute hook."""
        # Should not raise
        await style_agent.before_execute(sample_task)

    @pytest.mark.asyncio
    async def test_after_execute_hook(self, style_agent, sample_task):
        """Test after_execute hook."""
        result = {"status": "success"}
        # Should not raise
        await style_agent.after_execute(sample_task, result)

    @pytest.mark.asyncio
    async def test_execute_with_retry(self, style_agent, sample_task, mock_llm):
        """Test execution with retry mechanism."""
        # First call fails, second succeeds
        mock_llm.generate.side_effect = [
            Exception("API error"),
            '{"style": "cinematic", "reasoning": "test"}'
        ]

        result = await style_agent.execute_with_retry(sample_task)

        assert result["status"] == "success"
        assert mock_llm.generate.call_count == 2


__all__ = ["TestStyleAgent"]
