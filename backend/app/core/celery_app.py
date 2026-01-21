"""
Celery application configuration.

This module sets up Celery for async task processing with Redis as the broker.
"""

from celery import Celery
from app.core.config import settings

# Create Celery app
broker_url = settings.REDIS_URL
if not broker_url:
    broker_url = f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/0"

celery_app = Celery(
    "ragify",
    broker=broker_url,
    backend=broker_url,
    include=["app.workers.document_ingestion", "app.workers.embedding_generation"],
)

# Celery configuration
celery_app.conf.update(
    # Serialization
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    # Timezone
    timezone="UTC",
    enable_utc=True,
    # Task settings
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes max per task
    task_soft_time_limit=25 * 60,  # Soft limit at 25 minutes
    # Retry settings
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    # Result settings
    result_expires=3600,  # Results expire after 1 hour
    # Worker settings
    worker_prefetch_multiplier=1,  # Fair distribution
    worker_concurrency=4,  # Number of concurrent workers
    # Task routing
    task_routes={
        "app.workers.document_ingestion.*": {"queue": "ingestion"},
        "app.workers.embedding_generation.*": {"queue": "embeddings"},
    },
    # Default queue
    task_default_queue="default",
)
