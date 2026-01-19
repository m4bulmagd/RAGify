from typing import Optional, List, TYPE_CHECKING
from uuid import UUID, uuid4
from sqlmodel import Field, SQLModel, Relationship

if TYPE_CHECKING:
    from .user import User
    from .document import Document


class ProjectBase(SQLModel):
    name: str = Field(index=True)
    description: Optional[str] = None


class Project(ProjectBase, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    owner_id: UUID = Field(foreign_key="user.id")

    owner: "User" = Relationship(back_populates="projects")
    documents: List["Document"] = Relationship(back_populates="project")
