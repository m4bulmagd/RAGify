from typing import Optional, List, TYPE_CHECKING
from uuid import UUID, uuid4
from enum import Enum
from sqlmodel import Field, SQLModel, Relationship
from datetime import datetime

if TYPE_CHECKING:
    from .project import Project
    from .chunk import Chunk


class DocumentStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class DocumentBase(SQLModel):
    filename: str
    file_type: str
    size: int
    status: DocumentStatus = Field(default=DocumentStatus.PENDING)
    error_message: Optional[str] = None
    url: Optional[str] = None  # Path to file on disk or S3 URL


class Document(DocumentBase, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    project_id: UUID = Field(foreign_key="project.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    project: "Project" = Relationship(back_populates="documents")
    chunks: List["Chunk"] = Relationship(back_populates="document")
