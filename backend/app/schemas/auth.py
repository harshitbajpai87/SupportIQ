"""
SupportIQ — Auth Pydantic schemas.
"""
from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field
from app.models.user import UserRole


class UserCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    email: EmailStr
    password: str = Field(..., min_length=6)
    role: UserRole = UserRole.CUSTOMER
    preferred_language: str = "en"


class UserOut(BaseModel):
    id: int
    name: str
    email: str
    role: UserRole
    preferred_language: str
    is_active: bool

    model_config = {"from_attributes": True}


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut
