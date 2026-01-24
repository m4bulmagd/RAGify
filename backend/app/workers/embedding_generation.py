"""
Embedding generation Celery tasks.

Generates embeddings for document chunks and stores them
in PostgreSQL (pgvector).

Architecture:
- Tasks: Thin Celery wrappers that delegate to services
- Services: Business logic for embedding generation
"""

from typing import Any, Dict, List, Optional

from celery import shared_task
from celery.utils.log import get_task_logger
from sqlalchemy.exc import SQLAlchemyError

from app.services.processing.embedding_service import EmbeddingGenerationService
from app.services.processing.exceptions import (
    ChunkNotFoundError,
    EmbeddingGenerationError,
    EmbeddingProviderError,
    VectorStoreError,
)

logger = get_task_logger(__name__)


@shared_task(
    bind=True,
    autoretry_for=(
        EmbeddingProviderError,
        VectorStoreError,
        SQLAlchemyError,
    ),
    retry_backoff=True,
    retry_backoff_max=300,
    retry_kwargs={"max_retries": 3},
    name="app.workers.embedding_generation.generate_chunks_embeddings",
)
def generate_chunks_embeddings(
    self,
    chunk_ids: List[int],
    embedding_provider: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Generate embeddings for all chunks of a document.

    Splits chunks into batches and creates subtasks for parallel processing.

    Args:
        embedding_provider: Optional embedding provider name

    Returns:
        dict with task information
    """
    from app.core.db import get_sync_session

    with get_sync_session() as session:
        # Fetch all chunk IDs for document

        if not chunk_ids:
            logger.warning(f"No chunks provided")
            return {
                "status": "error",
                "message": "No chunks provided",
            }

        task_id = self.request.id

        if not chunk_ids:
            logger.warning(f"[{task_id}] Empty chunk_ids list provided")
            return {"status": "error", "message": "No chunk IDs provided"}

        try:
            service = EmbeddingGenerationService(
                session=session,
                embedding_provider_name=embedding_provider,
            )
            result = service.process_chunks(chunk_ids)

            logger.info(
                f"[{task_id}] Completed: {result['chunks_processed']} processed, "
            )
            return result

        except ChunkNotFoundError as e:
            # Don't retry if chunks don't exist
            logger.error(f"[{task_id}] Chunks not found: {e}")
            return {"status": "error", "message": str(e)}

        except (EmbeddingProviderError, VectorStoreError) as e:
            # Will be retried automatically by Celery
            logger.error(f"[{task_id}] Retryable error: {e}")
            raise

        except Exception as e:
            # Wrap unexpected errors
            logger.exception(f"[{task_id}] Unexpected error: {e}")
            raise EmbeddingGenerationError(f"Unexpected error: {e}") from e

        return {
            "status": "queued",
            "total_chunks": len(chunk_ids),
        }
