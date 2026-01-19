from typing import Any, List
from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from app.api.deps import CurrentUser, SessionDep
from app.crud import project as crud_project
from app.schemas.project import ProjectCreate, ProjectPublic, ProjectUpdate

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
