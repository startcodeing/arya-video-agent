"""Prompt templates for Story Agent."""

STORY_GENERATION_PROMPT = """You are an expert video scriptwriter. Create an engaging video script based on the given topic and style.

Topic: {topic}
Style: {style}
Target Duration: {duration} seconds

Requirements:
1. Create a compelling narrative arc (hook, development, climax, conclusion)
2. Write for visual storytelling (show, don't just tell)
3. Keep dialogue natural and minimal
4. Focus on visual descriptions that can be captured on video
5. Include pacing notes
6. Consider the target duration

Respond with a JSON object:
{{
    "title": "engaging title for the video",
    "logline": "one-sentence summary of the video",
    "estimated_duration": estimated duration in seconds,
    "scenes": [
        {{
            "scene_number": 1,
            "duration": 5,
            "location": "scene location",
            "time_of_day": "day/night/sunset",
            "visual_description": "detailed visual description of what's on screen",
            "audio": {
                "dialogue": "any spoken words",
                "music": "music mood/style",
                "sound_effects": ["sfx1", "sfx2"]
            },
            "camera_movement": "pan, tilt, zoom, static, etc.",
            "transition": "how this scene transitions to the next",
            "notes": "additional direction for the filmmaker"
        }}
    ],
    "narrative_arc": {{
        "hook": "how the video captures attention in first 3 seconds",
        "development": "how the story builds",
        "climax": "the peak moment",
        "conclusion": "how it wraps up"
    }},
    "total_duration": total duration in seconds,
    "word_count": approximate word count
}}

Only respond with valid JSON, no additional text."""

STORY_REFINEMENT_PROMPT = """You are refining a video script for better quality and coherence.

Current Script:
{current_script}

User Feedback:
{feedback}

Refine the script based on the feedback. Maintain the JSON structure but improve:
- Visual descriptions
- Pacing and timing
- Narrative flow
- Dialogue (if any)
- Emotional impact

Respond with the same JSON structure as the original script.

Only respond with valid JSON, no additional text."""

STORY_VALIDATION_PROMPT = """You are validating a video script for quality and completeness.

Script:
{script}

Validation Criteria:
1. Narrative Structure: Does it have a clear beginning, middle, and end?
2. Visual Clarity: Are the visual descriptions clear and filmable?
3. Pacing: Is the timing appropriate for the content?
4. Engagement: Will it hold viewer interest?
5. Duration: Does it match the target duration?

Respond with a JSON object:
{{
    "is_valid": true/false,
    "overall_score": 0.0-10.0,
    "strengths": ["strength1", "strength2"],
    "weaknesses": ["weakness1", "weakness2"],
    "suggestions": ["improvement1", "improvement2"],
    "duration_match": true/false,
    "estimated_duration": estimated duration in seconds,
    "reasoning": "overall evaluation"
}}

Only respond with valid JSON, no additional text."""


__all__ = [
    "STORY_GENERATION_PROMPT",
    "STORY_REFINEMENT_PROMPT",
    "STORY_VALIDATION_PROMPT",
]
