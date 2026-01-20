from typing import Optional, List, Any, TYPE_CHECKING
from uuid import UUID, uuid4
from sqlmodel import Field, SQLModel, Relationship, Column
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime
from app.utils.datetime import utc_now
from sqlalchemy import TIMESTAMP, Column

if TYPE_CHECKING:
    from .document import Document
    from .chat import ChatContext


class ChunkBase(SQLModel):
    text: str
    metadata_: Optional[dict] = Field(default=None, sa_column=Column(JSONB))
    page_number: Optional[int] = None


class Chunk(ChunkBase, table=True):
    """
    Text chunk from a document with embeddings.
    """

    __tablename__ = "chunks"

    id: Optional[int] = Field(default=None, primary_key=True)
    document_id: UUID = Field(foreign_key="documents.id", index=True)
    created_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(TIMESTAMP(timezone=True), nullable=False),
    )

    embedding: Optional[List[float]] = Field(
        default=None, sa_column=Column(Vector(1536))
    )

    document: "Document" = Relationship(back_populates="chunks")
    chat_contexts: List["ChatContext"] = Relationship(back_populates="chunk")
