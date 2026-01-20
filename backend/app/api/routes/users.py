from typing import Any

from fastapi import APIRouter, HTTPException

from app.api.deps import CurrentUser, SessionDep
from app.crud import user as crud_user
from app.schemas.user import UserCreate, UserPublic, UserRegister, UserUpdateMe
from app.schemas.dashboard import DashboardStats
from app.models.project import Project
from app.models.chat import ChatMessage, ChatSession
from app.models.document import Document, DocumentStatus
from sqlmodel import select, func

router = APIRouter()


@router.post("/", response_model=UserPublic)
async def register_user(session: SessionDep, user_in: UserRegister) -> Any:
    """
    Create new user without the need to be logged in (Open Registration).
    """
    user = await crud_user.get_by_email(session, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=400,
            detail="The user with this email already exists in the system",
        )

    # Map UserRegister to UserCreate (which has password)
    user_create = UserCreate.model_validate(user_in.model_dump())
    user = await crud_user.create(session, obj_in=user_create)
    return user


@router.get("/me", response_model=UserPublic)
def read_user_me(current_user: CurrentUser) -> Any:
    """
    Get current user.
    """
    return current_user


@router.patch("/me", response_model=UserPublic)
async def update_user_me(
    session: SessionDep, user_in: UserUpdateMe, current_user: CurrentUser
) -> Any:
    """
    Update own user.
    """
    if user_in.email:
        existing_user = await crud_user.get_by_email(session, email=user_in.email)
        if existing_user and existing_user.id != current_user.id:
            raise HTTPException(
                status_code=409, detail="User with this email already exists"
            )

    user_data = user_in.model_dump(exclude_unset=True)
    current_user = await crud_user.update(
        session, db_obj=current_user, obj_in=user_data
    )
    return current_user


@router.get("/me/stats", response_model=DashboardStats)
async def read_user_dashboard_stats(
    session: SessionDep, current_user: CurrentUser
) -> Any:
    """
    Get current user dashboard statistics.
    """
    # 1. Total Projects
    proj_query = select(func.count(Project.id)).where(
        Project.owner_id == current_user.id
    )
    total_projects = (await session.execute(proj_query)).scalar() or 0

    # 2. Total Requests (Chat Messages)
    # Join ChatMessage -> ChatSession -> User
    msg_query = (
        select(func.count(ChatMessage.id))
        .join(ChatSession, ChatMessage.session_id == ChatSession.id)
        .where(ChatSession.user_id == current_user.id)
    )
    total_requests = (await session.execute(msg_query)).scalar() or 0

    # 3. Storage Usage (Sum of Document sizes)
    # Project -> Document (Project owner is user)
    storage_query = (
        select(func.sum(Document.size))
        .join(Project, Document.project_id == Project.id)
        .where(Project.owner_id == current_user.id)
    )
    storage_usage = (await session.execute(storage_query)).scalar() or 0

    # 4. Processing Docs
    processing_query = (
        select(func.count(Document.id))
        .join(Project, Document.project_id == Project.id)
        .where(
            Project.owner_id == current_user.id,
            (Document.status == DocumentStatus.PROCESSING)
            | (Document.status == DocumentStatus.PENDING),
        )
    )
    processing_docs = (await session.execute(processing_query)).scalar() or 0

    return DashboardStats(
        total_projects=total_projects,
        total_requests=total_requests,
        storage_usage=storage_usage,
        processing_docs=processing_docs,
    )
