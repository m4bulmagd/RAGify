from abc import ABC, abstractmethod
from typing import AsyncGenerator, Optional, Dict, Any, List


class BaseLLM(ABC):
    """
    Abstract base class for LLM providers.
    """

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        **kwargs: Any
    ) -> str:
        """
        Generate a response from the LLM.

        Args:
            prompt: The user prompt
            system_prompt: Optional system prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Additional provider-specific arguments

        Returns:
            The generated text response
        """
        pass

    @abstractmethod
    async def generate_stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        **kwargs: Any
    ) -> AsyncGenerator[str, None]:
        """
        Stream a response from the LLM.

        Args:
            prompt: The user prompt
            system_prompt: Optional system prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Additional provider-specific arguments

        Returns:
            An async generator yielding chunks of text
        """

    @staticmethod
    @abstractmethod
    def supported_models() -> List[Dict[str, Any]]:
        """
        Get list of supported models for this provider.

        Returns:
            List of dictionaries containing model metadata (id, name, description, etc.)
        """
        pass
