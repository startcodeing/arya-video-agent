"""Unit tests for LLM providers."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.models.llm.openai import OpenAILLM
from openai import AsyncOpenAI


@pytest.fixture
def mock_openai_client():
    """Create a mock OpenAI client."""
    client = AsyncMock(spec=AsyncOpenAI)

    # Mock chat completions
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "Generated text response"
    mock_response.usage.total_tokens = 100

    client.chat.completions.create = AsyncMock(return_value=mock_response)
    return client


@pytest.fixture
def mock_openai_client_stream():
    """Create a mock OpenAI client for streaming."""
    client = AsyncMock(spec=AsyncOpenAI)

    # Create mock stream chunks
    chunks = [
        MagicMock(choices=[MagicMock(delta=MagicMock(content="Hello"))]),
        MagicMock(choices=[MagicMock(delta=MagicMock(content=" world"))]),
        MagicMock(choices=[MagicMock(delta=MagicMock(content="!"))]),
        MagicMock(choices=[MagicMock(delta=MagicMock(content=None))]),
    ]

    async def mock_stream(*args, **kwargs):
        for chunk in chunks:
            yield chunk

    client.chat.completions.create = mock_stream
    return client


class TestOpenAILLM:
    """Test suite for OpenAI LLM provider."""

    def test_initialization_with_api_key(self):
        """Test initialization with API key."""
        with patch('app.models.llm.openai.settings') as mock_settings:
            mock_settings.OPENAI_API_KEY = "test-api-key"
            mock_settings.DEFAULT_LLM_MODEL = "gpt-4"

            llm = OpenAILLM(api_key="custom-key")

            assert llm.api_key == "custom-key"
            assert llm._client is not None

    def test_initialization_requires_api_key(self):
        """Test that initialization raises error without API key."""
        with patch('app.models.llm.openai.settings') as mock_settings:
            mock_settings.OPENAI_API_KEY = None

            with pytest.raises(ValueError, match="OpenAI API key is required"):
                OpenAILLM()

    def test_initialization_from_settings(self):
        """Test initialization using API key from settings."""
        with patch('app.models.llm.openai.settings') as mock_settings:
            mock_settings.OPENAI_API_KEY = "settings-api-key"

            llm = OpenAILLM()

            assert llm.api_key == "settings-api-key"

    @pytest.mark.asyncio
    async def test_generate(self, mock_openai_client):
        """Test text generation."""
        with patch('app.models.llm.openai.settings') as mock_settings:
            mock_settings.OPENAI_API_KEY = "test-key"
            mock_settings.DEFAULT_LLM_MODEL = "gpt-4"

            llm = OpenAILLM()
            llm._client = mock_openai_client

            result = await llm.generate(
                prompt="Test prompt",
                model="gpt-4",
                temperature=0.7,
                max_tokens=1000
            )

            assert result == "Generated text response"
            mock_openai_client.chat.completions.create.assert_called_once()

            # Verify call arguments
            call_args = mock_openai_client.chat.completions.create.call_args
            assert call_args[1]["model"] == "gpt-4"
            assert call_args[1]["temperature"] == 0.7
            assert call_args[1]["max_tokens"] == 1000

    @pytest.mark.asyncio
    async def test_generate_with_default_model(self, mock_openai_client):
        """Test generation with default model."""
        with patch('app.models.llm.openai.settings') as mock_settings:
            mock_settings.OPENAI_API_KEY = "test-key"
            mock_settings.DEFAULT_LLM_MODEL = "gpt-4-turbo"

            llm = OpenAILLM()
            llm._client = mock_openai_client

            result = await llm.generate(prompt="Test")

            assert result == "Generated text response"

    @pytest.mark.asyncio
    async def test_generate_with_history(self, mock_openai_client):
        """Test generation with conversation history."""
        with patch('app.models.llm.openai.settings') as mock_settings:
            mock_settings.OPENAI_API_KEY = "test-key"
            mock_settings.DEFAULT_LLM_MODEL = "gpt-4"

            llm = OpenAILLM()
            llm._client = mock_openai_client

            messages = [
                {"role": "system", "content": "You are a helpful assistant"},
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi there!"},
                {"role": "user", "content": "How are you?"}
            ]

            result = await llm.generate_with_history(
                messages=messages,
                model="gpt-4"
            )

            assert result == "Generated text response"

            # Verify messages were passed
            call_args = mock_openai_client.chat.completions.create.call_args
            assert call_args[1]["messages"] == messages

    @pytest.mark.asyncio
    async def test_generate_structured(self, mock_openai_client):
        """Test structured JSON generation."""
        # Mock JSON response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = '{"key": "value", "number": 42}'

        mock_openai_client.chat.completions.create = AsyncMock(return_value=mock_response)

        with patch('app.models.llm.openai.settings') as mock_settings:
            mock_settings.OPENAI_API_KEY = "test-key"
            mock_settings.DEFAULT_LLM_MODEL = "gpt-4"

            llm = OpenAILLM()
            llm._client = mock_openai_client

            schema = {
                "type": "object",
                "properties": {
                    "key": {"type": "string"},
                    "number": {"type": "integer"}
                }
            }

            result = await llm.generate_structured(
                prompt="Generate JSON",
                schema=schema
            )

            assert result["key"] == "value"
            assert result["number"] == 42

            # Verify JSON format was requested
            call_args = mock_openai_client.chat.completions.create.call_args
            assert call_args[1]["response_format"] == {"type": "json_object"}

    @pytest.mark.asyncio
    async def test_generate_structured_invalid_json(self, mock_openai_client):
        """Test structured generation with invalid JSON response."""
        # Mock invalid JSON response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "This is not JSON"

        mock_openai_client.chat.completions.create = AsyncMock(return_value=mock_response)

        with patch('app.models.llm.openai.settings') as mock_settings:
            mock_settings.OPENAI_API_KEY = "test-key"
            mock_settings.DEFAULT_LLM_MODEL = "gpt-4"

            llm = OpenAILLM()
            llm._client = mock_openai_client

            with pytest.raises(ValueError, match="Failed to parse JSON response"):
                await llm.generate_structured(prompt="Generate JSON")

    @pytest.mark.asyncio
    async def test_stream_generate(self, mock_openai_client_stream):
        """Test streaming generation."""
        with patch('app.models.llm.openai.settings') as mock_settings:
            mock_settings.OPENAI_API_KEY = "test-key"
            mock_settings.DEFAULT_LLM_MODEL = "gpt-4"

            llm = OpenAILLM()
            llm._client = mock_openai_client_stream

            chunks = []
            async for chunk in llm.stream_generate(prompt="Test"):
                chunks.append(chunk)

            assert "Hello" in chunks
            assert " world" in chunks
            assert "!" in chunks

    @pytest.mark.asyncio
    async def test_count_tokens_with_tiktoken(self):
        """Test token counting with tiktoken."""
        with patch('app.models.llm.openai.settings') as mock_settings:
            mock_settings.OPENAI_API_KEY = "test-key"
            mock_settings.DEFAULT_LLM_MODEL = "gpt-4"

            llm = OpenAILLM()

            # Mock tiktoken
            with patch('app.models.llm.openai.tiktoken') as mock_tiktoken:
                mock_encoding = MagicMock()
                mock_encoding.encode.return_value = [1, 2, 3, 4, 5]
                mock_tiktoken.encoding_for_model.return_value = mock_encoding

                count = await llm.count_tokens("Test text", model="gpt-4")

                assert count == 5
                mock_tiktoken.encoding_for_model.assert_called_once_with("gpt-4")

    @pytest.mark.asyncio
    async def test_count_tokens_fallback(self):
        """Test token counting fallback when tiktoken is not available."""
        with patch('app.models.llm.openai.settings') as mock_settings:
            mock_settings.OPENAI_API_KEY = "test-key"
            mock_settings.DEFAULT_LLM_MODEL = "gpt-4"

            llm = OpenAILLM()

            # Mock ImportError for tiktoken
            with patch('app.models.llm.openai.tiktoken', side_effect=ImportError):
                count = await llm.count_tokens("Test text that is longer")

                # Should use rough estimate (1 token ≈ 4 chars)
                assert count == len("Test text that is longer") // 4

    def test_get_available_models(self):
        """Test getting available models."""
        with patch('app.models.llm.openai.settings') as mock_settings:
            mock_settings.OPENAI_API_KEY = "test-key"

            llm = OpenAILLM()

            models = llm.get_available_models()

            assert "gpt-4" in models
            assert "gpt-4-turbo" in models
            assert "gpt-3.5-turbo" in models

    def test_get_default_model(self):
        """Test getting default model."""
        with patch('app.models.llm.openai.settings') as mock_settings:
            mock_settings.OPENAI_API_KEY = "test-key"
            mock_settings.DEFAULT_LLM_MODEL = "gpt-4-turbo"

            llm = OpenAILLM()

            assert llm.get_default_model() == "gpt-4-turbo"

    def test_get_default_model_from_settings(self):
        """Test getting default model from settings."""
        with patch('app.models.llm.openai.settings') as mock_settings:
            mock_settings.OPENAI_API_KEY = "test-key"
            mock_settings.DEFAULT_LLM_MODEL = None

            llm = OpenAILLM()

            assert llm.get_default_model() == "gpt-4"  # Hardcoded default

    @pytest.mark.asyncio
    async def test_validate_api_key_success(self, mock_openai_client):
        """Test API key validation on success."""
        with patch('app.models.llm.openai.settings') as mock_settings:
            mock_settings.OPENAI_API_KEY = "test-key"
            mock_settings.DEFAULT_LLM_MODEL = "gpt-4"

            llm = OpenAILLM()
            llm._client = mock_openai_client

            result = await llm.validate_api_key()

            assert result is True

    @pytest.mark.asyncio
    async def test_validate_api_key_failure(self, mock_openai_client):
        """Test API key validation on failure."""
        # Mock authentication error
        mock_openai_client.chat.completions.create = AsyncMock(
            side_effect=Exception("Invalid API key")
        )

        with patch('app.models.llm.openai.settings') as mock_settings:
            mock_settings.OPENAI_API_KEY = "test-key"
            mock_settings.DEFAULT_LLM_MODEL = "gpt-4"

            llm = OpenAILLM()
            llm._client = mock_openai_client

            result = await llm.validate_api_key()

            assert result is False

    def test_get_provider_name(self):
        """Test getting provider name."""
        with patch('app.models.llm.openai.settings') as mock_settings:
            mock_settings.OPENAI_API_KEY = "test-key"

            llm = OpenAILLM()

            assert llm.get_provider_name() == "openai"


__all__ = ["TestOpenAILLM"]
