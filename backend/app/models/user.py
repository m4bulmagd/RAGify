from typing import Optional, List, TYPE_CHECKING
from uuid import UUID, uuid4
from sqlmodel import Field, SQLModel, Relationship

if TYPE_CHECKING:
    from .project import Project


class UserBase(SQLModel):
    email: str = Field(unique=True, index=True, max_length=255)
    is_active: bool = True
    is_superuser: bool = False
    full_name: Optional[str] = None


class User(UserBase, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    hashed_password: str

    projects: List["Project"] = Relationship(back_populates="owner")
