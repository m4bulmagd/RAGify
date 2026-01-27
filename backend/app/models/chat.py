# app/models/chat.py

from typing import Optional, List, TYPE_CHECKING
from uuid import UUID, uuid4
from datetime import datetime
from app.utils.datetime import utc_now
from sqlalchemy import TIMESTAMP, Column
from sqlmodel import Field, SQLModel, Relationship, JSON
from enum import Enum

if TYPE_CHECKING:
    from .user import User
    from .project import Project
    from .agent import Agent
    from .document import Document
    from .chunk import Chunk


class MessageRole(str, Enum):
    """Message role types"""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ChatSessionStatus(str, Enum):
    """Chat session status"""

    ACTIVE = "active"
    ARCHIVED = "archived"
    DELETED = "deleted"


class FeedbackType(str, Enum):
    """Feedback types"""

    THUMBS_UP = "thumbs_up"
    THUMBS_DOWN = "thumbs_down"
    RATING = "rating"  # 1-5 stars


# ============================================================================
# Chat Session
# ============================================================================


class ChatSessionBase(SQLModel):
    """Base model for chat sessions"""

    title: Optional[str] = Field(default=None, max_length=255)
    status: ChatSessionStatus = Field(default=ChatSessionStatus.ACTIVE)


class ChatSession(ChatSessionBase, table=True):
    """
    Chat session represents a conversation thread.
    Linked to a specific agent and project.
    """

    __tablename__ = "chat_sessions"

    id: UUID = Field(default_factory=uuid4, primary_key=True)

    # Foreign keys
    user_id: UUID = Field(foreign_key="users.id", index=True)
    project_id: UUID = Field(foreign_key="projects.id", index=True)
    agent_id: UUID = Field(foreign_key="agents.id", index=True)

    # Metadata
    message_count: int = Field(default=0)

    # Timestamps
    created_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(TIMESTAMP(timezone=True), nullable=False),
    )
    updated_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(TIMESTAMP(timezone=True), nullable=False),
    )
    last_message_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(TIMESTAMP(timezone=True), nullable=True),
    )

    # Relationships
    user: "User" = Relationship(back_populates="chat_sessions")
    project: "Project" = Relationship(back_populates="chat_sessions")
    agent: "Agent" = Relationship(back_populates="chat_sessions")
    messages: List["ChatMessage"] = Relationship(
        back_populates="session",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )


# ============================================================================
# Chat Message
# ============================================================================


class ChatMessageBase(SQLModel):
    """Base model for chat messages"""

    role: MessageRole
    content: str


class ChatMessage(ChatMessageBase, table=True):
    """
    Individual message in a chat session.
    Can be from user, assistant, or system.
    """

    __tablename__ = "chat_messages"

    id: UUID = Field(default_factory=uuid4, primary_key=True)

    # Foreign key
    session_id: UUID = Field(foreign_key="chat_sessions.id", index=True)

    # Message content and metadata
    content: str = Field(sa_column=Column(JSON))  # Can store rich content

    # LLM metadata (for assistant messages)
    model_name: Optional[str] = Field(default=None, max_length=100)
    tokens_used: Optional[int] = Field(default=None)
    latency_ms: Optional[int] = Field(default=None)  # Response time

    # Cost tracking
    cost_usd: Optional[float] = Field(default=None)

    # Search/retrieval metadata
    sources_count: int = Field(default=0)
    retrieval_score: Optional[float] = Field(default=None)

    # Timestamps
    created_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(TIMESTAMP(timezone=True), nullable=False),
    )

    # Relationships
    session: "ChatSession" = Relationship(back_populates="messages")
    contexts: List["ChatContext"] = Relationship(
        back_populates="message",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )
    feedback: Optional["ChatFeedback"] = Relationship(
        back_populates="message", sa_relationship_kwargs={"uselist": False}
    )


# ============================================================================
# Chat Context (Retrieved Chunks)
# ============================================================================


class ChatContextBase(SQLModel):
    """Base model for chat context"""

    similarity_score: float = Field(ge=0.0, le=1.0)
    rank: int = Field(ge=0)  # Position in retrieval results


class ChatContext(ChatContextBase, table=True):
    """
    Links messages to the document chunks used as context.
    Tracks which sources were retrieved and used for each response.
    """

    __tablename__ = "chat_contexts"

    id: UUID = Field(default_factory=uuid4, primary_key=True)

    # Foreign keys
    message_id: UUID = Field(foreign_key="chat_messages.id", index=True)
    chunk_id: int = Field(foreign_key="chunks.id", index=True)
    document_id: UUID = Field(foreign_key="documents.id", index=True)

    # Retrieval metadata
    similarity_score: float = Field(ge=0.0, le=1.0)
    rank: int = Field(ge=0)
    retrieval_method: str = Field(
        default="hybrid", max_length=50
    )  # vector, keyword, hybrid

    # Was this chunk actually used in the response?
    was_used: bool = Field(default=True)

    # Timestamps
    created_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(TIMESTAMP(timezone=True), nullable=False),
    )

    # Relationships
    message: "ChatMessage" = Relationship(back_populates="contexts")
    chunk: "Chunk" = Relationship(back_populates="chat_contexts")
    document: "Document" = Relationship(back_populates="chat_contexts")


# ============================================================================
# Chat Feedback
# ============================================================================


class ChatFeedbackBase(SQLModel):
    """Base model for chat feedback"""

    feedback_type: FeedbackType
    rating: Optional[int] = Field(default=None, ge=1, le=5)  # For RATING type
    comment: Optional[str] = Field(default=None, max_length=1000)


class ChatFeedback(ChatFeedbackBase, table=True):
    """
    User feedback on assistant messages.
    Helps track response quality and improve the system.
    """

    __tablename__ = "chat_feedback"

    id: UUID = Field(default_factory=uuid4, primary_key=True)

    # Foreign keys
    message_id: UUID = Field(foreign_key="chat_messages.id", unique=True, index=True)
    user_id: UUID = Field(foreign_key="users.id", index=True)

    # Feedback details
    feedback_type: FeedbackType
    rating: Optional[int] = Field(default=None, ge=1, le=5)
    comment: Optional[str] = Field(default=None, max_length=1000)

    # Categories for negative feedback
    issues: Optional[str] = Field(
        default=None, sa_column=Column(JSON)
    )  # ["inaccurate", "incomplete", "irrelevant"]

    # Timestamps
    created_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(TIMESTAMP(timezone=True), nullable=False),
    )
    updated_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(TIMESTAMP(timezone=True), nullable=False),
    )

    # Relationships
    message: "ChatMessage" = Relationship(back_populates="feedback")
    user: "User" = Relationship(back_populates="chat_feedback")
