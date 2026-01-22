"""
OpenAI embedding provider.

Implements EmbeddingProvider interface using OpenAI API.
"""

from typing import List
import logging

from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import settings
from app.core.interfaces.embedding import EmbeddingProvider


logger = logging.getLogger(__name__)


class OpenAIEmbeddingProvider(EmbeddingProvider):
    """
    Generates embeddings using OpenAI API.

    OpenAI's embedding models don't require different modes for
    documents vs queries - the same embedding works for both.
    However, we implement both methods for interface consistency.
    """

    DEFAULT_MODEL = "text-embedding-3-small"
    DEFAULT_DIMENSIONS = 1536
    MAX_BATCH_SIZE = 1500  # OpenAI supports large batches

    def __init__(
        self,
        model: str = DEFAULT_MODEL,
        dimensions: int = DEFAULT_DIMENSIONS,
        api_key: str | None = None,
    ):
        """
        Initialize OpenAI embedding provider.

        Args:
            model: OpenAI embedding model name
            dimensions: Embedding dimensions
            api_key: Optional API key override, defaults to settings.OPENAI_API_KEY
        """
        self._model = model
        self._dimensions = dimensions
        self._client = OpenAI(api_key=api_key or settings.OPENAI_API_KEY)

    @property
    def model_name(self) -> str:
        """Return the model name being used."""
        return self._model

    @property
    def dimensions(self) -> int:
        """Return the embedding dimensions."""
        return self._dimensions

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for documents.

        Args:
            texts: List of document text strings to embed

        Returns:
            List of embedding vectors

        Raises:
            ValueError: If texts is empty
            RuntimeError: If the API call fails after retries
        """
        if not texts:
            return []

        all_embeddings = []

        for i in range(0, len(texts), self.MAX_BATCH_SIZE):
            batch = texts[i : i + self.MAX_BATCH_SIZE]
            embeddings = self._embed_batch(batch)
            all_embeddings.extend(embeddings)

        return all_embeddings

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    def embed_query(self, text: str) -> List[float]:
        """
        Generate embedding for a query.

        Args:
            text: Query text to embed

        Returns:
            Embedding vector

        Raises:
            ValueError: If text is empty
            RuntimeError: If the API call fails after retries
        """
        if not text or not text.strip():
            raise ValueError("Query text cannot be empty")

        embeddings = self._embed_batch([text])
        return embeddings[0]

    def _embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Embed a batch of texts.

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors
        """
        try:
            logger.debug(
                f"Generating embeddings for {len(texts)} texts "
                f"using model {self._model}"
            )

            response = self._client.embeddings.create(
                model=self._model,
                input=texts,
                dimensions=self._dimensions,
            )

            # Sort by index to ensure correct order
            sorted_data = sorted(response.data, key=lambda x: x.index)
            return [item.embedding for item in sorted_data]

        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            raise RuntimeError(f"Failed to generate embeddings: {e}") from e
