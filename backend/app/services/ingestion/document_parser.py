"""
Document parser service.

Parses different document formats (PDF, DOCX, TXT, MD) and extracts text content.
Uses LlamaIndex readers for consistent document handling.
"""

import tempfile
import os
from typing import Optional
from pathlib import Path

from llama_index.core import SimpleDirectoryReader
from llama_index.core.schema import Document as LlamaDocument

from app.core.storage import s3_client


class DocumentParser:
    """
    Multi-format document parser using LlamaIndex readers.
    """

    SUPPORTED_EXTENSIONS = {".pdf", ".txt", ".md", ".docx"}

    def __init__(self):
        pass

    def parse_from_s3(self, s3_key: str) -> list[LlamaDocument]:
        """
        Download file from S3 and parse its content.

        Args:
            s3_key: S3 object key

        Returns:
            List of LlamaIndex Document objects
        """
        # Download to temp file
        with tempfile.TemporaryDirectory() as temp_dir:
            filename = os.path.basename(s3_key)
            local_path = os.path.join(temp_dir, filename)

            # Download from S3
            success = s3_client.download_file(s3_key, local_path)
            if not success:
                raise ValueError(f"Failed to download file from S3: {s3_key}")

            # Parse the file
            return self.parse_file(local_path)

    def parse_file(self, file_path: str) -> list[LlamaDocument]:
        """
        Parse a local file and extract text content.

        Args:
            file_path: Path to the local file

        Returns:
            List of LlamaIndex Document objects
        """
        path = Path(file_path)

        if path.suffix.lower() not in self.SUPPORTED_EXTENSIONS:
            raise ValueError(f"Unsupported file type: {path.suffix}")

        # Use SimpleDirectoryReader for consistent parsing
        reader = SimpleDirectoryReader(
            input_files=[str(path)],
            filename_as_id=True,
        )

        documents = reader.load_data()
        return documents

    def extract_text(self, documents: list[LlamaDocument]) -> str:
        """
        Extract combined text from all documents.

        Args:
            documents: List of LlamaIndex Documents

        Returns:
            Combined text content
        """
        return "\n\n".join([doc.text for doc in documents if doc.text])

    def get_page_count(self, documents: list[LlamaDocument]) -> int:
        """
        Get the total page count from documents.

        Args:
            documents: List of LlamaIndex Documents

        Returns:
            Number of pages (estimated for non-PDF documents)
        """
        # LlamaIndex may include page info in metadata
        max_page = 0
        for doc in documents:
            if doc.metadata and "page_label" in doc.metadata:
                try:
                    page = int(doc.metadata["page_label"])
                    max_page = max(max_page, page)
                except (ValueError, TypeError):
                    pass
        return max_page if max_page > 0 else len(documents)
