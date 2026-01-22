"""
Gemini embedding provider.

Implements EmbeddingProvider interface using Google Gemini API.
Handles Gemini-specific task types internally without exposing them.
"""

from typing import List
import logging

from google import genai
from google.genai import types
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import settings
from app.core.interfaces.embedding import EmbeddingProvider


logger = logging.getLogger(__name__)


class GeminiEmbeddingProvider(EmbeddingProvider):
    """
    Generates embeddings using Google Gemini API.

    Gemini-specific task types are handled internally:
    - RETRIEVAL_DOCUMENT: Used for embed_documents (content to be indexed)
    - RETRIEVAL_QUERY: Used for embed_query (search queries)
    """

    DEFAULT_MODEL = "gemini-embedding-001"
    DEFAULT_DIMENSIONS = 1536
    MAX_BATCH_SIZE = 100

    # Gemini-specific task types (internal implementation detail)
    _TASK_TYPE_DOCUMENT = "RETRIEVAL_DOCUMENT"
    _TASK_TYPE_QUERY = "RETRIEVAL_QUERY"

    def __init__(
        self,
        model: str = DEFAULT_MODEL,
        dimensions: int = DEFAULT_DIMENSIONS,
        api_key: str | None = None,
    ):
        """
        Initialize Gemini embedding provider.

        Args:
            model: Gemini embedding model name
            dimensions: Embedding dimensions (max 768 for gemini-embedding-001)
            api_key: Optional API key override, defaults to settings.GOOGLE_API_KEY
        """
        self._model = model
        self._dimensions = dimensions
        self._client = genai.Client(api_key=api_key or settings.GOOGLE_API_KEY)

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
        Generate embeddings for documents using RETRIEVAL_DOCUMENT task type.

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
            logger.info(
                f"############ Generating {self._TASK_TYPE_DOCUMENT} embeddings for batch {i} to {i + self.MAX_BATCH_SIZE}"
            )
            batch = texts[i : i + self.MAX_BATCH_SIZE]
            embeddings = self._embed_batch(batch, self._TASK_TYPE_DOCUMENT)
            all_embeddings.extend(embeddings)

        return all_embeddings

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    def embed_query(self, text: str) -> List[float]:
        """
        Generate embedding for a query using RETRIEVAL_QUERY task type.

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

        embeddings = self._embed_batch([text], self._TASK_TYPE_QUERY)
        return embeddings[0]

    def _embed_batch(self, texts: List[str], task_type: str) -> List[List[float]]:
        """
        Embed a batch of texts with the specified task type.

        Args:
            texts: List of texts to embed
            task_type: Gemini task type (RETRIEVAL_DOCUMENT or RETRIEVAL_QUERY)

        Returns:
            List of embedding vectors
        """
        try:
            logger.debug(
                f"Generating {task_type} embeddings for {len(texts)} texts "
                f"using model {self._model}"
            )

            result = self._client.models.embed_content(
                model=self._model,
                contents=texts,
                config=types.EmbedContentConfig(
                    task_type=task_type,
                    output_dimensionality=self._dimensions,
                ),
            )

            return [embedding.values for embedding in result.embeddings]

        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            raise RuntimeError(f"Failed to generate embeddings: {e}") from e
