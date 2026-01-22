"""Prompt templates for Storyboard Agent."""

STORYBOARD_BREAKDOWN_PROMPT = """You are an expert storyboard artist and video director. Break down the script into individual storyboard scenes/shots that can be produced.

Script Title: {title}
Script:
{script}
Style: {style}
Total Duration: {duration} seconds

Instructions:
1. Break each scene into individual shots
2. Each shot should be 3-10 seconds for optimal engagement
3. Provide detailed visual descriptions for each shot
4. Specify camera angles, movements, and framing
5. Include visual continuity between shots
6. Consider practicality for video generation

Respond with a JSON object:
{{
    "total_scenes": number of scenes,
    "total_shots": total number of shots,
    "estimated_duration": total estimated duration,
    "scenes": [
        {{
            "scene_number": 1,
            "shot_number": 1,
            "duration": 5,
            "shot_type": "wide/medium/close-up/extreme close-up/etc.",
            "camera_angle": "eye-level/low angle/high angle/bird's eye/dutch angle",
            "camera_movement": "static/pan/tilt/dolly/truck/zoom/follow",
            "visual_description": "extremely detailed visual description of what appears in frame",
            "composition": "rule of thirds, center frame, leading lines, etc.",
            "lighting": "lighting description and mood",
            "color_notes": "specific color palette for this shot",
            "action": "what happens in this shot",
            "subject_focus": "main subject/focus of the shot",
            "background": "background elements and environment",
            "transition_to_next": "cut, fade, dissolve, wipe, etc.",
            "audio_cue": "what audio accompanies this shot",
            "notes": "additional production notes"
        }}
    ],
    "shot_summary": {{
        "wide_shots": count,
        "medium_shots": count,
        "close_up_shots": count,
        "special_shots": count
    }},
    "production_notes": "overall notes for video generation team"
}}

Only respond with valid JSON, no additional text."""

STORYBOARD_REFINEMENT_PROMPT = """You are refining a storyboard for better visual continuity and production quality.

Current Storyboard:
{current_storyboard}

User Feedback:
{feedback}

Refine the storyboard based on feedback. Improve:
- Visual descriptions for AI generation
- Shot-to-shot continuity
- Pacing and timing
- Camera variety
- Production feasibility

Maintain the JSON structure.

Only respond with valid JSON, no additional text."""

FRAME_DESCRIPTION_PROMPT = """You are creating a detailed first frame description for AI image generation.

Shot Description:
{shot_description}
Style: {style}

Create an extremely detailed prompt for generating the first frame of this shot. The prompt should:
1. Be optimized for AI image generation (DALL-E, Midjourney, Stable Diffusion)
2. Include specific visual details
3. Describe lighting, color, composition
4. Specify mood and atmosphere
5. Include technical camera details

Respond with a JSON object:
{{
    "prompt": "detailed AI image generation prompt",
    "negative_prompt": "what to avoid in the image",
    "style_modifiers": ["modifier1", "modifier2"],
    "technical_specs": {{
        "aspect_ratio": "16:9 or 9:16 or 1:1",
        "resolution": "recommended resolution",
        "quality": "standard/hd"
    }},
    "key_elements": ["element1", "element2", "element3"],
    "composition_notes": "specific composition guidance"
}}

Only respond with valid JSON, no additional text."""

STORYBOARD_VALIDATION_PROMPT = """You are validating a storyboard for completeness and quality.

Storyboard:
{storyboard}
Script:
{script}

Validation Criteria:
1. Completeness: Does it cover the entire script?
2. Visual Clarity: Are shot descriptions clear and detailed?
3. Variety: Is there good shot variety?
4. Continuity: Do shots flow logically?
5. Timing: Is the total duration appropriate?
6. Feasibility: Can these shots be generated?

Respond with a JSON object:
{{
    "is_valid": true/false,
    "overall_score": 0.0-10.0,
    "coverage_complete": true/false,
    "visual_clarity_score": 0.0-10.0,
    "shot_variety_score": 0.0-10.0,
    "continuity_score": 0.0-10.0,
    "duration_match": true/false,
    "strengths": ["strength1", "strength2"],
    "issues": ["issue1", "issue2"],
    "recommendations": ["recommendation1", "recommendation2"]
}}

Only respond with valid JSON, no additional text."""


__all__ = [
    "STORYBOARD_BREAKDOWN_PROMPT",
    "STORYBOARD_REFINEMENT_PROMPT",
    "FRAME_DESCRIPTION_PROMPT",
    "STORYBOARD_VALIDATION_PROMPT",
]
