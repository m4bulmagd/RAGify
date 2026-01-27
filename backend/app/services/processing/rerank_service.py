"""
Reranking service.

Uses cross-encoders (via Cohere API) to re-score retrieved chunks 
based on their relevance to the query.
"""

import logging
from typing import List, Tuple, Optional
import cohere
from app.core.config import settings
from app.models.chunk import Chunk

logger = logging.getLogger(__name__)

class RerankService:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.COHERE_API_KEY
        self._client = None

    @property
    def client(self):
        if self._client is None and self.api_key:
            self._client = cohere.ClientV2(api_key=self.api_key)
        return self._client

    async def rerank(
        self, 
        query: str, 
        chunks: List[Chunk], 
        top_n: int = 3,
        model: str = "rerank-v3.5"
    ) -> List[Tuple[Chunk, float]]:
        """
        Rerank chunks using Cohere's Rerank API.
        
        Returns:
            List of (Chunk, relevance_score) sorted by score descending.
        """
        if not chunks:
            return []
        
        if not self.client:
            logger.warning("Cohere API key not configured. Skipping reranking.")
            return [(c, 0.0) for c in chunks[:top_n]]

        try:
            # Prepare documents for Cohere
            documents = [chunk.text for chunk in chunks]
            
            response = self.client.rerank(
                model=model,
                query=query,
                documents=documents,
                top_n=top_n,
            )

            reranked_results = []
            for result in response.results:
                chunk = chunks[result.index]
                reranked_results.append((chunk, result.relevance_score))

            logger.info(f"Reranked {len(chunks)} chunks down to {len(reranked_results)}")
            return reranked_results

        except Exception as e:
            logger.error(f"Reranking failed: {e}")
            # Fallback to original order if reranking fails
            return [(c, 1.0) for c in chunks[:top_n]]
