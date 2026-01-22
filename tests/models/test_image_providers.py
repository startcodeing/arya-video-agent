"""Unit tests for Image generation providers."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.models.image.openai import DALLEImageModel
from openai import AsyncOpenAI


@pytest.fixture
def mock_openai_client():
    """Create a mock OpenAI client."""
    client = AsyncMock(spec=AsyncOpenAI)

    # Mock image generation response
    mock_response = MagicMock()
    mock_image = MagicMock()
    mock_image.url = "https://example.com/generated-image.png"
    mock_image.revised_prompt = "A beautiful sunset over mountains"

    mock_response.data = [mock_image]
    client.images.generate = AsyncMock(return_value=mock_response)
    client.images.create_variation = AsyncMock(return_value=mock_response)

    return client


class TestDALLEImageModel:
    """Test suite for DALL-E image generation provider."""

    def test_initialization_with_api_key(self):
        """Test initialization with API key."""
        with patch('app.models.image.openai.settings') as mock_settings:
            mock_settings.OPENAI_API_KEY = "test-api-key"
            mock_settings.DEFAULT_IMAGE_MODEL = "dall-e-3"

            model = DALLEImageModel(api_key="custom-key")

            assert model.api_key == "custom-key"
            assert model._client is not None

    def test_initialization_requires_api_key(self):
        """Test that initialization raises error without API key."""
        with patch('app.models.image.openai.settings') as mock_settings:
            mock_settings.OPENAI_API_KEY = None

            with pytest.raises(ValueError, match="OpenAI API key is required"):
                DALLEImageModel()

    def test_initialization_from_settings(self):
        """Test initialization using API key from settings."""
        with patch('app.models.image.openai.settings') as mock_settings:
            mock_settings.OPENAI_API_KEY = "settings-api-key"

            model = DALLEImageModel()

            assert model.api_key == "settings-api-key"

    @pytest.mark.asyncio
    async def test_generate_dalle3(self, mock_openai_client):
        """Test DALL-E 3 image generation."""
        with patch('app.models.image.openai.settings') as mock_settings:
            mock_settings.OPENAI_API_KEY = "test-key"
            mock_settings.DEFAULT_IMAGE_MODEL = "dall-e-3"

            model = DALLEImageModel()
            model._client = mock_openai_client

            result = await model.generate(
                prompt="A beautiful sunset",
                size="1024x1024",
                n=1,
                quality="standard",
                style="vivid"
            )

            assert result["url"] == "https://example.com/generated-image.png"
            assert result["revised_prompt"] == "A beautiful sunset over mountains"
            assert len(result["urls"]) == 1

            mock_openai_client.images.generate.assert_called_once()

            # Verify call parameters
            call_args = mock_openai_client.images.generate.call_args
            assert call_args[1]["model"] == "dall-e-3"
            assert call_args[1]["size"] == "1024x1024"
            assert call_args[1]["quality"] == "standard"
            assert call_args[1]["style"] == "vivid"

    @pytest.mark.asyncio
    async def test_generate_dalle3_hd_quality(self, mock_openai_client):
        """Test DALL-E 3 with HD quality."""
        with patch('app.models.image.openai.settings') as mock_settings:
            mock_settings.OPENAI_API_KEY = "test-key"
            mock_settings.DEFAULT_IMAGE_MODEL = "dall-e-3"

            model = DALLEImageModel()
            model._client = mock_openai_client

            result = await model.generate(
                prompt="A detailed landscape",
                size="1792x1024",
                quality="hd"
            )

            assert result["url"] == "https://example.com/generated-image.png"

            call_args = mock_openai_client.images.generate.call_args
            assert call_args[1]["quality"] == "hd"
            assert call_args[1]["size"] == "1792x1024"

    @pytest.mark.asyncio
    async def test_generate_dalle2(self, mock_openai_client):
        """Test DALL-E 2 image generation."""
        with patch('app.models.image.openai.settings') as mock_settings:
            mock_settings.OPENAI_API_KEY = "test-key"
            mock_settings.DEFAULT_IMAGE_MODEL = "dall-e-2"

            model = DALLEImageModel()
            model._client = mock_openai_client

            result = await model.generate(
                prompt="A cat sitting on a table",
                model="dall-e-2",
                size="512x512"
            )

            assert result["url"] == "https://example.com/generated-image.png"

            call_args = mock_openai_client.images.generate.call_args
            assert call_args[1]["model"] == "dall-e-2"
            assert call_args[1]["size"] == "512x512"
            # DALL-E 2 should not have quality parameter
            assert "quality" not in call_args[1]

    @pytest.mark.asyncio
    async def test_generate_multiple_images(self, mock_openai_client):
        """Test generating multiple images."""
        # Mock response with multiple images
        mock_response = MagicMock()
        mock_images = [
            MagicMock(url="https://example.com/image1.png"),
            MagicMock(url="https://example.com/image2.png"),
        ]
        mock_response.data = mock_images

        mock_openai_client.images.generate = AsyncMock(return_value=mock_response)

        with patch('app.models.image.openai.settings') as mock_settings:
            mock_settings.OPENAI_API_KEY = "test-key"
            mock_settings.DEFAULT_IMAGE_MODEL = "dall-e-3"

            model = DALLEImageModel()
            model._client = mock_openai_client

            result = await model.generate(
                prompt="Generate variations",
                n=2
            )

            assert len(result["urls"]) == 2
            assert result["urls"][0] == "https://example.com/image1.png"
            assert result["urls"][1] == "https://example.com/image2.png"

    @pytest.mark.asyncio
    async def test_generate_dalle3_invalid_size(self, mock_openai_client):
        """Test DALL-E 3 with invalid size."""
        with patch('app.models.image.openai.settings') as mock_settings:
            mock_settings.OPENAI_API_KEY = "test-key"
            mock_settings.DEFAULT_IMAGE_MODEL = "dall-e-3"

            model = DALLEImageModel()
            model._client = mock_openai_client

            with pytest.raises(ValueError, match="DALL-E 3 only supports sizes"):
                await model.generate(
                    prompt="Test",
                    model="dall-e-3",
                    size="512x512"  # Invalid for DALL-E 3
                )

    @pytest.mark.asyncio
    async def test_generate_dalle3_invalid_quality(self, mock_openai_client):
        """Test DALL-E 3 with invalid quality."""
        with patch('app.models.image.openai.settings') as mock_settings:
            mock_settings.OPENAI_API_KEY = "test-key"
            mock_settings.DEFAULT_IMAGE_MODEL = "dall-e-3"

            model = DALLEImageModel()
            model._client = mock_openai_client

            with pytest.raises(ValueError, match="Quality must be one of"):
                await model.generate(
                    prompt="Test",
                    model="dall-e-3",
                    quality="ultra"  # Invalid quality
                )

    @pytest.mark.asyncio
    async def test_generate_dalle3_invalid_style(self, mock_openai_client):
        """Test DALL-E 3 with invalid style."""
        with patch('app.models.image.openai.settings') as mock_settings:
            mock_settings.OPENAI_API_KEY = "test-key"
            mock_settings.DEFAULT_IMAGE_MODEL = "dall-e-3"

            model = DALLEImageModel()
            model._client = mock_openai_client

            with pytest.raises(ValueError, match="Style must be one of"):
                await model.generate(
                    prompt="Test",
                    model="dall-e-3",
                    style="artistic"  # Invalid style
                )

    @pytest.mark.asyncio
    async def test_generate_dalle2_invalid_size(self, mock_openai_client):
        """Test DALL-E 2 with invalid size."""
        with patch('app.models.image.openai.settings') as mock_settings:
            mock_settings.OPENAI_API_KEY = "test-key"
            mock_settings.DEFAULT_IMAGE_MODEL = "dall-e-2"

            model = DALLEImageModel()
            model._client = mock_openai_client

            with pytest.raises(ValueError, match="DALL-E 2 only supports sizes"):
                await model.generate(
                    prompt="Test",
                    model="dall-e-2",
                    size="1792x1024"  # Invalid for DALL-E 2
                )

    @pytest.mark.asyncio
    async def test_generate_from_image(self, mock_openai_client):
        """Test image-to-image generation."""
        with patch('app.models.image.openai.settings') as mock_settings:
            mock_settings.OPENAI_API_KEY = "test-key"
            mock_settings.DEFAULT_IMAGE_MODEL = "dall-e-2"

            model = DALLEImageModel()
            model._client = mock_openai_client

            result = await model.generate_from_image(
                prompt="Add more clouds",
                image_url="https://example.com/source-image.png",
                size="1024x1024",
                n=2
            )

            assert result["url"] == "https://example.com/generated-image.png"

            mock_openai_client.images.create_variation.assert_called_once()

            call_args = mock_openai_client.images.create_variation.call_args
            assert call_args[1]["size"] == "1024x1024"
            assert call_args[1]["n"] == 2

    def test_get_available_sizes(self):
        """Test getting available image sizes."""
        with patch('app.models.image.openai.settings') as mock_settings:
            mock_settings.OPENAI_API_KEY = "test-key"

            model = DALLEImageModel()

            sizes = model.get_available_sizes()

            assert "1024x1024" in sizes
            assert "1792x1024" in sizes
            assert "1024x1792" in sizes

    def test_get_available_styles(self):
        """Test getting available styles."""
        with patch('app.models.image.openai.settings') as mock_settings:
            mock_settings.OPENAI_API_KEY = "test-key"

            model = DALLEImageModel()

            styles = model.get_available_styles()

            assert "vivid" in styles
            assert "natural" in styles

    def test_get_available_models(self):
        """Test getting available models."""
        with patch('app.models.image.openai.settings') as mock_settings:
            mock_settings.OPENAI_API_KEY = "test-key"

            model = DALLEImageModel()

            models = model.get_available_models()

            assert "dall-e-3" in models
            assert "dall-e-2" in models

    def test_get_default_model(self):
        """Test getting default model."""
        with patch('app.models.image.openai.settings') as mock_settings:
            mock_settings.OPENAI_API_KEY = "test-key"
            mock_settings.DEFAULT_IMAGE_MODEL = "dall-e-3"

            model = DALLEImageModel()

            assert model.get_default_model() == "dall-e-3"

    def test_get_default_model_from_settings(self):
        """Test getting default model from settings."""
        with patch('app.models.image.openai.settings') as mock_settings:
            mock_settings.OPENAI_API_KEY = "test-key"
            mock_settings.DEFAULT_IMAGE_MODEL = None

            model = DALLEImageModel()

            assert model.get_default_model() == "dall-e-3"  # Hardcoded default

    def test_parse_size(self):
        """Test parsing size string."""
        with patch('app.models.image.openai.settings') as mock_settings:
            mock_settings.OPENAI_API_KEY = "test-key"

            model = DALLEImageModel()

            width, height = model.parse_size("1024x768")

            assert width == 1024
            assert height == 768

    def test_parse_size_invalid_format(self):
        """Test parsing invalid size format."""
        with patch('app.models.image.openai.settings') as mock_settings:
            mock_settings.OPENAI_API_KEY = "test-key"

            model = DALLEImageModel()

            with pytest.raises(ValueError, match="Invalid size format"):
                model.parse_size("invalid")

    @pytest.mark.asyncio
    async def test_download_image(self):
        """Test downloading image from URL."""
        with patch('app.models.image.openai.settings') as mock_settings:
            mock_settings.OPENAI_API_KEY = "test-key"

            model = DALLEImageModel()

            # Mock httpx client
            with patch('app.models.image.openai.httpx.AsyncClient') as mock_client_class:
                mock_response = MagicMock()
                mock_response.content = b"fake image data"
                mock_response.raise_for_status = MagicMock()

                mock_client = AsyncMock()
                mock_client.__aenter__.return_value = mock_client
                mock_client.__aexit__.return_value = None
                mock_client.get = AsyncMock(return_value=mock_response)
                mock_client_class.return_value = mock_client

                content = await model.download_image("https://example.com/image.png")

                assert content == b"fake image data"
                mock_client.get.assert_called_once_with("https://example.com/image.png")

    def test_get_provider_name(self):
        """Test getting provider name."""
        with patch('app.models.image.openai.settings') as mock_settings:
            mock_settings.OPENAI_API_KEY = "test-key"

            model = DALLEImageModel()

            assert model.get_provider_name() == "dalle"


__all__ = ["TestDALLEImageModel"]
