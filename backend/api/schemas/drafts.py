"""Pydantic schemas for /drafts routes."""
from __future__ import annotations

from typing import Any, Dict, Optional

from pydantic import BaseModel


class DraftSaveRequest(BaseModel):
    data: Dict[str, Any]


class DraftResponse(BaseModel):
    draft_id: str
    user_id: str
    cv_id: Optional[str] = None
    data: Dict[str, Any]
    saved_at: str

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "DraftResponse":
        return cls(
            draft_id=d["draft_id"],
            user_id=d["user_id"],
            cv_id=d.get("cv_id"),
            data=d.get("data", {}),
            saved_at=d["saved_at"],
        )
