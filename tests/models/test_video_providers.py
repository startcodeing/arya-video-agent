"""Unit tests for Video generation providers."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.models.video.runway import RunwayVideoModelMock


class TestRunwayVideoModelMock:
    """Test suite for Runway video generation mock provider."""

    def test_initialization(self):
        """Test mock initialization."""
        with patch('app.models.video.runway.settings') as mock_settings:
            mock_settings.RUNWAY_API_KEY = None

            model = RunwayVideoModelMock()

            assert model._client == "mock_client"
            assert model.api_key is None

    def test_initialization_with_api_key(self):
        """Test initialization with API key (not used in mock)."""
        with patch('app.models.video.runway.settings') as mock_settings:
            mock_settings.RUNWAY_API_KEY = "test-key"

            model = RunwayVideoModelMock(api_key="custom-key")

            assert model.api_key == "custom-key"

    def test_initialization_from_settings(self):
        """Test initialization using API key from settings."""
        with patch('app.models.video.runway.settings') as mock_settings:
            mock_settings.RUNWAY_API_KEY = "settings-key"

            model = RunwayVideoModelMock()

            assert model.api_key == "settings-key"

    @pytest.mark.asyncio
    async def test_generate_video(self):
        """Test mock video generation."""
        with patch('app.models.video.runway.settings') as mock_settings:
            mock_settings.RUNWAY_API_KEY = None
            mock_settings.DEFAULT_VIDEO_MODEL = "runway-gen3"

            model = RunwayVideoModelMock()

            result = await model.generate(
                prompt="A beautiful sunset over mountains",
                duration=5,
                aspect_ratio="16:9"
            )

            assert result["status"] == "completed"
            assert "id" in result
            assert "url" in result
            assert result["model"] == "runway-gen3"
            assert result["duration"] == 5
            assert result["aspect_ratio"] == "16:9"

    @pytest.mark.asyncio
    async def test_generate_with_custom_model(self):
        """Test generation with custom model."""
        with patch('app.models.video.runway.settings') as mock_settings:
            mock_settings.RUNWAY_API_KEY = None

            model = RunwayVideoModelMock()

            result = await model.generate(
                prompt="Test video",
                model="runway-gen2",
                duration=10
            )

            assert result["model"] == "runway-gen2"
            assert result["duration"] == 10

    @pytest.mark.asyncio
    async def test_generate_with_image_url(self):
        """Test image-to-video generation."""
        with patch('app.models.video.runway.settings') as mock_settings:
            mock_settings.RUNWAY_API_KEY = None

            model = RunwayVideoModelMock()

            result = await model.generate(
                prompt="Make the image move",
                image_url="https://example.com/frame.png",
                duration=5
            )

            assert result["status"] == "completed"
            assert "url" in result

    @pytest.mark.asyncio
    async def test_generate_delay(self):
        """Test that generation has appropriate delay."""
        import time
        import asyncio

        with patch('app.models.video.runway.settings') as mock_settings:
            mock_settings.RUNWAY_API_KEY = None

            model = RunwayVideoModelMock()

            start = time.time()
            await model.generate(
                prompt="Test",
                duration=5  # Should result in 5 second delay
            )
            elapsed = time.time() - start

            # Should have delayed for approximately 5 seconds (with some tolerance)
            assert 4.5 < elapsed < 6.0

    @pytest.mark.asyncio
    async def test_generate_max_delay(self):
        """Test that delay is capped at 10 seconds."""
        import time

        with patch('app.models.video.runway.settings') as mock_settings:
            mock_settings.RUNWAY_API_KEY = None

            model = RunwayVideoModelMock()

            start = time.time()
            await model.generate(
                prompt="Test",
                duration=20  # Should be capped at 10 seconds
            )
            elapsed = time.time() - start

            # Should have delayed for approximately 10 seconds (capped)
            assert 9.5 < elapsed < 11.0

    @pytest.mark.asyncio
    async def test_get_generation_status(self):
        """Test getting generation status."""
        with patch('app.models.video.runway.settings') as mock_settings:
            mock_settings.RUNWAY_API_KEY = None

            model = RunwayVideoModelMock()

            status = await model.get_generation_status("test-generation-id")

            assert status["id"] == "test-generation-id"
            assert status["status"] == "completed"
            assert status["progress"] == 100
            assert "url" in status

    @pytest.mark.asyncio
    async def test_generate_from_image(self):
        """Test image-to-video generation using dedicated method."""
        with patch('app.models.video.runway.settings') as mock_settings:
            mock_settings.RUNWAY_API_KEY = None

            model = RunwayVideoModelMock()

            result = await model.generate_from_image(
                image_url="https://example.com/frame.png",
                prompt="Add motion to the image",
                duration=5,
                motion=7
            )

            assert result["status"] == "completed"
            assert "url" in result

    def test_get_available_durations(self):
        """Test getting available durations."""
        model = RunwayVideoModelMock()

        durations = model.get_available_durations()

        assert 5 in durations
        assert 10 in durations

    def test_get_available_ratios(self):
        """Test getting available aspect ratios."""
        model = RunwayVideoModelMock()

        ratios = model.get_available_ratios()

        assert "16:9" in ratios
        assert "9:16" in ratios
        assert "1:1" in ratios

    def test_get_available_models(self):
        """Test getting available models."""
        model = RunwayVideoModelMock()

        models = model.get_available_models()

        assert "runway-gen3" in models
        assert "runway-gen2" in models

    def test_get_default_model(self):
        """Test getting default model."""
        with patch('app.models.video.runway.settings') as mock_settings:
            mock_settings.RUNWAY_API_KEY = None
            mock_settings.DEFAULT_VIDEO_MODEL = "runway-gen3"

            model = RunwayVideoModelMock()

            assert model.get_default_model() == "runway-gen3"

    def test_get_default_model_from_settings(self):
        """Test getting default model from settings."""
        with patch('app.models.video.runway.settings') as mock_settings:
            mock_settings.RUNWAY_API_KEY = None
            mock_settings.DEFAULT_VIDEO_MODEL = None

            model = RunwayVideoModelMock()

            # Should use hardcoded default
            assert model.get_default_model() == "runway-gen3"

    @pytest.mark.asyncio
    async def test_validate_api_key(self):
        """Test API key validation (always returns True for mock)."""
        with patch('app.models.video.runway.settings') as mock_settings:
            mock_settings.RUNWAY_API_KEY = None

            model = RunwayVideoModelMock()

            result = await model.validate_api_key()

            assert result is True

    def test_get_provider_name(self):
        """Test getting provider name."""
        model = RunwayVideoModelMock()

        assert model.get_provider_name() == "runway"


class TestBaseVideoModel:
    """Test suite for BaseVideoModel abstract class."""

    def test_base_model_abstract_methods(self):
        """Test that base model requires abstract methods."""
        from app.models.video.base import BaseVideoModel

        # Try to instantiate without implementing abstract methods
        with pytest.raises(TypeError):
            BaseVideoModel()

    @pytest.mark.asyncio
    async def test_download_video(self):
        """Test downloading video from URL."""
        from app.models.video.base import BaseVideoModel

        # Create a concrete implementation for testing
        class TestVideoModel(BaseVideoModel):
            def __init__(self):
                self._client = "test_client"

            def _initialize_client(self):
                pass

            async def generate(self, prompt, model=None, duration=5, aspect_ratio="16:9", image_url=None, **kwargs):
                return {"id": "test", "url": "https://example.com/video.mp4"}

            def get_available_models(self):
                return ["test-model"]

        model = TestVideoModel()

        # Mock httpx client
        with patch('app.models.video.base.httpx.AsyncClient') as mock_client_class:
            mock_response = MagicMock()
            mock_response.content = b"fake video data"
            mock_response.raise_for_status = MagicMock()

            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client

            content = await model.download_video("https://example.com/video.mp4")

            assert content == b"fake video data"
            mock_client.get.assert_called_once_with("https://example.com/video.mp4")

    @pytest.mark.asyncio
    async def test_get_default_model_fallback(self):
        """Test default model fallback to first available."""
        from app.models.video.base import BaseVideoModel

        class TestVideoModel(BaseVideoModel):
            def __init__(self):
                self._client = "test_client"

            def _initialize_client(self):
                pass

            async def generate(self, prompt, model=None, duration=5, aspect_ratio="16:9", image_url=None, **kwargs):
                return {}

            def get_available_models(self):
                return ["model-1", "model-2"]

        model = TestVideoModel()
        default = model.get_default_model()

        assert default == "model-1"

    @pytest.mark.asyncio
    async def test_validate_api_key_default_implementation(self):
        """Test default validate_api_key implementation."""
        from app.models.video.base import BaseVideoModel

        class TestVideoModel(BaseVideoModel):
            def __init__(self):
                self._client = "test_client"

            def _initialize_client(self):
                pass

            async def generate(self, prompt, model=None, duration=5, aspect_ratio="16:9", image_url=None, **kwargs):
                return {"id": "test", "url": "https://example.com/video.mp4"}

            def get_available_models(self):
                return ["test-model"]

        model = TestVideoModel()

        # Should succeed
        result = await model.validate_api_key()
        assert result is True

    @pytest.mark.asyncio
    async def test_validate_api_key_on_failure(self):
        """Test validate_api_key when generation fails."""
        from app.models.video.base import BaseVideoModel

        class FailingVideoModel(BaseVideoModel):
            def __init__(self):
                self._client = "test_client"

            def _initialize_client(self):
                pass

            async def generate(self, prompt, model=None, duration=5, aspect_ratio="16:9", image_url=None, **kwargs):
                raise Exception("API key invalid")

            def get_available_models(self):
                return ["test-model"]

        model = FailingVideoModel()

        result = await model.validate_api_key()
        assert result is False


__all__ = ["TestRunwayVideoModelMock", "TestBaseVideoModel"]
