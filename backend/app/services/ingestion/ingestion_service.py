"""
Ingestion service orchestrator.

Coordinates the full document ingestion pipeline:
Parser → Cleaner → Deduplicator → Chunker → Storage

Features:
- File-type-aware processing
- Structured error handling
- Quality metrics tracking
- Logging at each pipeline step
"""

import logging
import time
from pathlib import Path
from typing import List, Optional
from uuid import UUID

from sqlmodel import Session

from app.models.document import Document
from app.models.chunk import Chunk
from app.services.ingestion.document_parser import DocumentParser
from app.services.ingestion.metadata_extractor import MetadataExtractor
from app.services.ingestion.text_cleaner import TextCleaner
from app.services.ingestion.deduplicator import Deduplicator
from app.services.ingestion.types import (
    FileType,
    IngestionResult,
    CleaningResult,
)
from app.services.processing.chunking_service import ChunkingService

logger = logging.getLogger(__name__)


class IngestionService:
    """
    Orchestrates the complete document ingestion pipeline.

    The pipeline consists of:
    1. Parse - Extract text from document
    2. Metadata - Extract document metadata
    3. Clean - Normalize and clean text (file-type aware)
    4. Deduplicate - Check for duplicate content
    5. Chunk - Split text into retrievable chunks
    6. Store - Save chunks to database
    """

    def __init__(
        self,
        # Cleaner configuration
        remove_page_numbers: bool = True,
        fix_hyphenation: bool = True,
        remove_boilerplate: bool = True,
        # Chunker configuration
        chunk_size: int = 512,
        chunk_overlap: int = 50,
    ):
        """
        Initialize the ingestion service with configuration.

        Args:
            remove_page_numbers: Remove page number artifacts
            fix_hyphenation: Fix hyphenated words across lines
            remove_boilerplate: Remove common boilerplate text
            chunk_size: Target chunk size in tokens
            chunk_overlap: Overlap between chunks
        """
        self.parser = DocumentParser()
        self.metadata_extractor = MetadataExtractor()
        self.text_cleaner = TextCleaner(
            remove_page_numbers=remove_page_numbers,
            fix_hyphenation=fix_hyphenation,
            remove_boilerplate=remove_boilerplate,
        )
        self.deduplicator = Deduplicator()
        self.chunking_service = ChunkingService(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )

    def process_document(
        self,
        document: Document,
        session: Session,
        skip_duplicate: bool = False,
    ) -> IngestionResult:
        """
        Process a document through the full ingestion pipeline.

        Args:
            document: Document record to process
            session: Database session
            skip_duplicate: If True, skip processing if duplicate found

        Returns:
            IngestionResult with chunks, metrics, and any warnings
        """
        start_time = time.time()
        result = IngestionResult()

        try:
            logger.info(
                f"Starting ingestion for document {document.id}: {document.filename}"
            )

            # Determine file type
            file_type = self._get_file_type(document.filename)
            logger.debug(f"Detected file type: {file_type.value}")

            # Step 1: Parse document from S3
            logger.debug("Step 1: Parsing document from S3")
            try:
                llama_documents = self.parser.parse_from_s3(document.url)
            except Exception as e:
                logger.error(f"Failed to parse document: {e}")
                result.success = False
                result.error = f"Parse error: {str(e)}"
                return result

            if not llama_documents:
                logger.warning("No content extracted from document")
                result.warnings.append("No content extracted from document")
                return result

            # Step 2: Extract metadata
            logger.debug("Step 2: Extracting metadata")
            metadata = self.metadata_extractor.extract(
                llama_documents, document.filename
            )
            logger.debug(
                f"Extracted metadata: title={metadata.title}, "
                f"pages={metadata.page_count}, words={metadata.word_count}"
            )

            # Step 3: Extract and clean text
            logger.debug("Step 3: Extracting and cleaning text")
            raw_text = self.parser.extract_text(llama_documents)

            cleaning_result = self.text_cleaner.clean(raw_text, file_type=file_type)
            result.cleaning_result = cleaning_result

            if cleaning_result.warnings:
                result.warnings.extend(cleaning_result.warnings)
                for warning in cleaning_result.warnings:
                    logger.warning(f"Cleaning warning: {warning}")

            logger.info(
                f"Cleaned text: {cleaning_result.metrics.original_length} -> "
                f"{cleaning_result.metrics.cleaned_length} chars "
                f"({cleaning_result.metrics.reduction_percentage:.1f}% reduction)"
            )

            if cleaning_result.metrics.hyphenations_fixed > 0:
                logger.debug(
                    f"Fixed {cleaning_result.metrics.hyphenations_fixed} hyphenations"
                )
            if cleaning_result.metrics.page_artifacts_removed > 0:
                logger.debug(
                    f"Removed {cleaning_result.metrics.page_artifacts_removed} page artifacts"
                )

            cleaned_text = cleaning_result.text
            if not cleaned_text:
                logger.warning("No text after cleaning")
                result.warnings.append("Document contains no extractable text")
                return result

            # Step 4: Check for duplicates
            logger.debug("Step 4: Checking for duplicates")
            content_hash = self.deduplicator.generate_content_hash(cleaned_text)

            existing = self.deduplicator.check_duplicate(
                session, content_hash, document.project_id, document.id
            )

            if existing:
                result.is_duplicate = True
                result.duplicate_document_id = str(existing.id)
                result.warnings.append(
                    f"Duplicate of existing document: {existing.filename}"
                )
                logger.warning(
                    f"Duplicate content detected. Matches document {existing.id}: "
                    f"{existing.filename}"
                )

                if skip_duplicate:
                    logger.info("Skipping duplicate document processing")
                    document.content_hash = content_hash
                    session.add(document)
                    session.commit()
                    return result

            # Save content hash to document
            document.content_hash = content_hash
            session.add(document)
            session.commit()
            logger.debug(f"Saved content hash: {content_hash[:16]}...")

            # Step 5: Chunk the text
            logger.debug("Step 5: Chunking text")
            chunk_texts = self.chunking_service.chunk_text(
                text=cleaned_text,
                source_metadata={
                    "document_id": str(document.id),
                    "filename": document.filename,
                    "title": metadata.title,
                    "file_type": file_type.value,
                },
            )

            logger.info(f"Created {len(chunk_texts)} chunks")

            # Step 6: Create Chunk records
            logger.debug("Step 6: Saving chunks to database")
            chunks = []
            for i, chunk_data in enumerate(chunk_texts):
                chunk = Chunk(
                    document_id=document.id,
                    text=chunk_data["text"],
                    page_number=chunk_data.get("page_number"),
                    metadata_=chunk_data.get("metadata", {}),
                )
                session.add(chunk)
                chunks.append(chunk)

            session.commit()

            # Refresh to get IDs
            for chunk in chunks:
                session.refresh(chunk)

            result.chunks = chunks

            elapsed_ms = (time.time() - start_time) * 1000
            logger.info(
                f"Completed ingestion for {document.filename}: "
                f"{len(chunks)} chunks in {elapsed_ms:.2f}ms"
            )

            return result

        except Exception as e:
            logger.exception(f"Ingestion failed for document {document.id}: {e}")
            result.success = False
            result.error = str(e)
            return result

    def _get_file_type(self, filename: str) -> FileType:
        """
        Determine file type from filename.
        """
        path = Path(filename)
        extension = path.suffix.lower()
        return FileType.from_extension(extension)
