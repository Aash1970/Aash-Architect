"""Pydantic schemas for /auth routes."""
from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    full_name: str = Field(min_length=2, max_length=120)
    role: Literal["User", "Coach", "Admin", "SystemAdmin"] = "User"
    tier: Literal["Free", "Premium", "Enterprise"] = "Free"


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str = Field(min_length=8)


class UserResponse(BaseModel):
    user_id: str
    email: str
    full_name: str
    role: str
    tier: str
    language: str
    is_active: bool
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None


class LoginResponse(BaseModel):
    success: bool = True
    user: UserResponse
