"""
Embedding provider interface.

Defines the abstract base class for all embedding providers.
This interface is provider-agnostic and should not contain any
provider-specific concepts (e.g., task types, input types).
"""

from abc import ABC, abstractmethod
from typing import List


class EmbeddingProvider(ABC):
    """
    Abstract base class for embedding providers.

    All embedding implementations (OpenAI, Gemini, Cohere, etc.)
    must implement this interface.

    The interface provides two methods:
    - embed_documents: For embedding documents/chunks to be stored
    - embed_query: For embedding search queries

    This separation allows providers to optimize embeddings based on
    the use case (e.g., Gemini uses different task types, Cohere uses
    different input types) without exposing these details in the interface.
    """

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Return the model name being used."""
        ...

    @property
    @abstractmethod
    def dimensions(self) -> int:
        """Return the embedding dimensions."""
        ...

    @abstractmethod
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for documents/chunks to be stored.

        This method is optimized for embedding content that will be
        indexed and searched against.

        Args:
            texts: List of document text strings to embed

        Returns:
            List of embedding vectors, one per input text

        Raises:
            ValueError: If texts is empty or contains invalid content
            RuntimeError: If the embedding API call fails
        """
        ...

    @abstractmethod
    def embed_query(self, text: str) -> List[float]:
        """
        Generate embedding for a search query.

        This method is optimized for embedding queries that will be
        used to search against stored document embeddings.

        Args:
            text: Query text to embed

        Returns:
            Embedding vector for the query

        Raises:
            ValueError: If text is empty
            RuntimeError: If the embedding API call fails
        """
        ...
