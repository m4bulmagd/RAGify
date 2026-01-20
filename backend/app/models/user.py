from typing import Optional, List, TYPE_CHECKING
from uuid import UUID, uuid4
from datetime import datetime
from app.utils.datetime import utc_now
from sqlalchemy import TIMESTAMP, Column
from sqlmodel import Field, SQLModel, Relationship

if TYPE_CHECKING:
    from .project import Project
    from .agent import Agent
    from .chat import ChatSession, ChatFeedback


class UserBase(SQLModel):
    email: str = Field(unique=True, index=True, max_length=255)
    is_active: bool = True
    is_superuser: bool = False
    full_name: Optional[str] = Field(default=None, max_length=255)


class User(UserBase, table=True):
    __tablename__ = "users"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    hashed_password: str

    created_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(TIMESTAMP(timezone=True), nullable=False),
    )
    updated_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(TIMESTAMP(timezone=True), nullable=False),
    )

    projects: List["Project"] = Relationship(back_populates="owner")
    agents: List["Agent"] = Relationship(back_populates="user")
    chat_sessions: List["ChatSession"] = Relationship(back_populates="user")
    chat_feedback: List["ChatFeedback"] = Relationship(back_populates="user")
