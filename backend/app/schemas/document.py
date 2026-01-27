from typing import Optional
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, ConfigDict

from app.models.document import DocumentStatus


class DocumentBase(BaseModel):
    filename: str
    file_type: str
    size: int
    status: DocumentStatus
    error_message: Optional[str] = None
    url: Optional[str] = None
    content_hash: Optional[str] = None


class DocumentWithChunkCount(DocumentBase):
    """Document response with chunk_count for list views."""

    id: UUID
    project_id: UUID
    created_at: datetime
    updated_at: datetime
    chunk_count: int = 0

    model_config = ConfigDict(from_attributes=True)
