"""
Embedding generation Celery tasks.

Generates embeddings for document chunks and stores them
in PostgreSQL (pgvector) and Qdrant.
"""

from typing import List
from celery import shared_task
from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=300,
    retry_kwargs={"max_retries": 5},
    name="app.workers.embedding_generation.generate_embeddings_batch",
)
def generate_embeddings_batch(self, chunk_ids: List[int]) -> dict:
    """
    Generate embeddings for a batch of chunks.

    Args:
        chunk_ids: List of chunk IDs to generate embeddings for

    Returns:
        dict with processing results
    """
    from app.core.db import get_sync_session
    from app.models.chunk import Chunk
    from app.models.document import Document, DocumentStatus
    from app.services.processing.embedding_service import EmbeddingService
    from app.vectorstores.qdrant_store import QdrantStore
    from sqlmodel import select

    logger.info(f"Generating embeddings for {len(chunk_ids)} chunks")

    with get_sync_session() as session:
        # Fetch chunks
        statement = select(Chunk).where(Chunk.id.in_(chunk_ids))
        result = session.execute(statement)
        chunks = result.scalars().all()

        if not chunks:
            logger.warning(f"No chunks found for IDs: {chunk_ids}")
            return {"status": "error", "message": "No chunks found"}

        try:
            # Initialize services
            embedding_service = EmbeddingService()
            qdrant_store = QdrantStore()

            # Get document for project context
            document_id = chunks[0].document_id
            doc_statement = select(Document).where(Document.id == document_id)
            document = session.execute(doc_statement).scalar_one()

            # Generate embeddings
            texts = [chunk.text for chunk in chunks]
            embeddings = embedding_service.generate_embeddings(texts)

            # Save to PostgreSQL (pgvector)
            for chunk, embedding in zip(chunks, embeddings):
                chunk.embedding = embedding
                session.add(chunk)

            # Save to Qdrant
            qdrant_store.upsert_chunks(
                project_id=str(document.project_id),
                chunks=chunks,
                embeddings=embeddings,
            )

            session.commit()

            # Update document status to COMPLETED
            document.status = DocumentStatus.COMPLETED
            session.add(document)
            session.commit()

            # Notify user
            from app.services.notification import NotificationService

            notification_service = NotificationService()
            notification_service.notify_document_status(
                document.id, DocumentStatus.COMPLETED, message="Processing complete"
            )

            logger.info(f"Successfully generated embeddings for {len(chunks)} chunks")

            return {
                "status": "completed",
                "chunks_processed": len(chunks),
            }

        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            # Mark document as failed
            if chunks:
                document_id = chunks[0].document_id
                doc_statement = select(Document).where(Document.id == document_id)
                document = session.execute(doc_statement).scalar_one_or_none()
                if document:
                    document.status = DocumentStatus.FAILED
                    document.error_message = f"Embedding generation failed: {str(e)}"
                    session.add(document)
                    session.commit()

                    # Notify user
                    from app.services.notification import NotificationService

                    notification_service = NotificationService()
                    notification_service.notify_document_status(
                        document.id, DocumentStatus.FAILED, message=str(e)
                    )
            raise
