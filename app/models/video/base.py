"""Base class for Video generation providers."""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional


class BaseVideoModel(ABC):
    """
    Base class for all video generation providers.

    All video generation providers (Runway, Pika, Stable Video, etc.) should
    inherit from this class and implement the required methods.
    """

    def __init__(self, api_key: str = None):
        """
        Initialize the video model provider.

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
        model: str = None,
        duration: int = 5,
        aspect_ratio: str = "16:9",
        image_url: str = None,
        **kwargs
    ) -> Dict[str, any]:
        """
        Generate video from text prompt.

        Args:
            prompt: Text description of the desired video
            model: Model to use
            duration: Video duration in seconds
            aspect_ratio: Aspect ratio (e.g., "16:9", "9:16", "1:1")
            image_url: URL of first frame (for image-to-video)
            **kwargs: Additional provider-specific parameters

        Returns:
            Dict containing:
                - url: URL of the generated video
                - id: Video ID
                - status: Generation status
        """
        raise NotImplementedError(f"{self.__class__.__name__} must implement generate()")

    async def generate_from_image(
        self,
        image_url: str,
        prompt: str,
        model: str = None,
        duration: int = 5,
        motion: int = 5,
        **kwargs
    ) -> Dict[str, any]:
        """
        Generate video from first frame image (image-to-video).

        Args:
            image_url: URL of the first frame
            prompt: Text description of the desired motion/video
            model: Model to use
            duration: Video duration in seconds
            motion: Amount of motion (1-10)
            **kwargs: Additional parameters

        Returns:
            Dict containing video information
        """
        # Default: use the generate method with image_url
        return await self.generate(
            prompt=prompt,
            model=model,
            duration=duration,
            image_url=image_url,
            **kwargs
        )

    async def get_generation_status(
        self,
        generation_id: str
    ) -> Dict[str, any]:
        """
        Check the status of a video generation request.

        Args:
            generation_id: ID of the generation request

        Returns:
            Dict containing:
                - id: Generation ID
                - status: Status (pending, processing, completed, failed)
                - url: Video URL if completed
                - error: Error message if failed
        """
        # Default: not implemented
        raise NotImplementedError(
            f"{self.__class__.__name__} does not support status checking"
        )

    async def download_video(self, url: str) -> bytes:
        """
        Download video from URL.

        Args:
            url: Video URL

        Returns:
            Video data as bytes
        """
        import httpx

        async with httpx.AsyncClient(timeout=300.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.content

    def get_available_durations(self) -> List[int]:
        """
        Get list of available video durations.

        Returns:
            List of supported durations in seconds
        """
        return [5, 10]

    def get_available_ratios(self) -> List[str]:
        """
        Get list of available aspect ratios.

        Returns:
            List of supported aspect ratios
        """
        return ["16:9", "9:16", "1:1"]

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
            # Try a simple generation request (may not be supported by all)
            await self.generate(
                prompt="A simple video",
                duration=5
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
        return self.__class__.__name__.replace("Model", "").replace("Video", "").lower()


__all__ = ["BaseVideoModel"]
