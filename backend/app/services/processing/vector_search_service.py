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

    async def similarity_search(
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
        # Apply project filter
        if project_id:
            statement = statement.where(
                Chunk.project_id == project_id
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

        # Eager load document relationship to avoid MissingGreenlet
        from sqlalchemy.orm import selectinload

        statement = statement.options(selectinload(Chunk.document))

        # Execute query
        result = await self.session.execute(statement)
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

    async def similarity_search_with_scores(
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
        results = await self.similarity_search(
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

    async def keyword_search(
        self,
        query_text: str,
        limit: int = 10,
        document_ids: Optional[List[UUID]] = None,
        project_id: Optional[UUID] = None,
    ) -> List[Tuple[Chunk, float]]:
        """
        Perform keyword search using Postgres Full Text Search.

        Args:
            query_text: The search query string
            limit: Maximum number of results to return
            document_ids: Optional list of document IDs to filter by
            project_id: Optional project ID to filter by

        Returns:
            List of (Chunk, rank_score) tuples, sorted by score (descending)
        """
        # Prepare TS Query (simple 'plain' parsing for now to handle special chars)
        # websearch_to_tsquery is often better for user input
        ts_query = func.websearch_to_tsquery("english", query_text)
        rank = func.ts_rank(Chunk.content_vector, ts_query)

        statement = select(Chunk, rank.label("rank")).where(
            Chunk.content_vector.op("@@")(ts_query)
        )

        if document_ids:
            statement = statement.where(Chunk.document_id.in_(document_ids))

        # Apply project filter
        if project_id:
            statement = statement.where(
                Chunk.project_id == project_id
            )

        statement = statement.order_by(rank.desc()).limit(limit)

        # Eager load document
        from sqlalchemy.orm import selectinload

        statement = statement.options(selectinload(Chunk.document))

        result = await self.session.execute(statement)
        rows = result.all()

        return [(row.Chunk, row.rank) for row in rows]

    def reciprocal_rank_fusion(
        self,
        vector_results: List[Tuple[Chunk, float]],
        keyword_results: List[Tuple[Chunk, float]],
        k: int = 60,
    ) -> List[Tuple[Chunk, float]]:
        """
        Combine vector and keyword results using Reciprocal Rank Fusion (RRF).

        Args:
            vector_results: List of (Chunk, score) from vector search
            keyword_results: List of (Chunk, score) from keyword search
            k: RRF constant (default 60)

        Returns:
            Combined list of (Chunk, rrf_score) sorted by score
        """
        scores = {}

        # Vector Ranks
        for rank, (chunk, _) in enumerate(vector_results):
            if chunk.id not in scores:
                scores[chunk.id] = {"chunk": chunk, "score": 0.0}
            scores[chunk.id]["score"] += 1.0 / (k + rank + 1)

        # Keyword Ranks
        for rank, (chunk, _) in enumerate(keyword_results):
            if chunk.id not in scores:
                scores[chunk.id] = {"chunk": chunk, "score": 0.0}
            scores[chunk.id]["score"] += 1.0 / (k + rank + 1)

        sorted_scores = sorted(
            scores.values(), key=lambda x: x["score"], reverse=True
        )
        return [(item["chunk"], item["score"]) for item in sorted_scores]

    async def hybrid_search(
        self,
        query_embedding: List[float],
        query_text: str,
        limit: int = 10,
        vector_limit: Optional[int] = None,
        keyword_limit: Optional[int] = None,
        threshold: Optional[float] = None,
        document_ids: Optional[List[UUID]] = None,
        project_id: Optional[UUID] = None,
    ) -> List[Tuple[Chunk, float]]:
        """
        Perform hybrid search (Vector + Keyword) using RRF.

        Args:
            query_embedding: Query vector
            query_text: Query text string
            limit: Final number of results to return
            vector_limit: How many vector results to fetch (default: limit * 2)
            keyword_limit: How many keyword results to fetch (default: limit * 2)
            ... filters ...

        Returns:
            Merged list of chunks
        """
        # Fetch more candidates than final limit for better fusion
        v_limit = vector_limit or (limit * 2)
        k_limit = keyword_limit or (limit * 2)

        # Run both searches in parallel (ideally)
        # For simplicity in this async context without asyncio.gather overhead on session:
        # (SQLAlchemy async session isn't thread-safe for parallel queries on same session)
        
        vector_results = await self.similarity_search_with_scores(
            query_embedding=query_embedding,
            limit=v_limit,
            threshold=threshold,
            document_ids=document_ids,
            project_id=project_id,
        )

        keyword_results = await self.keyword_search(
            query_text=query_text,
            limit=k_limit,
            document_ids=document_ids,
            project_id=project_id,
        )

        # Fuse
        merged = self.reciprocal_rank_fusion(vector_results, keyword_results)
        
        # Clip to limit
        return merged[:limit]
