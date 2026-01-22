"""Prompt templates for all agents."""

from app.prompts.style_agent import (
    STYLE_DETECTION_PROMPT,
    STYLE_VALIDATION_PROMPT,
)
from app.prompts.story_agent import (
    STORY_GENERATION_PROMPT,
    STORY_REFINEMENT_PROMPT,
    STORY_VALIDATION_PROMPT,
)
from app.prompts.storyboard_agent import (
    STORYBOARD_BREAKDOWN_PROMPT,
    STORYBOARD_REFINEMENT_PROMPT,
    FRAME_DESCRIPTION_PROMPT,
    STORYBOARD_VALIDATION_PROMPT,
)
from app.prompts.image_agent import (
    IMAGE_PROMPT_ENHANCEMENT,
)
from app.prompts.video_agent import (
    VIDEO_PROMPT_ENHANCEMENT,
)
from app.prompts.composer_agent import (
    COMPOSITION_PLAN_PROMPT,
)

__all__ = [
    # Style Agent
    "STYLE_DETECTION_PROMPT",
    "STYLE_VALIDATION_PROMPT",
    # Story Agent
    "STORY_GENERATION_PROMPT",
    "STORY_REFINEMENT_PROMPT",
    "STORY_VALIDATION_PROMPT",
    # Storyboard Agent
    "STORYBOARD_BREAKDOWN_PROMPT",
    "STORYBOARD_REFINEMENT_PROMPT",
    "FRAME_DESCRIPTION_PROMPT",
    "STORYBOARD_VALIDATION_PROMPT",
    # Image Agent
    "IMAGE_PROMPT_ENHANCEMENT",
    # Video Agent
    "VIDEO_PROMPT_ENHANCEMENT",
    # Composer Agent
    "COMPOSITION_PLAN_PROMPT",
]
