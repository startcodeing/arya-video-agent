"""Base class for LLM providers."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class BaseLLM(ABC):
    """
    Base class for all LLM (Large Language Model) providers.

    All LLM providers (OpenAI, Anthropic, etc.) should inherit from this class
    and implement the required methods.
    """

    def __init__(self, api_key: str = None):
        """
        Initialize the LLM provider.

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
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs
    ) -> str:
        """
        Generate text from a prompt.

        Args:
            prompt: The input prompt
            model: Model to use (provider-specific)
            temperature: Sampling temperature (0.0 to 2.0)
            max_tokens: Maximum tokens to generate
            **kwargs: Additional provider-specific parameters

        Returns:
            Generated text as string
        """
        raise NotImplementedError(f"{self.__class__.__name__} must implement generate()")

    @abstractmethod
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
            model: Model to use (provider-specific)
            temperature: Sampling temperature (0.0 to 2.0)
            max_tokens: Maximum tokens to generate
            **kwargs: Additional provider-specific parameters

        Returns:
            Generated text as string
        """
        raise NotImplementedError(f"{self.__class__.__name__} must implement generate_with_history()")

    async def generate_structured(
        self,
        prompt: str,
        schema: Dict[str, Any],
        model: str = None,
        temperature: float = 0.7,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate structured output (JSON).

        Args:
            prompt: The input prompt
            schema: Expected output schema
            model: Model to use
            temperature: Sampling temperature
            **kwargs: Additional parameters

        Returns:
            Structured output as dict
        """
        # Default implementation: generate and parse JSON
        text = await self.generate(
            prompt=prompt,
            model=model,
            temperature=temperature,
            **kwargs
        )

        import json
        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse JSON response: {e}")

    async def count_tokens(self, text: str, model: str = None) -> int:
        """
        Count tokens in text.

        Args:
            text: Text to count tokens in
            model: Model to use for tokenization

        Returns:
            Token count
        """
        # Default implementation: rough estimate (1 token ≈ 4 chars)
        return len(text) // 4

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
                prompt="Hello",
                max_tokens=5,
                temperature=0.0
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
        return self.__class__.__name__.replace("LLM", "").lower()

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
        # Default implementation: not streaming
        # Override in subclasses for streaming support
        result = await self.generate(
            prompt=prompt,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        )
        yield result


__all__ = ["BaseLLM"]
