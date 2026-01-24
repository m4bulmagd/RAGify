"""
Embedding generation service.

Encapsulates business logic for generating and storing embeddings.
"""

from typing import Any, Dict, List, Optional
import logging

from app.services.processing.exceptions import (
    ChunkNotFoundError,
    EmbeddingGenerationError,
    EmbeddingProviderError,
    VectorStoreError,
)
from app.core.config import settings

logger = logging.getLogger(__name__)


class EmbeddingGenerationService:
    """
    Service for generating and storing embeddings.

    Encapsulates business logic separate from Celery tasks.
    Follows the service layer pattern for testability and reusability.
    """

    DEFAULT_PROVIDER = "gemini"

    def __init__(
        self,
        session,
        embedding_provider_name: Optional[str] = None,
    ):
        """
        Initialize the embedding generation service.

        Args:
            session: Database session
            embedding_provider_name: Name of the embedding provider to use
        """
        self.session = session
        self.embedding_provider_name = embedding_provider_name or self.DEFAULT_PROVIDER
        self._embedding_provider = None

    @property
    def embedding_provider(self):
        """Lazy initialization of embedding provider."""
        if self._embedding_provider is None:
            from app.factories.embedding_factory import EmbeddingFactory

            self._embedding_provider = EmbeddingFactory.create(
                self.embedding_provider_name
            )
        return self._embedding_provider

    def fetch_chunks(self, chunk_ids: List[int]):
        """
        Fetch chunks from database.

        Args:
            chunk_ids: List of chunk IDs

        Returns:
            List of Chunk objects

        Raises:
            ChunkNotFoundError: If no chunks found
        """
        from app.models.chunk import Chunk
        from sqlmodel import select

        statement = select(Chunk).where(Chunk.id.in_(chunk_ids))
        result = self.session.execute(statement)
        chunks = list(result.scalars().all())

        if not chunks:
            raise ChunkNotFoundError(f"No chunks found for IDs: {chunk_ids}")

        logger.info(f"Fetched {len(chunks)} chunks from database")
        return chunks

    def fetch_document(self, document_id: int):
        """
        Fetch document from database.

        Args:
            document_id: Document ID

        Returns:
            Document object

        Raises:
            ValueError: If document not found
        """
        from app.models.document import Document
        from sqlmodel import select

        statement = select(Document).where(Document.id == document_id)
        document = self.session.execute(statement).scalar_one_or_none()

        if not document:
            raise ValueError(f"Document {document_id} not found")

        return document

    def get_chunks_needing_embeddings(self, chunk_ids: List[int]):
        """
        Get chunks that need embeddings.

        Args:
            chunk_ids: List of chunk IDs

        Returns:
            List of Chunk objects
        """
        from app.models.chunk import Chunk
        from sqlmodel import select

        # Get chunks that need embeddings
        statement = select(Chunk).where(
            Chunk.id.in_(chunk_ids), Chunk.embedding.is_(None)
        )
        result = self.session.execute(statement)
        needs_embedding = list(result.scalars().all())

        return needs_embedding

    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for texts.

        Args:
            texts: List of text strings

        Returns:
            List of embedding vectors

        Raises:
            EmbeddingProviderError: If embedding generation fails
        """
        try:
            embeddings = self.embedding_provider.embed_documents(texts)
            logger.info(f"Generated {len(embeddings)} embeddings")
            return embeddings
        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            raise EmbeddingProviderError(f"Failed to generate embeddings: {e}") from e

    def save_embeddings_to_postgres(self, chunks, embeddings) -> None:
        """
        Save embeddings to PostgreSQL (pgvector).

        Args:
            chunks: List of Chunk objects
            embeddings: List of embedding vectors
        """
        from app.models.chunk import Chunk

        # Create update mappings
        mappings = [
            {"id": chunk.id, "embedding": embedding}
            for chunk, embedding in zip(chunks, embeddings)
        ]

        # Bulk update
        self.session.bulk_update_mappings(Chunk, mappings)

        logger.info(f"Saved {len(chunks)} embeddings to PostgreSQL")

    def update_document_status(
        self,
        document_id: int,
        status,
        error_message: Optional[str] = None,
    ) -> None:
        """
        Update document status and notify user.

        Args:
            document_id: Document ID
            status: DocumentStatus enum value
            error_message: Optional error message
        """
        document = self.fetch_document(document_id)
        document.status = status

        if error_message:
            document.error_message = error_message

        self.session.add(document)
        self.session.commit()

        # Notify user (non-blocking)
        self._send_notification(document_id, status, error_message)

        logger.info(f"Updated document {document_id} status to {status.value}")

    def _send_notification(
        self,
        document_id: int,
        status,
        error_message: Optional[str] = None,
    ) -> None:
        """Send notification about document status. Failures are logged but not raised."""
        try:
            from app.services.notification import NotificationService

            notification_service = NotificationService()
            message = error_message or "Processing complete"
            notification_service.notify_document_status(
                document_id, status, message=message
            )
        except Exception as e:
            # Don't fail the task if notification fails
            logger.warning(
                f"Failed to send notification for document {document_id}: {e}"
            )

    def process_chunks(self, chunk_ids: List[int]) -> Dict[str, Any]:
        """
        Main processing logic for generating embeddings.

        This method is idempotent - safe to retry without side effects.

        Args:
            chunk_ids: List of chunk IDs

        Returns:
            dict with processing results
        """
        from app.models.document import DocumentStatus

        # Filter chunks that need processing (idempotency)
        chunks_to_process = self.get_chunks_needing_embeddings(chunk_ids)

        if not chunks_to_process:
            logger.info("All chunks already have embeddings, skipping")
            return {
                "status": "completed",
                "chunks_processed": 0,
            }

        # Get document for project context
        document_id = chunks_to_process[0].document_id
        document = self.fetch_document(document_id)

        try:
            # Generate embeddings
            texts = [chunk.text for chunk in chunks_to_process]
            embeddings = self.generate_embeddings(texts)

            # Save to PostgreSQL
            self.save_embeddings_to_postgres(chunks_to_process, embeddings)

            # Commit transaction (all or nothing)
            self.session.commit()

            # Update document status to COMPLETED
            self.update_document_status(document_id, DocumentStatus.COMPLETED)

            return {
                "status": "completed",
                "chunks_processed": len(chunks_to_process),
                "document_id": document_id,
            }

        except (EmbeddingProviderError, VectorStoreError):
            # These errors should be retried - rollback and re-raise
            self.session.rollback()
            raise

        except Exception as e:
            # Unexpected errors - rollback, mark failed, and wrap
            self.session.rollback()
            logger.exception(f"Unexpected error processing chunks: {e}")

            try:
                self.update_document_status(
                    document_id,
                    DocumentStatus.FAILED,
                    error_message=f"Embedding generation failed: {e}",
                )
            except Exception as status_error:
                logger.error(f"Failed to update document status: {status_error}")

            raise EmbeddingGenerationError(f"Unexpected error: {e}") from e
