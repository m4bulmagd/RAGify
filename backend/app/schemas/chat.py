# app/schemas/chat.py

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime
from uuid import UUID
from app.models.chat import MessageRole, ChatSessionStatus, FeedbackType


# ============================================================================
# Chat Session Schemas
# ============================================================================


class ChatSessionCreate(BaseModel):
    """Schema for creating a chat session"""

    agent_id: UUID
    project_id: UUID
    title: Optional[str] = None


class ChatSessionUpdate(BaseModel):
    """Schema for updating a chat session"""

    title: Optional[str] = None
    status: Optional[ChatSessionStatus] = None


class ChatSessionResponse(BaseModel):
    """Schema for chat session response"""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    project_id: UUID
    agent_id: UUID
    title: Optional[str]
    status: ChatSessionStatus
    message_count: int
    created_at: datetime
    updated_at: datetime
    last_message_at: Optional[datetime]


class ChatSessionDetail(ChatSessionResponse):
    """Detailed chat session with messages"""

    messages: List["ChatMessageResponse"] = []


# ============================================================================
# Chat Message Schemas
# ============================================================================


class ChatMessageCreate(BaseModel):
    """Schema for creating a message"""

    session_id: UUID
    role: MessageRole
    content: str


class ChatMessageResponse(BaseModel):
    """Schema for message response"""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    session_id: UUID
    role: MessageRole
    content: str
    model_name: Optional[str]
    tokens_used: Optional[int]
    latency_ms: Optional[int]
    cost_usd: Optional[float]
    sources_count: int
    created_at: datetime


class ChatMessageDetail(ChatMessageResponse):
    """Detailed message with contexts and feedback"""

    contexts: List["ChatContextResponse"] = []
    feedback: Optional["ChatFeedbackResponse"] = None


# ============================================================================
# Chat Request/Response (for API)
# ============================================================================


class ChatRequest(BaseModel):
    """Request for chat completion"""

    session_id: Optional[UUID] = None  # If None, create new session
    agent_id: UUID
    message: str
    stream: bool = Field(default=True, description="Enable streaming response")


class ChatSource(BaseModel):
    """Source information for citations"""

    chunk_id: UUID
    document_id: UUID
    document_name: str
    content: str
    similarity_score: float
    page_number: Optional[int] = None


class ChatResponse(BaseModel):
    """Response from chat completion"""

    session_id: UUID
    message_id: UUID
    content: str
    sources: List[ChatSource] = []
    model_name: str
    tokens_used: int
    latency_ms: int


class ChatStreamChunk(BaseModel):
    """Chunk for streaming response"""

    type: str  # "content", "source", "done"
    content: Optional[str] = None
    source: Optional[ChatSource] = None
    metadata: Optional[dict] = None


# ============================================================================
# Chat Context Schemas
# ============================================================================


class ChatContextResponse(BaseModel):
    """Schema for chat context response"""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    message_id: UUID
    chunk_id: UUID
    document_id: UUID
    similarity_score: float
    rank: int
    retrieval_method: str
    was_used: bool
    created_at: datetime


# ============================================================================
# Chat Feedback Schemas
# ============================================================================


class ChatFeedbackCreate(BaseModel):
    """Schema for creating feedback"""

    message_id: UUID
    feedback_type: FeedbackType
    rating: Optional[int] = Field(default=None, ge=1, le=5)
    comment: Optional[str] = Field(default=None, max_length=1000)
    issues: Optional[List[str]] = None  # ["inaccurate", "incomplete", "irrelevant"]


class ChatFeedbackUpdate(BaseModel):
    """Schema for updating feedback"""

    rating: Optional[int] = Field(default=None, ge=1, le=5)
    comment: Optional[str] = None
    issues: Optional[List[str]] = None


class ChatFeedbackResponse(BaseModel):
    """Schema for feedback response"""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    message_id: UUID
    user_id: UUID
    feedback_type: FeedbackType
    rating: Optional[int]
    comment: Optional[str]
    issues: Optional[List[str]]
    created_at: datetime
    updated_at: datetime


# ============================================================================
# Analytics Schemas
# ============================================================================


class ChatAnalytics(BaseModel):
    """Analytics for chat sessions"""

    total_sessions: int
    total_messages: int
    avg_messages_per_session: float
    avg_latency_ms: float
    total_cost_usd: float
    feedback_summary: dict  # {thumbs_up: 10, thumbs_down: 2, ...}
    popular_agents: List[dict]  # [{agent_id, agent_name, usage_count}]
