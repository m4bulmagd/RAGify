from typing import Optional, List, TYPE_CHECKING
from uuid import UUID, uuid4
from datetime import datetime
from sqlmodel import Field, SQLModel, Relationship
from app.utils.datetime import utc_now
from sqlalchemy import TIMESTAMP, Column

if TYPE_CHECKING:
    from .user import User
    from .document import Document
    from .agent import Agent
    from .chat import ChatSession


class ProjectBase(SQLModel):
    name: str = Field(index=True, max_length=255)
    description: Optional[str] = Field(default=None, max_length=1000)


class Project(ProjectBase, table=True):
    __tablename__ = "projects"  # Explicit table name

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    owner_id: UUID = Field(foreign_key="users.id", index=True)  # Match User.id type

    # Timestamps (recommended)
    created_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(TIMESTAMP(timezone=True), nullable=False),
    )
    updated_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(TIMESTAMP(timezone=True), nullable=False),
    )

    # Relationships
    owner: "User" = Relationship(back_populates="projects")
    documents: List["Document"] = Relationship(back_populates="project")
    agents: List["Agent"] = Relationship(back_populates="project")
    chat_sessions: List["ChatSession"] = Relationship(back_populates="project")
