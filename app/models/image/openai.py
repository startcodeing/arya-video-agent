"""OpenAI DALL-E image generation provider implementation."""

from typing import Any, Dict, List

from openai import AsyncOpenAI

from app.config import settings
from app.models.image.base import BaseImageModel
from app.utils.logger import get_logger

logger = get_logger(__name__)


class DALLEImageModel(BaseImageModel):
    """OpenAI DALL-E image generation provider implementation."""

    # Available models
    AVAILABLE_MODELS = [
        "dall-e-3",
        "dall-e-2",
    ]

    # Available sizes for DALL-E 3
    DALLE3_SIZES = ["1024x1024", "1792x1024", "1024x1792"]

    # Available sizes for DALL-E 2
    DALLE2_SIZES = ["256x256", "512x512", "1024x1024"]

    def __init__(self, api_key: str = None):
        """
        Initialize DALL-E image model provider.

        Args:
            api_key: OpenAI API key (optional, uses settings if not provided)
        """
        self.api_key = api_key or settings.OPENAI_API_KEY
        if not self.api_key:
            raise ValueError("OpenAI API key is required")

        self._client = None
        self._initialize_client()

    def _initialize_client(self) -> None:
        """Initialize OpenAI async client."""
        self._client = AsyncOpenAI(api_key=self.api_key)
        logger.info("DALL-E image model client initialized")

    async def generate(
        self,
        prompt: str,
        size: str = "1024x1024",
        n: int = 1,
        quality: str = "standard",
        style: str = None,
        model: str = None,
        **kwargs
    ) -> Dict[str, any]:
        """
        Generate image(s) using DALL-E.

        Args:
            prompt: Text description of the desired image
            size: Image size
            n: Number of images to generate
            quality: Image quality ("standard" or "hd")
            style: Image style ("vivid" or "natural") - DALL-E 3 only
            model: Model to use (default: dall-e-3)
            **kwargs: Additional parameters

        Returns:
            Dict containing image URLs and revised prompt
        """
        model = model or settings.DEFAULT_IMAGE_MODEL or "dall-e-3"

        # Validate parameters based on model
        if model == "dall-e-3":
            if size not in self.DALLE3_SIZES:
                raise ValueError(f"DALL-E 3 only supports sizes: {self.DALLE3_SIZES}")
            available_qualities = ["standard", "hd"]
            if quality not in available_qualities:
                raise ValueError(f"Quality must be one of: {available_qualities}")
        elif model == "dall-e-2":
            if size not in self.DALLE2_SIZES:
                raise ValueError(f"DALL-E 2 only supports sizes: {self.DALLE2_SIZES}")
            if quality != "standard":
                logger.warning("DALL-E 2 only supports 'standard' quality")

        # Prepare parameters
        params = {
            "model": model,
            "prompt": prompt,
            "size": size,
            "n": n,
        }

        # Add quality parameter for DALL-E 3
        if model == "dall-e-3":
            params["quality"] = quality

        # Add style parameter for DALL-E 3
        if model == "dall-e-3" and style:
            available_styles = ["vivid", "natural"]
            if style not in available_styles:
                raise ValueError(f"Style must be one of: {available_styles}")
            params["style"] = style

        try:
            response = await self._client.images.generate(**params)

            # Extract URLs
            urls = [item.url for item in response.data]

            logger.info(f"DALL-E generation completed: model={model}, count={len(urls)}")

            return {
                "url": urls[0] if n == 1 else urls,
                "urls": urls,
                "revised_prompt": response.data[0].revised_prompt if hasattr(response.data[0], 'revised_prompt') else prompt,
            }

        except Exception as e:
            logger.error(f"DALL-E generation failed: {e}")
            raise

    async def generate_from_image(
        self,
        prompt: str,
        image_url: str,
        size: str = "1024x1024",
        n: int = 1,
        **kwargs
    ) -> Dict[str, any]:
        """
        Generate image variations (image-to-image).

        Only supported by DALL-E 2.

        Args:
            prompt: Text description of modifications
            image_url: URL of the source image
            size: Image size
            n: Number of variations
            **kwargs: Additional parameters

        Returns:
            Dict containing image URLs
        """
        try:
            response = await self._client.images.create_variation(
                image=image_url,
                size=size,
                n=n,
                **kwargs
            )

            urls = [item.url for item in response.data]

            logger.info(f"DALL-E variation completed: count={len(urls)}")

            return {
                "url": urls[0] if n == 1 else urls,
                "urls": urls,
            }

        except Exception as e:
            logger.error(f"DALL-E variation failed: {e}")
            raise

    def get_available_sizes(self) -> List[str]:
        """Get list of available image sizes."""
        # Return DALL-E 3 sizes (most recent)
        return self.DALLE3_SIZES

    def get_available_styles(self) -> List[str]:
        """Get list of available styles."""
        return ["vivid", "natural"]

    def get_available_models(self) -> List[str]:
        """Get list of available models."""
        return self.AVAILABLE_MODELS

    def get_default_model(self) -> str:
        """Get default model."""
        return settings.DEFAULT_IMAGE_MODEL or "dall-e-3"


__all__ = ["DALLEImageModel"]
