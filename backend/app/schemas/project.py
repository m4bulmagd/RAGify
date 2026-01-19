from typing import Optional
from uuid import UUID

from pydantic import BaseModel


# Shared properties
class ProjectBase(BaseModel):
    name: str
    description: Optional[str] = None


# Properties to receive on creation
class ProjectCreate(ProjectBase):
    pass


# Properties to receive on update
class ProjectUpdate(ProjectBase):
    name: Optional[str] = None


# Properties to return to client
class ProjectPublic(ProjectBase):
    id: UUID
    owner_id: UUID
