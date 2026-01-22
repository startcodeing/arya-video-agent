"""Prompt templates for Image Agent."""

IMAGE_PROMPT_ENHANCEMENT = """You are an expert at creating prompts for AI image generation models (DALL-E, Midjourney, Stable Diffusion).

Base Shot Description:
{shot_description}

Video Style: {style}

Enhance this description into a detailed prompt for AI image generation. The prompt should:
1. Be highly detailed and specific
2. Include lighting, composition, mood, and atmosphere
3. Describe the style (photorealistic, cinematic, artistic, etc.)
4. Include technical quality keywords
5. Be optimized for the specific AI model

Respond with a JSON object:
{{
    "enhanced_prompt": "detailed, optimized prompt for image generation",
    "negative_prompt": "elements to avoid in the image",
    "style_keywords": ["keyword1", "keyword2", "keyword3"],
    "quality_modifiers": ["modifier1", "modifier2"],
    "technical_specs": {{
        "aspect_ratio": "16:9 or 9:16 or 1:1",
        "quality": "standard or hd"
    }},
    "key_elements": ["element1", "element2", "element3"]
}}

Only respond with valid JSON, no additional text."""


__all__ = [
    "IMAGE_PROMPT_ENHANCEMENT",
]
