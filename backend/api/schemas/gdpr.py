"""Pydantic schemas for /gdpr routes."""
from __future__ import annotations

from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class EraseUserRequest(BaseModel):
    target_user_id: str = Field(description="User ID to erase. Must be own ID or SystemAdmin.")


class ErasureReceiptResponse(BaseModel):
    erasure_id: str
    user_id: str
    cvs_deleted: int
    records_deleted: int
    completed_at: str
    status: str

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "ErasureReceiptResponse":
        return cls(
            erasure_id=d["erasure_id"],
            user_id=d["user_id"],
            cvs_deleted=d["cvs_deleted"],
            records_deleted=d["records_deleted"],
            completed_at=d["completed_at"],
            status=d["status"],
        )


class ConsentRequest(BaseModel):
    level: int = Field(
        ge=1, le=3,
        description="Consent level: 1=Essential (cannot be refused), 2=Functional, 3=Analytics",
    )
    granted: bool = Field(description="True to grant consent, False to withdraw")


class ConsentRecordResponse(BaseModel):
    record_id: str
    user_id: str
    level: int
    granted: bool
    recorded_at: str
    ip_address: str = ""
    user_agent: str = ""
    withdrawn_at: Optional[str] = None

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "ConsentRecordResponse":
        return cls(
            record_id=d["record_id"],
            user_id=d["user_id"],
            level=d["level"],
            granted=d["granted"],
            recorded_at=d["recorded_at"],
            ip_address=d.get("ip_address", ""),
            user_agent=d.get("user_agent", ""),
            withdrawn_at=d.get("withdrawn_at"),
        )


class ConsentStatusResponse(BaseModel):
    """Current consent state for the authenticated user, one field per level."""
    essential: bool    # Level 1 — always True (cannot be refused)
    functional: bool   # Level 2 — opt-in
    analytics: bool    # Level 3 — opt-in

    @classmethod
    def from_state(cls, state: Dict[int, bool]) -> "ConsentStatusResponse":
        return cls(
            essential=state.get(1, True),
            functional=state.get(2, False),
            analytics=state.get(3, False),
        )
