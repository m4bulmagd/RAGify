"""
Exceptions for embedding generation/processing.
"""


class EmbeddingGenerationError(Exception):
    """Base exception for embedding generation errors."""

    pass


class ChunkNotFoundError(EmbeddingGenerationError):
    """Raised when chunks are not found. Should NOT be retried."""

    pass


class EmbeddingProviderError(EmbeddingGenerationError):
    """Raised when embedding provider fails. Should be retried."""

    pass


class VectorStoreError(EmbeddingGenerationError):
    """Raised when vector store operations fail. Should be retried."""

    pass
