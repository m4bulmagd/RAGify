"""
Metadata extraction service.

Extracts metadata from documents like title, author, creation date.
"""

from typing import Optional
from dataclasses import dataclass
from datetime import datetime

from llama_index.core.schema import Document as LlamaDocument


@dataclass
class DocumentMetadata:
    """Extracted document metadata."""

    title: Optional[str] = None
    author: Optional[str] = None
    created_date: Optional[datetime] = None
    page_count: int = 0
    word_count: int = 0
    language: Optional[str] = None


class MetadataExtractor:
    """
    Extracts metadata from parsed documents.
    """

    def extract(
        self, documents: list[LlamaDocument], filename: str
    ) -> DocumentMetadata:
        """
        Extract metadata from documents.

        Args:
            documents: List of parsed LlamaIndex documents
            filename: Original filename

        Returns:
            DocumentMetadata with extracted information
        """
        metadata = DocumentMetadata()

        # Extract from LlamaIndex document metadata
        if documents:
            first_doc = documents[0]
            doc_metadata = first_doc.metadata or {}

            # Try to get title from metadata
            metadata.title = doc_metadata.get("title") or self._extract_title_from_text(
                first_doc.text
            )

            # Author
            metadata.author = doc_metadata.get("author")

            # Creation date
            if "creation_date" in doc_metadata:
                try:
                    metadata.created_date = datetime.fromisoformat(
                        doc_metadata["creation_date"]
                    )
                except (ValueError, TypeError):
                    pass

        # Calculate word count
        total_text = " ".join([doc.text for doc in documents if doc.text])
        metadata.word_count = len(total_text.split())

        # Page count
        metadata.page_count = self._get_page_count(documents)

        # Fallback title to filename
        if not metadata.title:
            metadata.title = filename.rsplit(".", 1)[0] if "." in filename else filename

        return metadata

    def _extract_title_from_text(self, text: str) -> Optional[str]:
        """
        Try to extract title from first line of text.
        """
        if not text:
            return None

        lines = text.strip().split("\n")
        if lines:
            first_line = lines[0].strip()
            # If first line is reasonably short, use as title
            if len(first_line) <= 200:
                return first_line

        return None

    def _get_page_count(self, documents: list[LlamaDocument]) -> int:
        """
        Get page count from documents metadata.
        """
        max_page = 0
        for doc in documents:
            if doc.metadata and "page_label" in doc.metadata:
                try:
                    page = int(doc.metadata["page_label"])
                    max_page = max(max_page, page)
                except (ValueError, TypeError):
                    pass

        return max_page if max_page > 0 else len(documents)
