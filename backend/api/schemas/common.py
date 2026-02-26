"""Shared response envelopes and error models."""
from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel


class ErrorDetail(BaseModel):
    code: str
    message: str
    field: Optional[str] = None


class ErrorResponse(BaseModel):
    success: bool = False
    error: ErrorDetail


class MessageResponse(BaseModel):
    success: bool = True
    message: str


class DataResponse(BaseModel):
    success: bool = True
    data: Any
