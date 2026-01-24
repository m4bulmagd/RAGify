"""
Vector search service for pgvector.

Provides similarity search functionality using the configured distance metric
and properly utilizing the vector index via SQLAlchemy ORM.
"""

from typing import List, Optional, Tuple, Callable
from uuid import UUID
from sqlmodel import Session, select
from sqlalchemy import func
import logging

from app.models.chunk import Chunk
from app.models.document import Document
from app.core.config import get_vector_config
from app.core.vector_config import DistanceMetric

logger = logging.getLogger(__name__)


class VectorSearchService:
    """
    Service for performing vector similarity search on chunks.

    Uses the configured distance metric and properly utilizes pgvector indexes
    via SQLAlchemy ORM integration.
    """

    def __init__(self, session: Session):
        """
        Initialize the vector search service.

        Args:
            session: Database session (sync or async)
        """
        self.session = session
        self._vector_config = None

    @property
    def vector_config(self):
        """Lazy load vector configuration."""
        if self._vector_config is None:
            self._vector_config = get_vector_config()
        return self._vector_config

    def _get_distance_func(self, query_embedding: List[float]) -> Callable:
        """
        Get the appropriate distance function based on configured metric.

        Args:
            query_embedding: The query embedding vector

        Returns:
            A callable that computes distance from the embedding column
        """
        distance_metric = self.vector_config.distance_metric

        if distance_metric == DistanceMetric.COSINE:
            return Chunk.embedding.cosine_distance(query_embedding)
        elif distance_metric == DistanceMetric.L2:
            return Chunk.embedding.l2_distance(query_embedding)
        elif distance_metric == DistanceMetric.INNER_PRODUCT:
            return Chunk.embedding.max_inner_product(query_embedding)
        else:
            # Default to cosine
            return Chunk.embedding.cosine_distance(query_embedding)

    def similarity_search(
        self,
        query_embedding: List[float],
        limit: int = 10,
        threshold: Optional[float] = None,
        document_ids: Optional[List[UUID]] = None,
        project_id: Optional[UUID] = None,
    ) -> List[Tuple[Chunk, float]]:
        """
        Perform similarity search on chunks.

        Args:
            query_embedding: The query embedding vector
            limit: Maximum number of results to return
            threshold: Optional similarity threshold (0-1 for cosine)
            document_ids: Optional list of document IDs to filter by
            project_id: Optional project ID to filter by

        Returns:
            List of (Chunk, distance) tuples, sorted by distance (ascending)
        """
        distance_metric = self.vector_config.distance_metric
        distance_expr = self._get_distance_func(query_embedding)

        # Build base query with distance calculation
        statement = select(Chunk, distance_expr.label("distance")).where(
            Chunk.embedding.is_not(None)
        )

        # Apply document filter
        if document_ids:
            statement = statement.where(Chunk.document_id.in_(document_ids))

        # Apply project filter (requires join with documents)
        if project_id:
            statement = statement.join(Document).where(
                Document.project_id == project_id
            )

        # Apply threshold filter
        if threshold is not None:
            if distance_metric == DistanceMetric.COSINE:
                # For cosine, distance is 1 - similarity
                # So if threshold is 0.7 similarity, distance should be <= 0.3
                distance_threshold = 1.0 - threshold
                statement = statement.where(distance_expr <= distance_threshold)
            elif distance_metric == DistanceMetric.L2:
                # For L2, lower distance is better
                statement = statement.where(distance_expr <= threshold)
            elif distance_metric == DistanceMetric.INNER_PRODUCT:
                # For inner product (negative), lower is better
                statement = statement.where(distance_expr <= -threshold)

        # Order by distance (ascending) and limit
        statement = statement.order_by(distance_expr.asc()).limit(limit)

        # Execute query
        result = self.session.execute(statement)
        rows = result.all()

        # Parse results
        chunks_with_scores = [(row.Chunk, row.distance) for row in rows]

        logger.info(
            f"Found {len(chunks_with_scores)} chunks using {distance_metric.value} distance"
        )

        return chunks_with_scores

    def distance_to_similarity(self, distance: float) -> float:
        """
        Convert distance to similarity score (0-1).

        The conversion depends on the distance metric being used.

        Args:
            distance: The raw distance value from pgvector

        Returns:
            Similarity score between 0 and 1
        """
        distance_metric = self.vector_config.distance_metric

        if distance_metric == DistanceMetric.COSINE:
            # Cosine distance = 1 - cosine_similarity
            # So similarity = 1 - distance
            return max(0.0, min(1.0, 1.0 - distance))

        elif distance_metric == DistanceMetric.L2:
            # L2 distance is unbounded, use exponential decay
            import math

            return math.exp(-distance)

        elif distance_metric == DistanceMetric.INNER_PRODUCT:
            # pgvector uses negative inner product
            import math

            return 1 / (1 + math.exp(distance))

        return 0.0

    def similarity_search_with_scores(
        self,
        query_embedding: List[float],
        limit: int = 10,
        threshold: Optional[float] = None,
        document_ids: Optional[List[UUID]] = None,
        project_id: Optional[UUID] = None,
    ) -> List[Tuple[Chunk, float]]:
        """
        Perform similarity search and return normalized similarity scores.

        This is a convenience wrapper around similarity_search that converts
        distances to similarity scores.

        Args:
            query_embedding: The query embedding vector
            limit: Maximum number of results to return
            threshold: Optional similarity threshold (0-1)
            document_ids: Optional list of document IDs to filter by
            project_id: Optional project ID to filter by

        Returns:
            List of (Chunk, similarity_score) tuples, sorted by score (descending)
        """
        results = self.similarity_search(
            query_embedding=query_embedding,
            limit=limit,
            threshold=threshold,
            document_ids=document_ids,
            project_id=project_id,
        )

        # Convert distances to similarity scores
        scored_results = [
            (chunk, self.distance_to_similarity(distance))
            for chunk, distance in results
        ]

        # Sort by similarity score descending (highest first)
        scored_results.sort(key=lambda x: x[1], reverse=True)

        return scored_results
