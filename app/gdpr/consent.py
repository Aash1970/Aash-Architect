"""
GDPR Consent Service — Production Grade
3-level consent model:
  Level 1 — Essential:   Required for service operation. Cannot be refused.
  Level 2 — Functional:  Improves UX (preferences, autosave). Opt-in.
  Level 3 — Analytics:   Platform improvement signals. Opt-in. Enterprise tier records.

Consent choices are stored to the data layer and logged to the audit trail.
No UI dependencies. No Streamlit imports.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import IntEnum
from typing import Dict, Any, List, Optional

from app.logging.logger import AuditLogger


class ConsentLevel(IntEnum):
    ESSENTIAL = 1    # Mandatory — cannot be refused
    FUNCTIONAL = 2   # Opt-in — preferences, autosave
    ANALYTICS = 3    # Opt-in — usage analytics


@dataclass
class ConsentRecord:
    """
    Immutable record of a single consent decision.
    One record per user per level per change event.
    """
    record_id: str
    user_id: str
    level: int              # ConsentLevel value
    granted: bool
    recorded_at: str        # ISO UTC
    ip_address: str = ""
    user_agent: str = ""
    withdrawn_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "record_id": self.record_id,
            "user_id": self.user_id,
            "level": self.level,
            "granted": self.granted,
            "recorded_at": self.recorded_at,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "withdrawn_at": self.withdrawn_at,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "ConsentRecord":
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


class ConsentServiceError(Exception):
    """Raised on consent service failures."""


class ConsentService:
    """
    Manages GDPR consent records for all users.

    Consent is stored via the data_service in a `consent_records` collection.
    Each change event produces a new immutable ConsentRecord (append-only log).
    Level 1 (Essential) consent is always implicitly granted at registration.
    """

    def __init__(self, data_service):
        self._ds = data_service

    # ── Recording ─────────────────────────────────────────────────────────────

    def record_consent(
        self,
        user_id: str,
        level: int,
        granted: bool,
        ip_address: str = "",
        user_agent: str = "",
    ) -> ConsentRecord:
        """
        Records a consent decision for a user at the given level.

        Args:
            user_id:     User making the consent decision
            level:       ConsentLevel (1, 2, or 3)
            granted:     True = consent given, False = consent refused/withdrawn
            ip_address:  Caller IP for audit trail
            user_agent:  Caller user-agent for audit trail

        Returns:
            The stored ConsentRecord

        Raises:
            ConsentServiceError: If level is invalid or Essential is refused
        """
        if level not in (ConsentLevel.ESSENTIAL, ConsentLevel.FUNCTIONAL, ConsentLevel.ANALYTICS):
            raise ConsentServiceError(f"Invalid consent level: {level}")

        if level == ConsentLevel.ESSENTIAL and not granted:
            raise ConsentServiceError(
                "Essential consent (Level 1) is required to use the service "
                "and cannot be refused."
            )

        record = ConsentRecord(
            record_id=str(uuid.uuid4()),
            user_id=user_id,
            level=int(level),
            granted=granted,
            recorded_at=datetime.now(timezone.utc).isoformat(),
            ip_address=ip_address,
            user_agent=user_agent,
        )

        self._ds.save_consent_record(record.to_dict())
        AuditLogger.consent_recorded(user_id, int(level), granted)
        return record

    def record_essential_consent(self, user_id: str, **kwargs) -> ConsentRecord:
        """Shorthand: records Level 1 Essential consent at registration."""
        return self.record_consent(user_id, ConsentLevel.ESSENTIAL, True, **kwargs)

    # ── Querying ──────────────────────────────────────────────────────────────

    def get_current_consent(self, user_id: str) -> Dict[int, bool]:
        """
        Returns the current consent state for all levels for a user.

        Returns:
            Dict mapping level (int) → granted (bool)
            Level 1 always returns True (Essential).
        """
        records = self._ds.get_consent_records(user_id)

        # Build state from most recent record per level
        state: Dict[int, Optional[bool]] = {
            ConsentLevel.ESSENTIAL: True,   # Essential always granted
            ConsentLevel.FUNCTIONAL: None,
            ConsentLevel.ANALYTICS: None,
        }

        # Records are ordered oldest-first; last record per level wins
        for r in records:
            lvl = r.get("level")
            if lvl in state:
                state[lvl] = r.get("granted", False)

        # Default un-decided levels to False (not granted)
        return {k: bool(v) for k, v in state.items()}

    def has_consent(self, user_id: str, level: int) -> bool:
        """Returns True if the user has granted consent at the given level."""
        state = self.get_current_consent(user_id)
        return state.get(level, False)

    def get_audit_log(self, user_id: str) -> List[Dict[str, Any]]:
        """Returns the full immutable consent audit log for a user."""
        return self._ds.get_consent_records(user_id)

    # ── Withdrawal ────────────────────────────────────────────────────────────

    def withdraw_consent(
        self,
        user_id: str,
        level: int,
        ip_address: str = "",
        user_agent: str = "",
    ) -> ConsentRecord:
        """
        Records a consent withdrawal.
        Level 1 cannot be withdrawn (raises ConsentServiceError).
        """
        if level == ConsentLevel.ESSENTIAL:
            raise ConsentServiceError(
                "Essential consent cannot be withdrawn. "
                "To remove all data, submit a GDPR erasure request."
            )
        return self.record_consent(
            user_id, level, False,
            ip_address=ip_address,
            user_agent=user_agent,
        )
