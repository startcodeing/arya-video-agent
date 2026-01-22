"""Prompt templates for Video Agent."""

VIDEO_PROMPT_ENHANCEMENT = """You are an expert at creating prompts for AI video generation models.

Base Shot Description:
{shot_description}

First Frame Image:
{image_description}

Video Style: {style}
Duration: {duration} seconds

Enhance this description into a detailed prompt for AI video generation. The prompt should:
1. Describe the motion and movement in the scene
2. Specify camera movements (pan, tilt, zoom, dolly, etc.)
3. Describe the pacing of the action
4. Include transitions and timing
5. Be optimized for video generation AI

Respond with a JSON object:
{{
    "enhanced_prompt": "detailed prompt for video generation",
    "motion_description": "specific description of movement and action",
    "camera_movement": "detailed camera movement instructions",
    "pacing": "slow/moderate/fast",
    "key_moments": ["moment1 at 0-2s", "moment2 at 2-4s", "..."],
    "transitions": "how elements enter/exit frame",
    "technical_specs": {{
        "duration": {duration},
        "aspect_ratio": "16:9 or 9:16 or 1:1",
        "fps": 24 or 30
    }}
}}

Only respond with valid JSON, no additional text."""


__all__ = [
    "VIDEO_PROMPT_ENHANCEMENT",
]
