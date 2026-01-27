# app/models/agent.py

from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
from enum import Enum
import json
from uuid import UUID, uuid4
from sqlalchemy import Column, TIMESTAMP

from datetime import datetime, UTC
from app.utils.datetime import utc_now
from app.core.constants import GeminiModel


class LLMProvider(str, Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    AZURE_OPENAI = "azure_openai"
    OLLAMA = "ollama"
    GEMINI = "gemini"


class AgentType(str, Enum):
    QA = "question-answering"


class AgentBase(SQLModel):
    name: str = Field(max_length=255, index=True)
    description: Optional[str] = Field(default=None, max_length=1000)
    agent_type: AgentType = Field(default=AgentType.QA)
    is_active: bool = Field(default=True)


class Agent(AgentBase, table=True):
    __tablename__ = "agents"

    id: UUID = Field(default_factory=uuid4, primary_key=True)

    # Foreign keys - use UUID to match your User and Project models
    project_id: UUID = Field(foreign_key="projects.id", index=True)
    created_by: UUID = Field(foreign_key="users.id", index=True)

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
    project: "Project" = Relationship(back_populates="agents")
    user: "User" = Relationship(back_populates="agents")
    llm_config: Optional["AgentLLMConfig"] = Relationship(
        back_populates="agent", sa_relationship_kwargs={"uselist": False}
    )
    retrieval_config: Optional["AgentRetrievalConfig"] = Relationship(
        back_populates="agent", sa_relationship_kwargs={"uselist": False}
    )

    document_links: List["AgentDocument"] = Relationship(back_populates="agent")
    chat_sessions: List["ChatSession"] = Relationship(back_populates="agent")


# LLM-specific Configuration
class AgentLLMConfig(SQLModel, table=True):
    __tablename__ = "agent_llm_configs"

    id: Optional[int] = Field(default=None, primary_key=True)
    agent_id: UUID = Field(foreign_key="agents.id", unique=True, index=True)

    # LLM Provider Settings
    provider: LLMProvider = Field(default=LLMProvider.GEMINI)
    model_name: str = Field(default=GeminiModel.GEMINI_2_5_PRO)

    # Generation Parameters
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(default=1000, ge=1, le=128000)
    top_p: float = Field(default=1.0, ge=0.0, le=1.0)
    frequency_penalty: float = Field(default=0.0, ge=-2.0, le=2.0)
    presence_penalty: float = Field(default=0.0, ge=-2.0, le=2.0)

    # Prompting
    system_prompt: str = Field(
        default="You are a helpful AI assistant.", max_length=4000
    )

    # Streaming
    enable_streaming: bool = Field(default=True)

    # Advanced Settings (JSON for flexibility)
    additional_params: Optional[str] = Field(default=None)  # JSON string

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
    agent: "Agent" = Relationship(back_populates="llm_config")

    @property
    def additional_params_dict(self) -> dict:
        """Parse additional params from JSON"""
        if self.additional_params:
            return json.loads(self.additional_params)
        return {}

    @additional_params_dict.setter
    def additional_params_dict(self, value: dict):
        """Set additional params as JSON"""
        self.additional_params = json.dumps(value)


# Retrieval-specific Configuration
class AgentRetrievalConfig(SQLModel, table=True):
    __tablename__ = "agent_retrieval_configs"

    id: Optional[int] = Field(default=None, primary_key=True)
    agent_id: UUID = Field(foreign_key="agents.id", unique=True, index=True)

    # Retrieval Strategy
    retrieval_mode: str = Field(
        default="hybrid", max_length=50  # Options: vector, keyword, hybrid
    )

    # Search Parameters
    top_k: int = Field(default=5, ge=1, le=50)
    similarity_threshold: float = Field(default=0.7, ge=0.0, le=1.0)

    # Hybrid Search Weights
    vector_weight: float = Field(default=0.7, ge=0.0, le=1.0)
    keyword_weight: float = Field(default=0.3, ge=0.0, le=1.0)

    # Reranking
    enable_reranking: bool = Field(default=False)
    reranker_model: Optional[str] = Field(default=None, max_length=255)
    rerank_top_n: Optional[int] = Field(default=3, ge=1, le=20)

    # Context Settings
    max_context_tokens: int = Field(default=4000, ge=100, le=32000)
    include_metadata: bool = Field(default=True)

    # Query Enhancement
    enable_query_expansion: bool = Field(default=False)
    enable_hypothetical_questions: bool = Field(default=False)

    # Filtering
    metadata_filters: Optional[str] = Field(default=None)  # JSON string

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
    agent: "Agent" = Relationship(back_populates="retrieval_config")


# Many-to-Many: Agent <-> Document
class AgentDocument(SQLModel, table=True):
    __tablename__ = "agent_documents"

    id: Optional[int] = Field(default=None, primary_key=True)
    agent_id: UUID = Field(foreign_key="agents.id", index=True)
    document_id: UUID = Field(foreign_key="documents.id", index=True)

    # Optional: Document-specific settings for this agent
    priority: int = Field(default=0)  # Higher priority documents searched first
    is_active: bool = Field(default=True)

    # Timestamps
    linked_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(TIMESTAMP(timezone=True), nullable=False),
    )

    # Relationships
    agent: "Agent" = Relationship(back_populates="document_links")
    document: "Document" = Relationship(back_populates="agent_links")
