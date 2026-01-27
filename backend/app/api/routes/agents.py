# app/api/routes/agents.py

from fastapi import APIRouter, HTTPException, status, Depends
from typing import List, Optional
from uuid import UUID

from app.api import deps
from app.api.deps import SessionDep, CurrentUser
from app.crud.agent import agent_crud
from app.schemas.agent import (
    AgentCreate,
    AgentResponse,
    AgentLLMConfigUpdate,
)

from app.models.agent import LLMProvider
from app.providers.llm.openai_llm import OpenAILLM
from app.providers.llm.gemini_llm import GeminiLLM

# ... existing imports ...


router = APIRouter()


@router.get("/providers", response_model=List[dict])
async def get_providers(
    current_user: CurrentUser,
):
    """
    Get available LLM providers and their supported models.
    """
    return [
        {
            "provider": LLMProvider.OPENAI.value,
            "name": "OpenAI",
            "models": OpenAILLM.supported_models(),
        },
        {
            "provider": LLMProvider.GEMINI.value,
            "name": "Google Gemini",
            "models": GeminiLLM.supported_models(),
        },
    ]


@router.post("/", response_model=AgentResponse, status_code=status.HTTP_201_CREATED)
async def create_agent(
    *, db: SessionDep, current_user: CurrentUser, agent_in: AgentCreate
):
    """Create new agent with configurations"""

    # Verify user has access to project
    await deps.check_project_access(db, agent_in.project_id, current_user)

    agent = await agent_crud.create_with_configs(
        db=db,
        agent_data={
            "name": agent_in.name,
            "description": agent_in.description,
            "agent_type": agent_in.agent_type,
            "project_id": agent_in.project_id,
            "created_by": current_user.id,
        },
        llm_config_data=agent_in.llm_config.model_dump(),
        retrieval_config_data=agent_in.retrieval_config.model_dump(),
        document_ids=agent_in.document_ids,
    )

    return agent


@router.get("/", response_model=List[AgentResponse])
async def get_agents(
    db: SessionDep,
    current_user: CurrentUser,
    project_id: Optional[UUID] = None,
    skip: int = 0,
    limit: int = 100,
):
    """
    Retrieve agents.
    """
    if project_id:
        await deps.check_project_access(db, project_id, current_user)
        agents = await agent_crud.get_multi_by_project(
            db, project_id=project_id, skip=skip, limit=limit
        )
    else:
        # Get all agents
        agents = await agent_crud.get_multi(db, skip=skip, limit=limit)

    return agents


@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(
    agent_id: UUID,
    db: SessionDep,
    current_user: CurrentUser,
):
    """Get agent by ID with all configurations"""

    agent = await agent_crud.get_with_configs(db, agent_id)

    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found"
        )

    await deps.check_project_access(db, agent.project_id, current_user)

    return agent


@router.patch("/{agent_id}/llm-config", response_model=AgentResponse)
async def update_llm_config(
    agent_id: UUID,
    config_update: AgentLLMConfigUpdate,
    db: SessionDep,
    current_user: CurrentUser,
):
    """Update LLM configuration for agent"""

    agent = await agent_crud.get(db, agent_id)
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found"
        )
    await deps.check_project_access(db, agent.project_id, current_user)

    updated_config = await agent_crud.update_llm_config(
        db=db,
        agent_id=agent_id,
        config_data=config_update.model_dump(exclude_unset=True),
    )

    if not updated_config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found"
        )

    return await agent_crud.get_with_configs(db, agent_id)
