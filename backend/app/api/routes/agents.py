# app/api/routes/agents.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session
from typing import List

from app.api import deps
from app.crud.agent import agent_crud
from app.schemas.agent import (
    AgentCreate,
    AgentUpdate,
    AgentResponse,
    AgentLLMConfigUpdate,
    AgentRetrievalConfigUpdate,
)
from app.models.user import User
from uuid import UUID

router = APIRouter()


@router.post("/", response_model=AgentResponse, status_code=status.HTTP_201_CREATED)
def create_agent(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    agent_in: AgentCreate
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

    agent = agent_crud.create_with_configs(
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


@router.get("/{agent_id}", response_model=AgentResponse)
def get_agent(
    agent_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """Get agent by ID with all configurations"""

    # TODO: Verify user has access to agent
    # ... permission check ...

    agent = agent_crud.get_with_configs(db, agent_id)

    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found"
        )

    # Check permissions
    # ...

    return agent


@router.patch("/{agent_id}/llm-config", response_model=AgentResponse)
def update_llm_config(
    agent_id: UUID,
    config_update: AgentLLMConfigUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """Update LLM configuration for agent"""

    updated_config = agent_crud.update_llm_config(
        db=db,
        agent_id=agent_id,
        config_data=config_update.model_dump(exclude_unset=True),
    )

    if not updated_config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found"
        )

    return agent_crud.get_with_configs(db, agent_id)
