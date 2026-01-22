"""Prompt templates for Style Agent."""

STYLE_DETECTION_PROMPT = """You are an expert video style analyzer. Analyze the given topic and determine the most appropriate video style.

Topic: {topic}

Available styles:
1. **Cinematic** - Dramatic, film-like quality with smooth camera movements and professional color grading
2. **Documentary** - Informative, realistic with interview-style framing and natural lighting
3. **Animated** - 2D or 3D animated style with vibrant colors and expressive characters
4. **Minimalist** - Clean, simple design with limited color palette and focus on essential elements
5. **Vintage** - Retro aesthetic with film grain, warm tones, and nostalgic feel
6. **Futuristic** - Sci-fi elements, neon colors, holographic effects, and advanced technology
7. **Nature** - Organic, earthy tones with focus on natural environments and wildlife
8. **Corporate** - Professional, clean business style with confident presentation

Consider the following aspects:
- Target audience
- Emotional tone
- Subject matter
- Context/purpose

Respond with a JSON object containing:
{{
    "style": "chosen_style_name",
    "reasoning": "brief explanation of why this style fits the topic",
    "visual_elements": ["element1", "element2", "..."],
    "color_palette": "primary color description",
    "mood": "overall mood/tone of the video",
    "camera_style": "camera movement and framing approach"
}}

Only respond with valid JSON, no additional text."""

STYLE_VALIDATION_PROMPT = """You are validating a video style selection.

Topic: {topic}
Proposed Style: {style}

Evaluate if this style is appropriate for the topic. Consider:
- Does the style match the subject matter?
- Will the style resonate with the target audience?
- Is the mood appropriate for the content?

Respond with a JSON object:
{{
    "is_appropriate": true/false,
    "confidence": 0.0-1.0,
    "suggestions": ["alternative styles if current is not ideal"],
    "reasoning": "explanation of your evaluation"
}}

Only respond with valid JSON, no additional text."""


__all__ = [
    "STYLE_DETECTION_PROMPT",
    "STYLE_VALIDATION_PROMPT",
]
