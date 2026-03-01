"""Pydantic schemas for /admin routes."""
from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


class UserUpdateRequest(BaseModel):
    full_name: Optional[str] = Field(default=None, min_length=2, max_length=120)
    role: Optional[Literal["User", "Coach", "Admin", "SystemAdmin"]] = None
    tier: Optional[Literal["Free", "Premium", "Enterprise"]] = None
    language: Optional[str] = None
    is_active: Optional[bool] = None


class AssignCoachRequest(BaseModel):
    user_id: str
    coach_id: str


class RetentionPolicyUpdateRequest(BaseModel):
    cv_version_days: Optional[int] = None
    deleted_cv_days: Optional[int] = None
    export_log_days: Optional[int] = None


class UserRetentionOverrideRequest(BaseModel):
    user_id: str
    cv_version_days: int = Field(ge=1)


class SetLanguagesRequest(BaseModel):
    lang_codes: List[str] = Field(min_length=1)


class AdminUserReport(BaseModel):
    user_id: str
    email: str
    full_name: str
    role: str
    tier: str
    is_active: bool
    created_at: Optional[str] = None
