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

    The embedding column stores vector embeddings for similarity search.
    A configurable index (HNSW by default, or IVFFlat) is created on this column
    to accelerate vector similarity queries.

    Index Configuration (via environment variables):
        - VECTOR_INDEX_TYPE: "hnsw" (default) or "ivfflat"
        - VECTOR_DISTANCE_METRIC: "cosine" (default), "l2", or "inner_product"
        - VECTOR_HNSW_M: Max connections per node for HNSW (default: 16)
        - VECTOR_HNSW_EF_CONSTRUCTION: Construction candidate list size (default: 64)
        - VECTOR_IVFFLAT_LISTS: Number of IVF lists (default: 100)

    The index is created via alembic migration. See:
        alembic/versions/a1b2c3d4e5f6_add_hnsw_index_to_chunks_embedding.py
    """

    __tablename__ = "chunks"

    id: Optional[int] = Field(default=None, primary_key=True)
    document_id: UUID = Field(foreign_key="documents.id", index=True)
    created_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(TIMESTAMP(timezone=True), nullable=False),
    )

    # Embedding vector for similarity search
    # Dimension should match your embedding model (1536 for OpenAI text-embedding-3-small)
    # The vector index is managed via alembic migrations for configurability
    embedding: Optional[List[float]] = Field(
        default=None, sa_column=Column(Vector(1536))
    )

    document: "Document" = Relationship(back_populates="chunks")
    chat_contexts: List["ChatContext"] = Relationship(back_populates="chunk")
