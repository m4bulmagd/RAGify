from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.security import OAuth2PasswordRequestForm

from app.api.deps import SessionDep
from app.core import security
from app.core.config import settings
from app.crud import user as crud_user
from app.schemas.token import Token

router = APIRouter()


@router.post("/login/access-token")
async def login_access_token(
    session: SessionDep,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    response: Response,
) -> Token:
    """
    OAuth2 compatible token login, get an access token for future requests.
    """
    user = await crud_user.authenticate(
        session=session, email=form_data.username, password=form_data.password
    )
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    elif not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        user.id, expires_delta=access_token_expires
    )

    # Set cookie
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=settings.SECURE_COOKIES,
        samesite="lax",
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )

    # We still return the token in the body for clients that want it,
    # but the cookie is the primary method for the browser.
    # To return both cookie and JSON, we need to return a custom Response or attach to it.
    # However, FastAPI makes it easier to inject Response into the function arguments.
    return Token(access_token=access_token)


@router.post("/login/logout")
async def logout(response: Response):
    """
    Logout user by clearing the access token cookie.
    """
    response.delete_cookie("access_token")
    return {"message": "Logged out successfully"}
