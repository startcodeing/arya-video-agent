"""Unit tests for ModelManager."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.models.manager import ModelManager, model_manager


@pytest.fixture
def mock_settings():
    """Mock settings with API keys."""
    with patch('app.models.manager.settings') as mock:
        mock.OPENAI_API_KEY = "test-openai-key"
        mock.RUNWAY_API_KEY = "test-runway-key"
        mock.DEFAULT_LLM_MODEL = "gpt-4"
        mock.DEFAULT_IMAGE_MODEL = "dall-e-3"
        mock.DEFAULT_VIDEO_MODEL = "runway-gen3"
        yield mock


class TestModelManager:
    """Test suite for ModelManager."""

    def test_initialization(self, mock_settings):
        """Test ModelManager initialization."""
        manager = ModelManager()

        # Check that providers were initialized
        assert "openai" in manager._llm_providers
        assert "openai" in manager._image_providers
        assert "runway" in manager._video_providers

    def test_initialization_without_openai_key(self):
        """Test initialization without OpenAI API key."""
        with patch('app.models.manager.settings') as mock_settings:
            mock_settings.OPENAI_API_KEY = None
            mock_settings.RUNWAY_API_KEY = None

            manager = ModelManager()

            # Should only have mock runway provider
            assert len(manager._llm_providers) == 0
            assert len(manager._image_providers) == 0
            assert "runway" in manager._video_providers

    def test_get_llm_provider_success(self, mock_settings):
        """Test getting LLM provider."""
        manager = ModelManager()

        provider = manager.get_llm_provider("openai")

        assert provider is not None
        assert provider.__class__.__name__ == "OpenAILLM"

    def test_get_llm_provider_default(self, mock_settings):
        """Test getting LLM provider with default."""
        manager = ModelManager()

        provider = manager.get_llm_provider()

        assert provider is not None
        assert provider.__class__.__name__ == "OpenAILLM"

    def test_get_llm_provider_not_found(self, mock_settings):
        """Test getting non-existent LLM provider."""
        manager = ModelManager()

        with pytest.raises(ValueError, match="Unknown LLM provider"):
            manager.get_llm_provider("nonexistent")

    def test_get_image_provider_success(self, mock_settings):
        """Test getting image provider."""
        manager = ModelManager()

        provider = manager.get_image_provider("openai")

        assert provider is not None
        assert provider.__class__.__name__ == "DALLEImageModel"

    def test_get_image_provider_default(self, mock_settings):
        """Test getting image provider with default."""
        manager = ModelManager()

        provider = manager.get_image_provider()

        assert provider is not None
        assert provider.__class__.__name__ == "DALLEImageModel"

    def test_get_image_provider_not_found(self, mock_settings):
        """Test getting non-existent image provider."""
        manager = ModelManager()

        with pytest.raises(ValueError, match="Unknown image provider"):
            manager.get_image_provider("nonexistent")

    def test_get_video_provider_success(self, mock_settings):
        """Test getting video provider."""
        manager = ModelManager()

        provider = manager.get_video_provider("runway")

        assert provider is not None
        assert provider.__class__.__name__ == "RunwayVideoModelMock"

    def test_get_video_provider_default(self, mock_settings):
        """Test getting video provider with default."""
        manager = ModelManager()

        provider = manager.get_video_provider()

        assert provider is not None
        assert provider.__class__.__name__ == "RunwayVideoModelMock"

    def test_get_video_provider_not_found(self, mock_settings):
        """Test getting non-existent video provider."""
        manager = ModelManager()

        with pytest.raises(ValueError, match="Unknown video provider"):
            manager.get_video_provider("nonexistent")

    def test_get_llm_model(self, mock_settings):
        """Test getting LLM model."""
        manager = ModelManager()

        model = manager.get_llm_model()

        assert model is not None
        assert model.__class__.__name__ == "OpenAILLM"

    def test_get_llm_model_with_provider(self, mock_settings):
        """Test getting LLM model with specific provider."""
        manager = ModelManager()

        model = manager.get_llm_model(provider="openai")

        assert model is not None

    def test_get_image_model(self, mock_settings):
        """Test getting image model."""
        manager = ModelManager()

        model = manager.get_image_model()

        assert model is not None
        assert model.__class__.__name__ == "DALLEImageModel"

    def test_get_video_model(self, mock_settings):
        """Test getting video model."""
        manager = ModelManager()

        model = manager.get_video_model()

        assert model is not None
        assert model.__class__.__name__ == "RunwayVideoModelMock"

    def test_list_available_providers(self, mock_settings):
        """Test listing all available providers."""
        manager = ModelManager()

        providers = manager.list_available_providers()

        assert "llm" in providers
        assert "image" in providers
        assert "video" in providers

        assert "openai" in providers["llm"]
        assert "openai" in providers["image"]
        assert "runway" in providers["video"]

    def test_list_available_providers_empty(self):
        """Test listing providers when none are initialized."""
        with patch('app.models.manager.settings') as mock_settings:
            mock_settings.OPENAI_API_KEY = None
            mock_settings.RUNWAY_API_KEY = None

            manager = ModelManager()
            providers = manager.list_available_providers()

            assert len(providers["llm"]) == 0
            assert len(providers["image"]) == 0
            assert "runway" in providers["video"]  # Mock doesn't need API key

    @pytest.mark.asyncio
    async def test_test_all_providers(self, mock_settings):
        """Test testing all providers."""
        manager = ModelManager()

        # Mock validate_api_key methods
        for provider in manager._llm_providers.values():
            provider.validate_api_key = AsyncMock(return_value=True)

        for provider in manager._image_providers.values():
            provider.validate_api_key = AsyncMock(return_value=True)

        for provider in manager._video_providers.values():
            provider.validate_api_key = AsyncMock(return_value=True)

        results = await manager.test_all_providers()

        assert "llm" in results
        assert "image" in results
        assert "video" in results

        assert results["llm"]["openai"] is True
        assert results["image"]["openai"] is True
        assert results["video"]["runway"] is True

    @pytest.mark.asyncio
    async def test_test_all_providers_with_failures(self, mock_settings):
        """Test testing all providers when some fail."""
        manager = ModelManager()

        # Mock validate_api_key with mixed results
        manager._llm_providers["openai"].validate_api_key = AsyncMock(return_value=True)
        manager._image_providers["openai"].validate_api_key = AsyncMock(return_value=False)
        manager._video_providers["runway"].validate_api_key = AsyncMock(
            side_effect=Exception("Connection error")
        )

        results = await manager.test_all_providers()

        assert results["llm"]["openai"] is True
        assert results["image"]["openai"] is False
        assert results["video"]["runway"] is False

    @pytest.mark.asyncio
    async def test_test_all_providers_empty(self):
        """Test testing providers when none are configured."""
        with patch('app.models.manager.settings') as mock_settings:
            mock_settings.OPENAI_API_KEY = None
            mock_settings.RUNWAY_API_KEY = None

            manager = ModelManager()
            results = await manager.test_all_providers()

            assert len(results["llm"]) == 0
            assert len(results["image"]) == 0
            assert results["video"]["runway"] is True  # Mock always returns True


class TestGlobalModelManager:
    """Test suite for global model_manager instance."""

    def test_global_manager_exists(self):
        """Test that global model_manager instance exists."""
        assert model_manager is not None
        assert isinstance(model_manager, ModelManager)

    def test_global_manager_usable(self):
        """Test that global manager can be used."""
        # This should not raise an error
        providers = model_manager.list_available_providers()

        assert isinstance(providers, dict)
        assert "llm" in providers
        assert "image" in providers
        assert "video" in providers


__all__ = ["TestModelManager", "TestGlobalModelManager"]
