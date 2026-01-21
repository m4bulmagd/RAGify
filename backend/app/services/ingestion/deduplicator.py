"""
Deduplication service.

Detects duplicate documents using content hashing.
"""

import hashlib
from typing import Optional
from uuid import UUID

from sqlmodel import Session, select

from app.models.document import Document


class Deduplicator:
    """
    Detects duplicate documents using content hashing.
    """

    def generate_content_hash(self, content: str) -> str:
        """
        Generate SHA-256 hash of content.

        Args:
            content: Text content to hash

        Returns:
            Hex digest of content hash
        """
        # Normalize content before hashing
        normalized = content.strip().lower()
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()

    def check_duplicate(
        self,
        session: Session,
        content_hash: str,
        project_id: UUID,
        exclude_document_id: Optional[UUID] = None,
    ) -> Optional[Document]:
        """
        Check if a document with this content hash already exists.

        Args:
            session: Database session
            content_hash: Hash to check
            project_id: Project to check within
            exclude_document_id: Document to exclude from check (for re-uploads)

        Returns:
            Existing Document if found, None otherwise
        """
        # Query for existing document with same content_hash and project_id
        statement = select(Document).where(
            Document.content_hash == content_hash,
            Document.project_id == project_id,
        )

        if exclude_document_id:
            statement = statement.where(Document.id != exclude_document_id)

        # Execute query
        result = session.execute(statement)
        return result.scalars().first()

    def is_duplicate(
        self,
        session: Session,
        content: str,
        project_id: UUID,
        exclude_document_id: Optional[UUID] = None,
    ) -> bool:
        """
        Check if content is a duplicate.

        Args:
            session: Database session
            content: Text content to check
            project_id: Project to check within
            exclude_document_id: Document to exclude

        Returns:
            True if duplicate exists
        """
        content_hash = self.generate_content_hash(content)
        duplicate = self.check_duplicate(
            session, content_hash, project_id, exclude_document_id
        )
        return duplicate is not None
