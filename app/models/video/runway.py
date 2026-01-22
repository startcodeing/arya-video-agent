"""Runway video generation provider implementation (Mock)."""

import asyncio
import time
from typing import Any, Dict, List
import uuid

from app.config import settings
from app.models.video.base import BaseVideoModel
from app.utils.logger import get_logger

logger = get_logger(__name__)


class RunwayVideoModelMock(BaseVideoModel):
    """
    Mock Runway video generation provider.

    This is a mock implementation for development and testing.
    It simulates video generation without calling the actual Runway API.
    """

    # Mock available models
    AVAILABLE_MODELS = [
        "runway-gen3",
        "runway-gen2",
    ]

    def __init__(self, api_key: str = None):
        """
        Initialize mock Runway provider.

        Args:
            api_key: Runway API key (not used in mock)
        """
        self.api_key = api_key or settings.RUNWAY_API_KEY

        # Mock doesn't need a real client
        self._client = "mock_client"

        logger.info("Runway video model MOCK provider initialized")

    def _initialize_client(self) -> None:
        """Initialize mock client."""
        # Mock client - no actual API calls
        pass

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
        Mock generate video.

        Simulates video generation with a delay.

        Args:
            prompt: Text description of the desired video
            model: Model to use
            duration: Video duration in seconds
            aspect_ratio: Aspect ratio
            image_url: URL of first frame (not used in mock)
            **kwargs: Additional parameters

        Returns:
            Dict containing mock video information
        """
        model = model or settings.DEFAULT_VIDEO_MODEL or "runway-gen3"

        logger.info(f"Mock video generation started: model={model}, duration={duration}s")

        # Simulate generation delay based on duration
        delay = min(duration, 10)  # Max 10 seconds delay
        await asyncio.sleep(delay)

        # Generate mock video ID and URL
        video_id = f"mock_video_{uuid.uuid4().hex[:8]}"
        mock_url = f"https://mock.runway.ml/videos/{video_id}.mp4"

        logger.info(f"Mock video generation completed: id={video_id}")

        return {
            "id": video_id,
            "url": mock_url,
            "status": "completed",
            "model": model,
            "duration": duration,
            "aspect_ratio": aspect_ratio,
        }

    async def get_generation_status(
        self,
        generation_id: str
    ) -> Dict[str, any]:
        """
        Mock check generation status.

        Args:
            generation_id: ID of the generation request

        Returns:
            Dict containing status information
        """
        # Mock always returns completed
        return {
            "id": generation_id,
            "status": "completed",
            "url": f"https://mock.runway.ml/videos/{generation_id}.mp4",
            "progress": 100,
        }

    def get_available_durations(self) -> List[int]:
        """Get list of available video durations."""
        return [5, 10]

    def get_available_ratios(self) -> List[str]:
        """Get list of available aspect ratios."""
        return ["16:9", "9:16", "1:1"]

    def get_available_models(self) -> List[str]:
        """Get list of available models."""
        return self.AVAILABLE_MODELS

    def get_default_model(self) -> str:
        """Get default model."""
        return settings.DEFAULT_VIDEO_MODEL or "runway-gen3"

    async def validate_api_key(self) -> bool:
        """
        Mock validate API key.

        Returns:
            Always True for mock
        """
        return True


__all__ = ["RunwayVideoModelMock"]
