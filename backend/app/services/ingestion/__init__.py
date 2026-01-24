"""
Ingestion services package.

Contains document parsing, metadata extraction, text cleaning,
and deduplication services.
"""

from app.services.ingestion.ingestion_service import IngestionService
from app.services.ingestion.text_cleaner import TextCleaner
from app.services.ingestion.types import (
    FileType,
    CleaningResult,
    CleaningMetrics,
    IngestionResult,
)

__all__ = [
    "IngestionService",
    "TextCleaner",
    "FileType",
    "CleaningResult",
    "CleaningMetrics",
    "IngestionResult",
]
