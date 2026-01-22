"""Base class for Image generation providers."""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional


class BaseImageModel(ABC):
    """
    Base class for all image generation providers.

    All image generation providers (DALL-E, Stable Diffusion, etc.) should
    inherit from this class and implement the required methods.
    """

    def __init__(self, api_key: str = None):
        """
        Initialize the image model provider.

        Args:
            api_key: API key for the provider (optional, can use env var)
        """
        self.api_key = api_key
        self._client = None
        self._initialize_client()

    @abstractmethod
    def _initialize_client(self) -> None:
        """
        Initialize the provider's client.

        This method should set self._client to the provider's client instance.
        """
        raise NotImplementedError(f"{self.__class__.__name__} must implement _initialize_client()")

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        size: str = "1024x1024",
        n: int = 1,
        quality: str = "standard",
        style: str = None,
        **kwargs
    ) -> Dict[str, any]:
        """
        Generate image(s) from text prompt.

        Args:
            prompt: Text description of the desired image
            size: Image size (e.g., "1024x1024", "512x512")
            n: Number of images to generate
            quality: Image quality ("standard" or "hd")
            style: Image style (provider-specific)
            **kwargs: Additional provider-specific parameters

        Returns:
            Dict containing:
                - url: URL(s) of the generated image(s)
                - revised_prompt: Revised prompt if applicable
        """
        raise NotImplementedError(f"{self.__class__.__name__} must implement generate()")

    async def generate_from_image(
        self,
        prompt: str,
        image_url: str,
        size: str = "1024x1024",
        n: int = 1,
        **kwargs
    ) -> Dict[str, any]:
        """
        Generate image(s) with image input (image-to-image).

        Args:
            prompt: Text description of modifications
            image_url: URL of the source image
            size: Image size
            n: Number of images to generate
            **kwargs: Additional parameters

        Returns:
            Dict containing image URL(s)
        """
        # Default: not implemented
        raise NotImplementedError(
            f"{self.__class__.__name__} does not support image-to-image generation"
        )

    def get_available_sizes(self) -> List[str]:
        """
        Get list of available image sizes.

        Returns:
            List of supported sizes
        """
        return ["256x256", "512x512", "1024x1024", "1792x1024", "1024x1792"]

    def get_available_styles(self) -> List[str]:
        """
        Get list of available styles.

        Returns:
            List of supported styles
        """
        return ["vivid", "natural"]

    def get_available_models(self) -> List[str]:
        """
        Get list of available models.

        Returns:
            List of model names
        """
        raise NotImplementedError(f"{self.__class__.__name__} must implement get_available_models()")

    def get_default_model(self) -> str:
        """
        Get default model for this provider.

        Returns:
            Default model name
        """
        models = self.get_available_models()
        return models[0] if models else ""

    async def validate_api_key(self) -> bool:
        """
        Validate API key.

        Returns:
            True if API key is valid, False otherwise
        """
        try:
            # Try a simple generation request
            await self.generate(
                prompt="A simple red circle",
                size="256x256",
                n=1
            )
            return True
        except Exception:
            return False

    def get_provider_name(self) -> str:
        """
        Get provider name.

        Returns:
            Provider name as string
        """
        return self.__class__.__name__.replace("Model", "").replace("Image", "").lower()

    def parse_size(self, size: str) -> tuple:
        """
        Parse size string to width and height.

        Args:
            size: Size string (e.g., "1024x1024")

        Returns:
            Tuple of (width, height)
        """
        try:
            width, height = size.lower().split("x")
            return (int(width), int(height))
        except (ValueError, AttributeError):
            raise ValueError(f"Invalid size format: {size}")

    async def download_image(self, url: str) -> bytes:
        """
        Download image from URL.

        Args:
            url: Image URL

        Returns:
            Image data as bytes
        """
        import httpx

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.content


__all__ = ["BaseImageModel"]
