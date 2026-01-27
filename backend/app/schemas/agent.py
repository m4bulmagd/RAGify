# app/schemas/agent.py

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime
from app.models.agent import LLMProvider, AgentType
from uuid import UUID


# Base schemas
class AgentLLMConfigBase(BaseModel):
    provider: LLMProvider = LLMProvider.OPENAI
    model_name: str = "gpt-4-turbo-preview"
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(default=1000, ge=1)
    top_p: float = Field(default=1.0, ge=0.0, le=1.0)
    system_prompt: str = "You are a helpful AI assistant."
    enable_streaming: bool = True


class AgentRetrievalConfigBase(BaseModel):
    retrieval_mode: str = "hybrid"
    top_k: int = Field(default=5, ge=1, le=50)
    similarity_threshold: float = Field(default=0.7, ge=0.0, le=1.0)
    enable_reranking: bool = False


class AgentBase(BaseModel):
    name: str
    description: Optional[str] = None
    agent_type: AgentType = AgentType.QA


# Create schemas
class AgentCreate(AgentBase):
    project_id: UUID
    llm_config: AgentLLMConfigBase
    retrieval_config: AgentRetrievalConfigBase
    document_ids: Optional[List[UUID]] = None


class AgentUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class AgentLLMConfigUpdate(BaseModel):
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    system_prompt: Optional[str] = None
    # ... other fields as optional


class AgentRetrievalConfigUpdate(BaseModel):
    retrieval_mode: Optional[str] = None
    top_k: Optional[int] = None
    similarity_threshold: Optional[float] = None
    enable_reranking: Optional[bool] = None


# Response schemas
class AgentLLMConfigResponse(AgentLLMConfigBase):
    id: int
    agent_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AgentRetrievalConfigResponse(AgentRetrievalConfigBase):
    id: int
    agent_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AgentResponse(AgentBase):
    id: UUID
    project_id: UUID
    created_by: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime
    llm_config: Optional[AgentLLMConfigResponse] = None
    retrieval_config: Optional[AgentRetrievalConfigResponse] = None

    model_config = ConfigDict(from_attributes=True)
