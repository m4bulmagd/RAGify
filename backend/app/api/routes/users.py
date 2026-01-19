from typing import Any

from fastapi import APIRouter, HTTPException

from app.api.deps import CurrentUser, SessionDep
from app.crud import user as crud_user
from app.schemas.user import UserCreate, UserPublic, UserRegister, UserUpdateMe

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
