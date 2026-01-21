"""
Ingestion services package.

Contains document parsing, metadata extraction, text cleaning,
and deduplication services.
"""

from app.services.ingestion.ingestion_service import IngestionService

__all__ = ["IngestionService"]
