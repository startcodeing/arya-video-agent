"""OpenAI LLM provider implementation."""

from typing import Any, Dict, List, Optional

from openai import AsyncOpenAI

from app.config import settings
from app.models.llm.base import BaseLLM
from app.utils.logger import get_logger

logger = get_logger(__name__)


class OpenAILLM(BaseLLM):
    """OpenAI LLM provider implementation."""

    # Available models
    AVAILABLE_MODELS = [
        "gpt-4",
        "gpt-4-turbo",
        "gpt-4-turbo-preview",
        "gpt-3.5-turbo",
        "gpt-3.5-turbo-16k",
    ]

    def __init__(self, api_key: str = None):
        """
        Initialize OpenAI LLM provider.

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
        logger.info("OpenAI LLM client initialized")

    async def generate(
        self,
        prompt: str,
        model: str = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs
    ) -> str:
        """
        Generate text from prompt using OpenAI.

        Args:
            prompt: The input prompt
            model: Model to use (default: gpt-4)
            temperature: Sampling temperature (0.0 to 2.0)
            max_tokens: Maximum tokens to generate
            **kwargs: Additional OpenAI parameters

        Returns:
            Generated text as string
        """
        model = model or self.get_default_model()

        try:
            response = await self._client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )

            content = response.choices[0].message.content
            logger.info(f"OpenAI generation completed: model={model}, tokens={response.usage.total_tokens}")

            return content

        except Exception as e:
            logger.error(f"OpenAI generation failed: {e}")
            raise

    async def generate_with_history(
        self,
        messages: List[Dict[str, str]],
        model: str = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs
    ) -> str:
        """
        Generate text from conversation history.

        Args:
            messages: List of message dicts with 'role' and 'content'
            model: Model to use
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Additional parameters

        Returns:
            Generated text as string
        """
        model = model or self.get_default_model()

        try:
            response = await self._client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )

            content = response.choices[0].message.content
            return content

        except Exception as e:
            logger.error(f"OpenAI generation with history failed: {e}")
            raise

    async def generate_structured(
        self,
        prompt: str,
        schema: Dict[str, Any] = None,
        model: str = None,
        temperature: float = 0.7,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate structured JSON output.

        Args:
            prompt: The input prompt
            schema: Expected output schema
            model: Model to use
            temperature: Sampling temperature
            **kwargs: Additional parameters

        Returns:
            Structured output as dict
        """
        model = model or self.get_default_model()

        # Add JSON format instruction to prompt
        json_instruction = "\n\nRespond only with valid JSON in the following format:\n"
        if schema:
            import json
            json_instruction += json.dumps(schema, indent=2)

        enhanced_prompt = prompt + json_instruction

        try:
            response = await self._client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "user", "content": enhanced_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=temperature,
                **kwargs
            )

            content = response.choices[0].message.content

            import json
            return json.loads(content)

        except Exception as e:
            logger.error(f"OpenAI structured generation failed: {e}")
            raise

    async def count_tokens(self, text: str, model: str = None) -> int:
        """
        Count tokens using tiktoken.

        Args:
            text: Text to count tokens in
            model: Model to use for tokenization

        Returns:
            Token count
        """
        try:
            import tiktoken

            model = model or self.get_default_model()
            encoding = tiktoken.encoding_for_model(model)
            return len(encoding.encode(text))

        except ImportError:
            logger.warning("tiktoken not installed, using rough estimate")
            return len(text) // 4
        except Exception as e:
            logger.error(f"Token counting failed: {e}")
            return len(text) // 4

    def get_available_models(self) -> List[str]:
        """Get list of available OpenAI models."""
        return self.AVAILABLE_MODELS

    def get_default_model(self) -> str:
        """Get default model."""
        return settings.DEFAULT_LLM_MODEL or "gpt-4"

    async def stream_generate(
        self,
        prompt: str,
        model: str = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs
    ):
        """
        Generate text with streaming.

        Args:
            prompt: The input prompt
            model: Model to use
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Additional parameters

        Yields:
            Text chunks as they are generated
        """
        model = model or self.get_default_model()

        try:
            stream = await self._client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True,
                **kwargs
            )

            async for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    yield chunk.choices[0].delta.content

        except Exception as e:
            logger.error(f"OpenAI streaming generation failed: {e}")
            raise


__all__ = ["OpenAILLM"]
