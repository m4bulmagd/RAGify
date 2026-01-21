"""
Ingestion service orchestrator.

Coordinates the full document ingestion pipeline:
Parser → Cleaner → Deduplicator → Chunker → Storage
"""

from typing import List
from uuid import UUID

from sqlmodel import Session

from app.models.document import Document
from app.models.chunk import Chunk
from app.services.ingestion.document_parser import DocumentParser
from app.services.ingestion.metadata_extractor import MetadataExtractor
from app.services.ingestion.text_cleaner import TextCleaner
from app.services.ingestion.deduplicator import Deduplicator
from app.services.processing.chunking_service import ChunkingService


class IngestionService:
    """
    Orchestrates the complete document ingestion pipeline.
    """

    def __init__(self):
        self.parser = DocumentParser()
        self.metadata_extractor = MetadataExtractor()
        self.text_cleaner = TextCleaner()
        self.deduplicator = Deduplicator()
        self.chunking_service = ChunkingService()

    def process_document(self, document: Document, session: Session) -> List[Chunk]:
        """
        Process a document through the full ingestion pipeline.

        Args:
            document: Document record to process
            session: Database session

        Returns:
            List of created Chunk objects
        """
        # Step 1: Parse document from S3
        llama_documents = self.parser.parse_from_s3(document.url)

        if not llama_documents:
            return []

        # Step 2: Extract metadata
        metadata = self.metadata_extractor.extract(llama_documents, document.filename)

        # Step 3: Extract and clean text
        raw_text = self.parser.extract_text(llama_documents)
        cleaned_text = self.text_cleaner.clean(raw_text)

        if not cleaned_text:
            return []

        # Step 4: Check for duplicates
        if self.deduplicator.is_duplicate(session, cleaned_text, document.project_id):
            # For now, we will just log it and proceed, but ideally we should flag it
            # or update the document status to indicate it's a duplicate.
            # Or maybe we skip processing?
            # Let's update the content hash and maybe skip chunking if strict deduplication is needed.
            # Current requirement: just check. We will save the hash.
            pass

        # Save content hash to document
        document.content_hash = self.deduplicator.generate_content_hash(cleaned_text)
        session.add(document)
        session.commit()  # Save hash before chunking (in case chunking fails)

        # Step 5: Chunk the text
        chunk_texts = self.chunking_service.chunk_text(
            text=cleaned_text,
            source_metadata={
                "document_id": str(document.id),
                "filename": document.filename,
                "title": metadata.title,
            },
        )

        # Step 6: Create Chunk records
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

        # Commit to get chunk IDs
        session.commit()

        # Refresh to get IDs
        for chunk in chunks:
            session.refresh(chunk)

        return chunks
