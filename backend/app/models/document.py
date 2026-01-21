from typing import Optional, List, TYPE_CHECKING
from uuid import UUID, uuid4
from enum import Enum
from sqlmodel import Field, SQLModel, Relationship
from datetime import datetime
from app.utils.datetime import utc_now
from sqlalchemy import TIMESTAMP, Column

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
    content_hash: Optional[str] = Field(default=None, index=True)


class Document(DocumentBase, table=True):
    __tablename__ = "documents"
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    project_id: UUID = Field(foreign_key="projects.id")
    created_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(TIMESTAMP(timezone=True), nullable=False),
    )
    updated_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(TIMESTAMP(timezone=True), nullable=False),
    )

    project: "Project" = Relationship(back_populates="documents")
    chunks: List["Chunk"] = Relationship(back_populates="document")
    agent_links: List["AgentDocument"] = Relationship(back_populates="document")
    chat_contexts: List["ChatContext"] = Relationship(back_populates="document")
