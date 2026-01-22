"""Unit tests for StoryboardAgent."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.agents.storyboard import StoryboardAgent
from app.entities.task import Task, TaskStatus


@pytest.fixture
def mock_llm():
    """Create a mock LLM provider."""
    llm = AsyncMock()

    # Mock storyboard generation response
    storyboard_response = '''{
        "total_scenes": 1,
        "total_shots": 3,
        "estimated_duration": 30,
        "scenes": [
            {
                "scene_number": 1,
                "shot_number": 1,
                "duration": 10,
                "shot_type": "wide",
                "camera_angle": "eye-level",
                "camera_movement": "static",
                "visual_description": "Wide shot of mountain landscape at sunrise",
                "composition": "rule of thirds",
                "lighting": "golden hour sunlight",
                "color_notes": "warm oranges and blues",
                "action": "camera reveals the landscape",
                "subject_focus": "mountain peaks",
                "background": "sky and clouds",
                "transition_to_next": "cut",
                "audio_cue": "gentle music starts",
                "notes": "Establishing shot"
            },
            {
                "scene_number": 1,
                "shot_number": 2,
                "duration": 10,
                "shot_type": "medium",
                "camera_angle": "low angle",
                "camera_movement": "slow push in",
                "visual_description": "Closer view of mountain details",
                "composition": "center frame",
                "lighting": "soft morning light",
                "color_notes": "natural colors",
                "action": "highlighting textures",
                "subject_focus": "rock formations",
                "background": "mountain slope",
                "transition_to_next": "fade",
                "audio_cue": "music builds",
                "notes": "Detail shot"
            },
            {
                "scene_number": 1,
                "shot_number": 3,
                "duration": 10,
                "shot_type": "close-up",
                "camera_angle": "high angle",
                "camera_movement": "pan right",
                "visual_description": "Close-up of wildflowers",
                "composition": "depth of field",
                "lighting": "dappled sunlight",
                "color_notes": "vibrant colors",
                "action": "flowers swaying in breeze",
                "subject_focus": "wildflowers",
                "background": "blurred mountains",
                "transition_to_next": "cut",
                "audio_cue": "nature sounds",
                "notes": "Foreground interest"
            }
        ],
        "shot_summary": {
            "wide_shots": 1,
            "medium_shots": 1,
            "close_up_shots": 1,
            "special_shots": 0
        },
        "production_notes": "Capture during golden hour for best lighting"
    }'''

    # Mock validation response
    validation_response = '''{
        "is_valid": true,
        "overall_score": 9.0,
        "coverage_complete": true,
        "visual_clarity_score": 9.5,
        "shot_variety_score": 9.0,
        "continuity_score": 8.5,
        "duration_match": true,
        "strengths": ["Excellent shot variety", "Clear visual descriptions"],
        "issues": [],
        "recommendations": ["Consider adding more close-ups for emotional impact"]
    }'''

    llm.generate = AsyncMock(side_effect=[storyboard_response, validation_response])
    return llm


@pytest.fixture
def storyboard_agent(mock_llm):
    """Create a StoryboardAgent instance with mocked LLM."""
    agent = StoryboardAgent()
    agent._llm = mock_llm
    return agent


@pytest.fixture
def sample_script():
    """Create a sample script."""
    return {
        "title": "Mountain Journey",
        "logline": "A journey through mountains",
        "estimated_duration": 60,
        "scenes": [
            {
                "scene_number": 1,
                "duration": 10,
                "visual_description": "Wide shot of mountains",
                "camera_movement": "pan",
            },
        ],
    }


@pytest.fixture
def sample_task(sample_script):
    """Create a sample task with script."""
    return Task(
        id="test-task-123",
        topic="A journey through the mountains",
        style="cinematic",
        status=TaskStatus.STORYBOARD_BREAKDOWN,
        user_id="user-123",
        options={
            "script": sample_script,
            "duration": 60,
        },
    )


class TestStoryboardAgent:
    """Test suite for StoryboardAgent."""

    def test_initialization(self):
        """Test agent initialization."""
        with patch('app.agents.storyboard.model_manager') as mock_mm:
            mock_mm.get_llm_provider.return_value = MagicMock()

            agent = StoryboardAgent()

            assert agent.name == "storyboard_agent"
            assert agent.retry_times == 2
            assert agent.retry_delay == 1.0

    @pytest.mark.asyncio
    async def test_execute_storyboard_generation(self, storyboard_agent, sample_task, mock_llm):
        """Test storyboard generation execution."""
        result = await storyboard_agent.execute(sample_task)

        assert result["status"] == "success"
        assert "storyboard" in result
        assert "validation" in result

        storyboard = result["storyboard"]
        assert storyboard["total_scenes"] == 1
        assert storyboard["total_shots"] == 3
        assert len(storyboard["scenes"]) == 3

        # Verify LLM was called
        assert mock_llm.generate.call_count == 2

    @pytest.mark.asyncio
    async def test_validate_input_valid(self, storyboard_agent, sample_task):
        """Test input validation with valid input."""
        assert storyboard_agent.validate_input(sample_task) is True

    def test_validate_input_no_task(self, storyboard_agent):
        """Test input validation with no task."""
        assert storyboard_agent.validate_input(None) is False

    def test_validate_input_no_script(self, storyboard_agent):
        """Test input validation with no script."""
        task = Task(
            id="test-task",
            topic="Test",
            status=TaskStatus.STORYBOARD_BREAKDOWN,
            user_id="user-123",
            options={},
        )
        assert storyboard_agent.validate_input(task) is False

    def test_validate_input_empty_script(self, storyboard_agent):
        """Test input validation with empty script."""
        task = Task(
            id="test-task",
            topic="Test",
            status=TaskStatus.STORYBOARD_BREAKDOWN,
            user_id="user-123",
            options={"script": {}},
        )
        assert storyboard_agent.validate_input(task) is False

    def test_validate_input_no_scenes(self, storyboard_agent):
        """Test input validation with script but no scenes."""
        task = Task(
            id="test-task",
            topic="Test",
            status=TaskStatus.STORYBOARD_BREAKDOWN,
            user_id="user-123",
            options={"script": {"scenes": []}},
        )
        assert storyboard_agent.validate_input(task) is False

    @pytest.mark.asyncio
    async def test_generate_frame_description(self, storyboard_agent, mock_llm):
        """Test frame description generation."""
        shot = {
            "shot_number": 1,
            "visual_description": "Wide shot of mountains at sunrise",
            "shot_type": "wide",
        }

        mock_llm.generate.return_value = '''{
            "prompt": "Cinematic wide shot of majestic mountain peaks at sunrise, golden hour lighting, dramatic clouds, professional photography, 8k resolution",
            "negative_prompt": "blurry, low quality, distorted",
            "style_modifiers": ["cinematic", "dramatic", "professional"],
            "technical_specs": {
                "aspect_ratio": "16:9",
                "resolution": "1920x1080",
                "quality": "hd"
            },
            "key_elements": ["mountains", "sunrise", "clouds"],
            "composition_notes": "Rule of thirds with mountains in upper third"
        }'''

        frame_data = await storyboard_agent.generate_frame_description(
            shot=shot,
            style="cinematic",
        )

        assert "prompt" in frame_data
        assert frame_data["technical_specs"]["aspect_ratio"] == "16:9"

    @pytest.mark.asyncio
    async def test_refine_storyboard(self, storyboard_agent, mock_llm):
        """Test storyboard refinement."""
        current_storyboard = {
            "total_scenes": 1,
            "total_shots": 2,
            "scenes": [],
        }

        mock_llm.generate.return_value = '{"total_scenes": 1, "total_shots": 3, "scenes": []}'

        refined = await storyboard_agent.refine_storyboard(
            task=Task(
                id="test-task",
                topic="Test",
                status=TaskStatus.STORYBOARD_BREAKDOWN,
                user_id="user-123",
                options={},
            ),
            current_storyboard=current_storyboard,
            feedback="Add more close-up shots",
        )

        assert refined["total_shots"] == 3
        mock_llm.generate.assert_called_once()

    @pytest.mark.asyncio
    async def test_parse_json_response(self, storyboard_agent):
        """Test JSON parsing."""
        json_str = '{"total_shots": 3, "scenes": []}'
        result = storyboard_agent._parse_json_response(json_str)
        assert result["total_shots"] == 3

    @pytest.mark.asyncio
    async def test_parse_json_with_extra_text(self, storyboard_agent):
        """Test JSON parsing with extra text."""
        json_with_text = "Result: {\"total_shots\": 3} End"
        result = storyboard_agent._parse_json_response(json_with_text)
        assert result["total_shots"] == 3

    @pytest.mark.asyncio
    async def test_frame_description_no_description(self, storyboard_agent):
        """Test frame description with missing visual description."""
        shot = {"shot_number": 1}

        with pytest.raises(ValueError, match="Shot has no visual description"):
            await storyboard_agent.generate_frame_description(
                shot=shot,
                style="cinematic",
            )

    @pytest.mark.asyncio
    async def test_storyboard_validation_fallback(self, storyboard_agent, mock_llm):
        """Test storyboard validation fallback when LLM fails."""
        # Storyboard generation succeeds
        mock_llm.generate.side_effect = [
            '{"total_scenes": 1, "total_shots": 2, "scenes": []}',
            Exception("Validation API error"),
        ]

        task = Task(
            id="test-task",
            topic="Test",
            status=TaskStatus.STORYBOARD_BREAKDOWN,
            user_id="user-123",
            options={
                "script": {"scenes": [{"scene_number": 1}]},
                "duration": 60,
            },
        )

        result = await storyboard_agent.execute(task)

        # Should still succeed with basic validation
        assert result["status"] == "success"
        assert result["validation"]["is_valid"] is True
        assert result["validation"]["overall_score"] == 7.0

    @pytest.mark.asyncio
    async def test_before_execute_hook(self, storyboard_agent, sample_task):
        """Test before_execute hook."""
        await storyboard_agent.before_execute(sample_task)

    @pytest.mark.asyncio
    async def test_after_execute_hook(self, storyboard_agent, sample_task):
        """Test after_execute hook."""
        result = {"status": "success", "storyboard": {}}
        await storyboard_agent.after_execute(sample_task, result)


__all__ = ["TestStoryboardAgent"]
