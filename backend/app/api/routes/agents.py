# app/api/routes/agents.py

from fastapi import APIRouter, HTTPException, status, Depends
from typing import List, Optional
from uuid import UUID

from app.api.deps import SessionDep, CurrentUser
from app.crud.agent import agent_crud
from app.schemas.agent import (
    AgentCreate,
    AgentResponse,
    AgentLLMConfigUpdate,
)

router = APIRouter()


@router.post("/", response_model=AgentResponse, status_code=status.HTTP_201_CREATED)
async def create_agent(
    *, db: SessionDep, current_user: CurrentUser, agent_in: AgentCreate
):
    """Create new agent with configurations"""

    # TODO: Verify user has access to project
    # ... permission check ...

    # TODO: Verify documents exist
    # ... permission check ...

    # TODO: Verify project exists
    # ... permission check ...

    # TODO: Verify user has access to documents
    # ... permission check ...

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
    # TODO: Add granular permissions

    if project_id:
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

    # TODO: Verify user has access to agent
    # ... permission check ...

    agent = await agent_crud.get_with_configs(db, agent_id)

    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found"
        )

    return agent


@router.patch("/{agent_id}/llm-config", response_model=AgentResponse)
async def update_llm_config(
    agent_id: UUID,
    config_update: AgentLLMConfigUpdate,
    db: SessionDep,
    current_user: CurrentUser,
):
    """Update LLM configuration for agent"""

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
