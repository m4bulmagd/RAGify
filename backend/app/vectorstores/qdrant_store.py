"""
Qdrant vector store implementation.

Manages vector storage and similarity search using Qdrant.
"""

from typing import List, Dict, Any, Optional
import logging

from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels
from qdrant_client.http.exceptions import UnexpectedResponse

from app.core.config import settings
from app.models.chunk import Chunk


logger = logging.getLogger(__name__)


class QdrantStore:
    """
    Qdrant vector database operations.
    """

    def __init__(self):
        """Initialize Qdrant client."""
        self.client = QdrantClient(
            host=settings.QDRANT_HOST,
            port=settings.QDRANT_PORT,
            api_key=settings.QDRANT_API_KEY if settings.QDRANT_API_KEY else None,
        )
        self.vector_size = 1536  # OpenAI text-embedding-3-small

    def _get_collection_name(self, project_id: str) -> str:
        """
        Get collection name for a project.

        Using project ID as collection name for isolation.
        """
        return f"project_{project_id.replace('-', '_')}"

    def ensure_collection(self, project_id: str) -> None:
        """
        Ensure collection exists for project.

        Args:
            project_id: Project UUID as string
        """
        collection_name = self._get_collection_name(project_id)

        try:
            self.client.get_collection(collection_name)
            logger.debug(f"Collection {collection_name} already exists")
        except (UnexpectedResponse, Exception):
            # Collection doesn't exist, create it
            logger.info(f"Creating collection {collection_name}")
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=qmodels.VectorParams(
                    size=self.vector_size,
                    distance=qmodels.Distance.COSINE,
                ),
            )

    def upsert_chunks(
        self,
        project_id: str,
        chunks: List[Chunk],
        embeddings: List[List[float]],
    ) -> None:
        """
        Upsert chunks with embeddings to Qdrant.

        Args:
            project_id: Project UUID as string
            chunks: List of Chunk objects
            embeddings: List of embedding vectors
        """
        if not chunks or not embeddings:
            return

        if len(chunks) != len(embeddings):
            raise ValueError("Chunks and embeddings must have same length")

        # Ensure collection exists
        self.ensure_collection(project_id)

        collection_name = self._get_collection_name(project_id)

        # Prepare points
        points = []
        for chunk, embedding in zip(chunks, embeddings):
            point = qmodels.PointStruct(
                id=chunk.id,  # Use chunk ID as point ID
                vector=embedding,
                payload={
                    "chunk_id": chunk.id,
                    "document_id": str(chunk.document_id),
                    "text": chunk.text[:1000],  # Store truncated text for preview
                    "page_number": chunk.page_number,
                    "metadata": chunk.metadata_ or {},
                },
            )
            points.append(point)

        # Batch upsert
        batch_size = 100
        for i in range(0, len(points), batch_size):
            batch = points[i : i + batch_size]
            self.client.upsert(
                collection_name=collection_name,
                points=batch,
            )

        logger.info(f"Upserted {len(points)} points to {collection_name}")

    def search(
        self,
        project_id: str,
        query_embedding: List[float],
        top_k: int = 10,
        filter_conditions: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search for similar vectors.

        Args:
            project_id: Project UUID as string
            query_embedding: Query vector
            top_k: Number of results to return
            filter_conditions: Optional filters

        Returns:
            List of search results with scores and payloads
        """
        collection_name = self._get_collection_name(project_id)

        # Build filter if provided
        qdrant_filter = None
        if filter_conditions:
            must_conditions = []
            for key, value in filter_conditions.items():
                must_conditions.append(
                    qmodels.FieldCondition(
                        key=key,
                        match=qmodels.MatchValue(value=value),
                    )
                )
            qdrant_filter = qmodels.Filter(must=must_conditions)

        try:
            results = self.client.search(
                collection_name=collection_name,
                query_vector=query_embedding,
                limit=top_k,
                query_filter=qdrant_filter,
            )

            return [
                {
                    "id": result.id,
                    "score": result.score,
                    "payload": result.payload,
                }
                for result in results
            ]

        except Exception as e:
            logger.error(f"Qdrant search error: {e}")
            return []

    def delete_by_document(self, project_id: str, document_id: str) -> None:
        """
        Delete all vectors for a document.

        Args:
            project_id: Project UUID as string
            document_id: Document UUID as string
        """
        collection_name = self._get_collection_name(project_id)

        try:
            self.client.delete(
                collection_name=collection_name,
                points_selector=qmodels.FilterSelector(
                    filter=qmodels.Filter(
                        must=[
                            qmodels.FieldCondition(
                                key="document_id",
                                match=qmodels.MatchValue(value=document_id),
                            )
                        ]
                    )
                ),
            )
            logger.info(f"Deleted vectors for document {document_id}")
        except Exception as e:
            logger.error(f"Error deleting vectors: {e}")

    def delete_collection(self, project_id: str) -> None:
        """
        Delete entire collection for a project.

        Args:
            project_id: Project UUID as string
        """
        collection_name = self._get_collection_name(project_id)

        try:
            self.client.delete_collection(collection_name)
            logger.info(f"Deleted collection {collection_name}")
        except Exception as e:
            logger.error(f"Error deleting collection: {e}")
