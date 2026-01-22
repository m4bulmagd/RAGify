"""
Embedding factory.

Factory pattern for creating embedding providers.
"""

from enum import Enum
from typing import Optional
import logging

from app.core.interfaces.embedding import EmbeddingProvider


logger = logging.getLogger(__name__)


class EmbeddingProviderType(str, Enum):
    """Supported embedding provider types."""

    GEMINI = "gemini"
    OPENAI = "openai"
    COHERE = "cohere"


class EmbeddingFactory:
    """
    Factory for creating embedding providers.

    Usage:
        provider = EmbeddingFactory.create("gemini")
        embeddings = provider.embed_documents(texts)
        query_embedding = provider.embed_query(query)
    """

    _default_provider: EmbeddingProviderType = EmbeddingProviderType.GEMINI

    @classmethod
    def create(
        cls,
        provider_type: Optional[str] = None,
        **kwargs,
    ) -> EmbeddingProvider:
        """
        Create an embedding provider instance.

        Args:
            provider_type: Type of provider ("gemini", "openai", "cohere")
                          If None, uses the default provider
            **kwargs: Additional arguments passed to the provider constructor

        Returns:
            EmbeddingProvider instance

        Raises:
            ValueError: If provider type is not supported
        """
        if provider_type is None:
            provider_type = cls._default_provider.value

        provider_type = provider_type.lower()

        if provider_type == EmbeddingProviderType.GEMINI.value:
            from app.providers.embeddings.gemini_embeddings import (
                GeminiEmbeddingProvider,
            )

            return GeminiEmbeddingProvider(**kwargs)

        elif provider_type == EmbeddingProviderType.OPENAI.value:
            from app.providers.embeddings.openai_embeddings import (
                OpenAIEmbeddingProvider,
            )

            return OpenAIEmbeddingProvider(**kwargs)

        elif provider_type == EmbeddingProviderType.COHERE.value:
            from app.providers.embeddings.cohere_embeddings import (
                CohereEmbeddingProvider,
            )

            return CohereEmbeddingProvider(**kwargs)

        else:
            raise ValueError(
                f"Unsupported embedding provider: {provider_type}. "
                f"Supported providers: {[p.value for p in EmbeddingProviderType]}"
            )

    @classmethod
    def set_default_provider(cls, provider_type: EmbeddingProviderType) -> None:
        """
        Set the default embedding provider.

        Args:
            provider_type: Provider type to use as default
        """
        cls._default_provider = provider_type
        logger.info(f"Default embedding provider set to: {provider_type.value}")

    @classmethod
    def get_default_provider(cls) -> EmbeddingProviderType:
        """Get the current default provider type."""
        return cls._default_provider
