"""Prompt templates for Composer Agent."""

COMPOSITION_PLAN_PROMPT = """You are an expert video editor and composer. Analyze the storyboard and create a composition plan.

Storyboard Summary:
{storyboard_summary}

Total Duration: {duration} seconds
Total Shots: {total_shots}

Create a detailed plan for composing these video clips into a final video. Consider:
1. Shot order and transitions
2. Timing and pacing
3. Audio synchronization
4. Visual continuity
5. Story flow

Respond with a JSON object:
{{
    "composition_plan": {{
        "total_duration": total duration in seconds,
        "shot_order": [1, 2, 3, ...],
        "transitions": [
            {{
                "from_shot": 1,
                "to_shot": 2,
                "type": "cut/fade/dissolve/wipe",
                "duration": 0.5
            }}
        ],
        "timing_adjustments": [
            {{
                "shot_number": 1,
                "original_duration": 5,
                "adjusted_duration": 4.5,
                "reason": "better pacing"
            }}
        ],
        "audio_plan": {{
            "music": "music description and timing",
            "sound_effects": ["sfx1 at shot 1", "sfx2 at shot 3"],
            "dialogue": "if any dialogue present"
        }},
        "effects": [
            {{
                "shot": 2,
                "effect": "color correction",
                "parameters": "warm tone, increased contrast"
            }}
        ],
        "notes": "overall composition notes"
    }},
    "technical_specs": {{
        "output_resolution": "1920x1080 or 1080x1920",
        "fps": 30,
        "codec": "h264",
        "bitrate": "5000k"
    }}
}}

Only respond with valid JSON, no additional text."""


__all__ = [
    "COMPOSITION_PLAN_PROMPT",
]
