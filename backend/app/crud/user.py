from typing import Any, Dict, Optional, Union

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.core.security import get_password_hash, verify_password
from app.crud.base import CRUDBase
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate


class CRUDUser(CRUDBase[User, UserCreate, UserUpdate]):
    async def get_by_email(
        self, session: AsyncSession, *, email: str
    ) -> Optional[User]:
        result = await session.execute(select(User).where(User.email == email))
        return result.scalars().first()

    async def create(self, session: AsyncSession, *, obj_in: UserCreate) -> User:
        db_obj = User.model_validate(
            obj_in, update={"hashed_password": get_password_hash(obj_in.password)}
        )
        session.add(db_obj)
        await session.commit()
        await session.refresh(db_obj)
        return db_obj

    async def update(
        self,
        session: AsyncSession,
        *,
        db_obj: User,
        obj_in: Union[UserUpdate, Dict[str, Any]]
    ) -> User:
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True)

        if update_data.get("password"):
            hashed_password = get_password_hash(update_data["password"])
            del update_data["password"]
            update_data["hashed_password"] = hashed_password

        return await super().update(session=session, db_obj=db_obj, obj_in=update_data)

    async def authenticate(
        self, session: AsyncSession, *, email: str, password: str
    ) -> Optional[User]:
        user = await self.get_by_email(session, email=email)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user

    def is_active(self, user: User) -> bool:
        return user.is_active

    def is_superuser(self, user: User) -> bool:
        return user.is_superuser


user = CRUDUser(User)
