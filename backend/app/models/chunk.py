from typing import Optional, List, Any, TYPE_CHECKING
from uuid import UUID, uuid4
from sqlmodel import Field, SQLModel, Relationship, Column
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects.postgresql import JSONB

if TYPE_CHECKING:
    from .document import Document


class ChunkBase(SQLModel):
    text: str
    metadata_: Optional[dict] = Field(default=None, sa_column=Column(JSONB))
    page_number: Optional[int] = None


class Chunk(ChunkBase, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    document_id: UUID = Field(foreign_key="document.id")

    # 1536 is default for OpenAI text-embedding-3-small, adjust as needed
    embedding: List[float] = Field(sa_column=Column(Vector(1536)))

    document: "Document" = Relationship(back_populates="chunks")
