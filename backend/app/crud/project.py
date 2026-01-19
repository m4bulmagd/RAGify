from typing import List, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.crud.base import CRUDBase
from app.models.project import Project
from app.schemas.project import ProjectCreate, ProjectUpdate


class CRUDProject(CRUDBase[Project, ProjectCreate, ProjectUpdate]):
    async def get_multi_by_owner(
        self, session: AsyncSession, *, owner_id: UUID, skip: int = 0, limit: int = 100
    ) -> List[Project]:
        statement = (
            select(Project)
            .where(Project.owner_id == owner_id)
            .offset(skip)
            .limit(limit)
        )
        result = await session.execute(statement)
        return result.scalars().all()

    async def create_with_owner(
        self, session: AsyncSession, *, obj_in: ProjectCreate, owner_id: UUID
    ) -> Project:
        obj_in_data = obj_in.model_dump()
        db_obj = Project(**obj_in_data, owner_id=owner_id)
        session.add(db_obj)
        await session.commit()
        await session.refresh(db_obj)
        return db_obj


project = CRUDProject(Project)
