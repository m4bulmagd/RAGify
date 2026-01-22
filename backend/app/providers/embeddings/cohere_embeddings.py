"""
Cohere embedding provider.

Implements EmbeddingProvider interface using Cohere API.
Handles Cohere-specific input types internally without exposing them.
"""

from typing import List
import logging

import cohere
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import settings
from app.core.interfaces.embedding import EmbeddingProvider


logger = logging.getLogger(__name__)


class CohereEmbeddingProvider(EmbeddingProvider):
    """
    Generates embeddings using Cohere API.

    Cohere-specific input types are handled internally:
    - search_document: Used for embed_documents (content to be indexed)
    - search_query: Used for embed_query (search queries)
    """

    DEFAULT_MODEL = "embed-english-v3.0"
    DEFAULT_DIMENSIONS = 1024
    MAX_BATCH_SIZE = 96  # Cohere's batch limit

    # Cohere-specific input types (internal implementation detail)
    _INPUT_TYPE_DOCUMENT = "search_document"
    _INPUT_TYPE_QUERY = "search_query"

    def __init__(
        self,
        model: str = DEFAULT_MODEL,
        dimensions: int | None = None,
        api_key: str | None = None,
    ):
        """
        Initialize Cohere embedding provider.

        Args:
            model: Cohere embedding model name
            dimensions: Optional embedding dimensions (model-dependent)
            api_key: Optional API key override, defaults to settings.COHERE_API_KEY
        """
        self._model = model
        self._dimensions = dimensions or self.DEFAULT_DIMENSIONS
        self._client = cohere.ClientV2(api_key=api_key or settings.COHERE_API_KEY)

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
        Generate embeddings for documents using search_document input type.

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
            embeddings = self._embed_batch(batch, self._INPUT_TYPE_DOCUMENT)
            all_embeddings.extend(embeddings)

        return all_embeddings

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    def embed_query(self, text: str) -> List[float]:
        """
        Generate embedding for a query using search_query input type.

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

        embeddings = self._embed_batch([text], self._INPUT_TYPE_QUERY)
        return embeddings[0]

    def _embed_batch(self, texts: List[str], input_type: str) -> List[List[float]]:
        """
        Embed a batch of texts with the specified input type.

        Args:
            texts: List of texts to embed
            input_type: Cohere input type (search_document or search_query)

        Returns:
            List of embedding vectors
        """
        try:
            logger.debug(
                f"Generating {input_type} embeddings for {len(texts)} texts "
                f"using model {self._model}"
            )

            response = self._client.embed(
                model=self._model,
                texts=texts,
                input_type=input_type,
                embedding_types=["float"],
            )

            # V2 API returns embeddings directly
            return [list(emb) for emb in response.embeddings.float_]

        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            raise RuntimeError(f"Failed to generate embeddings: {e}") from e
