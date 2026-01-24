"""
Types for ingestion service.

Contains dataclasses for structured results from the ingestion pipeline.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum


class FileType(str, Enum):
    """Supported file types for ingestion."""

    PDF = "pdf"
    TXT = "txt"
    MD = "md"
    CSV = "csv"
    UNKNOWN = "unknown"

    @classmethod
    def from_extension(cls, extension: str) -> "FileType":
        """Get FileType from file extension."""
        ext = extension.lower().lstrip(".")
        mapping = {
            "pdf": cls.PDF,
            "txt": cls.TXT,
            "md": cls.MD,
            "markdown": cls.MD,
            "csv": cls.CSV,
        }
        return mapping.get(ext, cls.UNKNOWN)


@dataclass
class CleaningMetrics:
    """Metrics from the text cleaning process."""

    original_length: int = 0
    cleaned_length: int = 0
    chars_removed: int = 0
    lines_removed: int = 0
    hyphenations_fixed: int = 0
    page_artifacts_removed: int = 0
    headers_removed: int = 0
    footers_removed: int = 0
    urls_normalized: int = 0
    whitespace_normalized: int = 0
    processing_time_ms: float = 0.0

    @property
    def reduction_percentage(self) -> float:
        """Calculate the percentage of text removed."""
        if self.original_length == 0:
            return 0.0
        return (self.chars_removed / self.original_length) * 100


@dataclass
class CleaningResult:
    """Result of the text cleaning process."""

    text: str
    metrics: CleaningMetrics = field(default_factory=CleaningMetrics)
    warnings: List[str] = field(default_factory=list)
    file_type: FileType = FileType.UNKNOWN


@dataclass
class IngestionResult:
    """Result of the full ingestion pipeline."""

    chunks: List[Any] = field(default_factory=list)  # List[Chunk]
    cleaning_result: Optional[CleaningResult] = None
    is_duplicate: bool = False
    duplicate_document_id: Optional[str] = None
    warnings: List[str] = field(default_factory=list)
    error: Optional[str] = None
    success: bool = True

    @property
    def chunk_count(self) -> int:
        """Number of chunks created."""
        return len(self.chunks)
