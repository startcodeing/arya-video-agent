"""Model manager for routing and managing model providers."""

from typing import Any, Dict, List, Optional

from app.config import settings
from app.models.llm.base import BaseLLM
from app.models.llm.openai import OpenAILLM
from app.models.image.base import BaseImageModel
from app.models.image.openai import DALLEImageModel
from app.models.video.base import BaseVideoModel
from app.models.video.runway import RunwayVideoModelMock
from app.utils.logger import get_logger

logger = get_logger(__name__)


class ModelManager:
    """
    Manager for model providers and routing.

    Handles:
    - Creating model instances
    - Routing requests to appropriate providers
    - Provider fallback strategies
    """

    def __init__(self):
        """Initialize model manager."""
        self._llm_providers: Dict[str, BaseLLM] = {}
        self._image_providers: Dict[str, BaseImageModel] = {}
        self._video_providers: Dict[str, BaseVideoModel] = {}

        # Initialize default providers
        self._initialize_providers()

    def _initialize_providers(self) -> None:
        """Initialize default model providers."""
        # Initialize LLM providers
        if settings.OPENAI_API_KEY:
            self._llm_providers["openai"] = OpenAILLM()
            logger.info("OpenAI LLM provider initialized")

        # Initialize image providers
        if settings.OPENAI_API_KEY:
            self._image_providers["openai"] = DALLEImageModel()
            logger.info("OpenAI (DALL-E) image provider initialized")

        # Initialize video providers
        if settings.RUNWAY_API_KEY or True:  # Mock doesn't need API key
            self._video_providers["runway"] = RunwayVideoModelMock()
            logger.info("Runway video provider initialized (mock)")

    def get_llm_provider(self, provider: str = "openai") -> BaseLLM:
        """
        Get LLM provider instance.

        Args:
            provider: Provider name (default: openai)

        Returns:
            LLM provider instance
        """
        if provider not in self._llm_providers:
            available = list(self._llm_providers.keys())
            raise ValueError(
                f"Unknown LLM provider: {provider}. "
                f"Available: {available}"
            )

        return self._llm_providers[provider]

    def get_image_provider(self, provider: str = "openai") -> BaseImageModel:
        """
        Get image provider instance.

        Args:
            provider: Provider name (default: openai)

        Returns:
            Image provider instance
        """
        if provider not in self._image_providers:
            available = list(self._image_providers.keys())
            raise ValueError(
                f"Unknown image provider: {provider}. "
                f"Available: {available}"
            )

        return self._image_providers[provider]

    def get_video_provider(self, provider: str = "runway") -> BaseVideoModel:
        """
        Get video provider instance.

        Args:
            provider: Provider name (default: runway)

        Returns:
            Video provider instance
        """
        if provider not in self._video_providers:
            available = list(self._video_providers.keys())
            raise ValueError(
                f"Unknown video provider: {provider}. "
                f"Available: {available}"
            )

        return self._video_providers[provider]

    def get_llm_model(
        self,
        model: str = None,
        provider: str = None
    ) -> BaseLLM:
        """
        Get LLM model instance with fallback.

        Args:
            model: Model name (optional)
            provider: Provider name (optional)

        Returns:
            LLM provider instance
        """
        # Use default provider if not specified
        if provider is None:
            provider = "openai"

        return self.get_llm_provider(provider)

    def get_image_model(
        self,
        model: str = None,
        provider: str = None
    ) -> BaseImageModel:
        """
        Get image model instance with fallback.

        Args:
            model: Model name (optional)
            provider: Provider name (optional)

        Returns:
            Image provider instance
        """
        # Use default provider if not specified
        if provider is None:
            provider = "openai"

        return self.get_image_provider(provider)

    def get_video_model(
        self,
        model: str = None,
        provider: str = None
    ) -> BaseVideoModel:
        """
        Get video model instance with fallback.

        Args:
            model: Model name (optional)
            provider: Provider name (optional)

        Returns:
            Video provider instance
        """
        # Use default provider if not specified
        if provider is None:
            provider = "runway"

        return self.get_video_provider(provider)

    def list_available_providers(self) -> Dict[str, List[str]]:
        """
        List all available providers by type.

        Returns:
            Dict with keys 'llm', 'image', 'video' and list of provider names
        """
        return {
            "llm": list(self._llm_providers.keys()),
            "image": list(self._image_providers.keys()),
            "video": list(self._video_providers.keys()),
        }

    async def test_all_providers(self) -> Dict[str, Dict[str, bool]]:
        """
        Test all provider API keys.

        Returns:
            Dict with test results for each provider
        """
        results = {
            "llm": {},
            "image": {},
            "video": {},
        }

        # Test LLM providers
        for name, provider in self._llm_providers.items():
            try:
                valid = await provider.validate_api_key()
                results["llm"][name] = valid
                logger.info(f"LLM provider {name}: {'Valid' if valid else 'Invalid'}")
            except Exception as e:
                results["llm"][name] = False
                logger.error(f"LLM provider {name} test failed: {e}")

        # Test image providers
        for name, provider in self._image_providers.items():
            try:
                valid = await provider.validate_api_key()
                results["image"][name] = valid
                logger.info(f"Image provider {name}: {'Valid' if valid else 'Invalid'}")
            except Exception as e:
                results["image"][name] = False
                logger.error(f"Image provider {name} test failed: {e}")

        # Test video providers
        for name, provider in self._video_providers.items():
            try:
                valid = await provider.validate_api_key()
                results["video"][name] = valid
                logger.info(f"Video provider {name}: {'Valid' if valid else 'Invalid'}")
            except Exception as e:
                results["video"][name] = False
                logger.error(f"Video provider {name} test failed: {e}")

        return results


# Global model manager instance
model_manager = ModelManager()


__all__ = ["ModelManager", "model_manager"]
