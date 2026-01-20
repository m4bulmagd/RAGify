from typing import Any, List
from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from app.api.deps import CurrentUser, SessionDep
from app.crud import project as crud_project
from app.schemas.project import ProjectCreate, ProjectPublic, ProjectUpdate

from app.schemas.project_stats import ProjectStats
from app.models.document import Document
from app.models.agent import Agent
from app.models.chunk import Chunk
from sqlmodel import select, func


router = APIRouter()


@router.post("/", response_model=ProjectPublic)
async def create_project(
    *, session: SessionDep, current_user: CurrentUser, project_in: ProjectCreate
) -> Any:
    """
    Create new project.
    """
    project = await crud_project.create_with_owner(
        session=session, obj_in=project_in, owner_id=current_user.id
    )
    return project


@router.get("/", response_model=List[ProjectPublic])
async def read_projects(
    session: SessionDep, current_user: CurrentUser, skip: int = 0, limit: int = 100
) -> Any:
    """
    Retrieve projects.
    """
    projects = await crud_project.get_multi_by_owner(
        session=session, owner_id=current_user.id, skip=skip, limit=limit
    )
    return projects


@router.get("/{id}", response_model=ProjectPublic)
async def read_project(session: SessionDep, current_user: CurrentUser, id: UUID) -> Any:
    """
    Get project by ID.
    """
    project = await crud_project.get(session=session, id=id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if project.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return project


@router.put("/{id}", response_model=ProjectPublic)
async def update_project(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    id: UUID,
    project_in: ProjectUpdate,
) -> Any:
    """
    Update a project.
    """
    project = await crud_project.get(session=session, id=id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if project.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    project = await crud_project.update(
        session=session, db_obj=project, obj_in=project_in
    )
    return project


@router.delete("/{id}", response_model=ProjectPublic)
async def delete_project(
    session: SessionDep, current_user: CurrentUser, id: UUID
) -> Any:
    """
    Delete a project.
    """
    project = await crud_project.get(session=session, id=id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if project.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    project = await crud_project.remove(session=session, id=id)
    return project


@router.get("/{id}/stats", response_model=ProjectStats)
async def get_project_stats(
    session: SessionDep, current_user: CurrentUser, id: UUID
) -> Any:
    """
    Get project statistics.
    """
    project = await crud_project.get(session=session, id=id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if project.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    # 1. Total Documents
    doc_query = select(func.count(Document.id)).where(Document.project_id == id)
    total_docs = (await session.execute(doc_query)).scalar() or 0

    # 2. Active Agents
    agent_query = select(func.count(Agent.id)).where(
        Agent.project_id == id, Agent.is_active == True
    )
    active_agents = (await session.execute(agent_query)).scalar() or 0

    # 3. Total Chunks
    # Join Chunk with Document to filter by project_id
    chunk_query = (
        select(func.count(Chunk.id))
        .join(Document, Chunk.document_id == Document.id)
        .where(Document.project_id == id)
    )
    total_chunks = (await session.execute(chunk_query)).scalar() or 0

    return ProjectStats(
        total_documents=total_docs,
        active_agents=active_agents,
        total_chunks=total_chunks,
        avg_retrieval_score=0.0,  # Placeholder
    )
