"""Pydantic schemas for /tier routes."""
from __future__ import annotations

from typing import Any, Dict, List

from pydantic import BaseModel


class TierLimitsResponse(BaseModel):
    tier: str
    max_cvs: int  # -1 means unlimited
    max_exports_per_month: int  # -1 means unlimited
    allowed_export_formats: List[str]
    ats_basic: bool
    ats_advanced: bool
    ats_analytics: bool
    coach_submit: bool
    version_history_days: int

    @classmethod
    def from_dict(cls, tier: str, d: Dict[str, Any]) -> "TierLimitsResponse":
        def _int(val: Any, default: int) -> int:
            """Convert 'Unlimited' sentinel or any non-int to -1 (unlimited)."""
            if isinstance(val, int):
                return val
            if isinstance(val, str) and val.lower() in ("unlimited", "∞", "inf"):
                return -1
            try:
                return int(val)
            except (TypeError, ValueError):
                return default

        return cls(
            tier=tier,
            max_cvs=_int(d.get("max_cvs"), 2),
            max_exports_per_month=_int(d.get("max_exports_per_month"), 3),
            allowed_export_formats=d.get("allowed_export_formats", ["pdf"]),
            ats_basic=d.get("ats_basic", False),
            ats_advanced=d.get("ats_advanced", False),
            ats_analytics=d.get("ats_analytics", False),
            coach_submit=d.get("coach_submit", False),
            version_history_days=_int(d.get("version_history_days"), 7),
        )
