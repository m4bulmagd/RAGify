"""
Document ingestion Celery tasks.

Handles the full document processing pipeline:
1. Download from S3
2. Parse document content
3. Clean and normalize text
4. Check for duplicates
5. Chunk text
6. Dispatch embedding tasks
"""

from uuid import UUID
from celery import shared_task
from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=600,
    retry_kwargs={"max_retries": 3},
    name="app.workers.document_ingestion.process_document",
)
def process_document(self, document_id: str) -> dict:
    """
    Main document processing task.

    Downloads document from S3, parses content, chunks text,
    and dispatches embedding generation tasks.

    Args:
        document_id: UUID of the document to process

    Returns:
        dict with processing results
    """
    from app.core.db import get_sync_session
    from app.models.document import Document, DocumentStatus
    from sqlmodel import select

    logger.info(f"Starting document processing for {document_id}")

    with get_sync_session() as session:
        # Fetch document
        statement = select(Document).where(Document.id == UUID(document_id))
        result = session.execute(statement)
        document = result.scalar_one_or_none()

        if not document:
            logger.error(f"Document {document_id} not found")
            return {"status": "error", "message": "Document not found"}

        try:
            # Update status to PROCESSING
            document.status = DocumentStatus.PROCESSING
            session.add(document)
            session.commit()

            # Step 1: Download file from S3
            from app.services.ingestion.ingestion_service import IngestionService

            ingestion_service = IngestionService()

            # Step 2: Parse, clean, chunk
            result = ingestion_service.process_document(document, session)
            chunks_data = result.chunks
            if not chunks_data:
                logger.warning(f"No chunks generated for document {document_id}")
                document.status = DocumentStatus.COMPLETED
                session.add(document)
                session.commit()

                # Notify user
                from app.services.notification import NotificationService

                notification_service = NotificationService()
                notification_service.notify_document_status(
                    document.id,
                    DocumentStatus.COMPLETED,
                    message="No content to process",
                )

                return {"status": "completed", "chunks": 0}

            # Step 3: Dispatch embedding generation
            from app.workers.embedding_generation import generate_chunks_embeddings

            chunk_ids = [chunk.id for chunk in chunks_data]
            generate_chunks_embeddings.delay(chunk_ids)

            logger.info(
                f"Document {document_id} parsed, {len(chunks_data)} chunks created"
            )

            return {
                "status": "processing",
                "chunks": len(chunks_data),
                "message": "Embeddings being generated",
            }

        except Exception as e:
            logger.error(f"Error processing document {document_id}: {e}")
            document.status = DocumentStatus.FAILED
            document.error_message = str(e)
            session.add(document)
            session.commit()

            # Notify user
            from app.services.notification import NotificationService

            notification_service = NotificationService()
            notification_service.notify_document_status(
                document.id, DocumentStatus.FAILED, message=str(e)
            )

            raise


@shared_task(name="app.workers.document_ingestion.cleanup_failed_documents")
def cleanup_failed_documents() -> dict:
    """
    Periodic task to clean up failed document processing attempts.
    Can be scheduled via Celery Beat.
    """
    from app.core.db import get_sync_session
    from app.models.document import Document, DocumentStatus
    from sqlmodel import select
    from datetime import datetime, timedelta

    logger.info("Running failed documents cleanup")

    with get_sync_session() as session:
        # Find documents stuck in PROCESSING for > 1 hour
        cutoff = datetime.utcnow() - timedelta(hours=1)
        statement = select(Document).where(
            Document.status == DocumentStatus.PROCESSING,
            Document.updated_at < cutoff,
        )
        result = session.execute(statement)
        stuck_docs = result.scalars().all()

        for doc in stuck_docs:
            doc.status = DocumentStatus.FAILED
            doc.error_message = "Processing timeout"
            session.add(doc)

        session.commit()

        return {"cleaned_up": len(stuck_docs)}
