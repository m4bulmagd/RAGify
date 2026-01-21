"""
Chunking service.

Splits text into chunks using LlamaIndex text splitters.
"""

from typing import List, Dict, Any, Optional

from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.schema import Document as LlamaDocument


class ChunkingService:
    """
    Text chunking service using LlamaIndex.
    """

    def __init__(
        self,
        chunk_size: int = 512,
        chunk_overlap: int = 50,
    ):
        """
        Initialize chunking service.

        Args:
            chunk_size: Target size of each chunk in tokens
            chunk_overlap: Number of overlapping tokens between chunks
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.splitter = SentenceSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )

    def chunk_text(
        self,
        text: str,
        source_metadata: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Split text into chunks.

        Args:
            text: Text content to chunk
            source_metadata: Metadata to attach to each chunk

        Returns:
            List of chunk dictionaries with text and metadata
        """
        if not text:
            return []

        # Create a LlamaIndex document
        document = LlamaDocument(
            text=text,
            metadata=source_metadata or {},
        )

        # Split into nodes
        nodes = self.splitter.get_nodes_from_documents([document])

        # Convert to chunk dictionaries
        chunks = []
        for i, node in enumerate(nodes):
            chunk_data = {
                "text": node.text,
                "chunk_index": i,
                "metadata": {
                    **(source_metadata or {}),
                    "chunk_index": i,
                    "total_chunks": len(nodes),
                },
            }

            # Try to extract page number from metadata
            if node.metadata and "page_label" in node.metadata:
                try:
                    chunk_data["page_number"] = int(node.metadata["page_label"])
                except (ValueError, TypeError):
                    pass

            chunks.append(chunk_data)

        return chunks

    def chunk_with_window(
        self,
        text: str,
        window_size: int = 3,
        source_metadata: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Create chunks with surrounding context window.

        This creates overlapping chunks where each chunk includes
        context from surrounding sentences for better retrieval.

        Args:
            text: Text content to chunk
            window_size: Number of sentences in context window
            source_metadata: Metadata to attach to each chunk

        Returns:
            List of chunk dictionaries
        """
        # For now, use standard chunking
        # TODO: Implement SentenceWindowNodeParser for advanced use cases
        return self.chunk_text(text, source_metadata)
