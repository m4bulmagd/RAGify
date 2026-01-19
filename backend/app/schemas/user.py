from typing import Optional
from uuid import UUID
from pydantic import BaseModel, EmailStr


# Shared properties
class UserBase(BaseModel):
    email: EmailStr
    is_active: bool = True
    is_superuser: bool = False
    full_name: Optional[str] = None


# Properties to receive via API on creation
class UserCreate(UserBase):
    password: str


# Properties to receive via API on update
class UserUpdate(UserBase):
    password: Optional[str] = None


class UserUpdateMe(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None


# Properties to return to client
class UserPublic(UserBase):
    id: UUID


class UserRegister(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None
