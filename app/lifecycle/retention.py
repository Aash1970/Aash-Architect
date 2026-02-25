"""
Retention Policy — Production Grade
Configurable retention rules per tier.
SystemAdmin can override retention settings.
Soft delete required before hard delete.
No UI dependencies.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List, Optional


@dataclass
class RetentionPolicy:
    """
    Defines how long CV data and versions are kept.

    Attributes:
        tier:                Tier this policy applies to
        cv_version_days:     Days to keep CV version history
        deleted_cv_days:     Days to keep soft-deleted CVs before hard delete
        export_log_days:     Days to keep export audit logs
        allow_override:      Whether SystemAdmin can override these limits
    """
    tier: str
    cv_version_days: int
    deleted_cv_days: int
    export_log_days: int
    allow_override: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tier": self.tier,
            "cv_version_days": self.cv_version_days,
            "deleted_cv_days": self.deleted_cv_days,
            "export_log_days": self.export_log_days,
            "allow_override": self.allow_override,
        }


# ── Default policies per tier ────────────────────────────────────────────────
DEFAULT_POLICIES: Dict[str, RetentionPolicy] = {
    "Free": RetentionPolicy(
        tier="Free",
        cv_version_days=7,
        deleted_cv_days=30,
        export_log_days=30,
        allow_override=True,
    ),
    "Premium": RetentionPolicy(
        tier="Premium",
        cv_version_days=90,
        deleted_cv_days=90,
        export_log_days=180,
        allow_override=True,
    ),
    "Enterprise": RetentionPolicy(
        tier="Enterprise",
        cv_version_days=365,
        deleted_cv_days=365,
        export_log_days=365,
        allow_override=True,
    ),
}


class RetentionService:
    """
    Manages retention policies and their application.

    Supports:
      - Policy lookup by tier
      - Dynamic policy override by SystemAdmin
      - Scheduled retention enforcement (called by background jobs)
    """

    def __init__(self):
        # Mutable copy of default policies; SystemAdmin can update these
        self._policies: Dict[str, RetentionPolicy] = {
            k: RetentionPolicy(**v.to_dict())
            for k, v in DEFAULT_POLICIES.items()
        }
        # Override registry: user_id → custom policy
        self._overrides: Dict[str, RetentionPolicy] = {}

    def get_policy(self, tier: str) -> RetentionPolicy:
        """Returns the active retention policy for a tier."""
        return self._policies.get(tier, DEFAULT_POLICIES["Free"])

    def update_policy(
        self,
        tier: str,
        cv_version_days: Optional[int] = None,
        deleted_cv_days: Optional[int] = None,
        export_log_days: Optional[int] = None,
        updated_by_sysadmin: str = "",
    ) -> RetentionPolicy:
        """
        Updates retention policy for a tier.
        Only callable by SystemAdmin (enforced in service layer, not here).

        Returns updated policy.
        """
        if tier not in self._policies:
            raise ValueError(f"Unknown tier: {tier}")

        policy = self._policies[tier]
        if cv_version_days is not None:
            if cv_version_days < 1:
                raise ValueError("cv_version_days must be at least 1.")
            object.__setattr__(policy, "cv_version_days", cv_version_days) if hasattr(policy, '__setattr__') else None
            self._policies[tier] = RetentionPolicy(
                tier=tier,
                cv_version_days=cv_version_days,
                deleted_cv_days=policy.deleted_cv_days,
                export_log_days=policy.export_log_days,
                allow_override=policy.allow_override,
            )
            policy = self._policies[tier]

        if deleted_cv_days is not None:
            if deleted_cv_days < 1:
                raise ValueError("deleted_cv_days must be at least 1.")
            self._policies[tier] = RetentionPolicy(
                tier=tier,
                cv_version_days=policy.cv_version_days,
                deleted_cv_days=deleted_cv_days,
                export_log_days=policy.export_log_days,
                allow_override=policy.allow_override,
            )
            policy = self._policies[tier]

        if export_log_days is not None:
            if export_log_days < 1:
                raise ValueError("export_log_days must be at least 1.")
            self._policies[tier] = RetentionPolicy(
                tier=tier,
                cv_version_days=policy.cv_version_days,
                deleted_cv_days=policy.deleted_cv_days,
                export_log_days=export_log_days,
                allow_override=policy.allow_override,
            )

        return self._policies[tier]

    def set_user_override(
        self,
        user_id: str,
        tier: str,
        cv_version_days: int,
        sysadmin_id: str,
    ) -> RetentionPolicy:
        """
        Sets a per-user retention override (SystemAdmin only).

        Returns the custom policy.
        """
        custom = RetentionPolicy(
            tier=tier,
            cv_version_days=cv_version_days,
            deleted_cv_days=self.get_policy(tier).deleted_cv_days,
            export_log_days=self.get_policy(tier).export_log_days,
            allow_override=True,
        )
        self._overrides[user_id] = custom
        return custom

    def get_effective_policy(self, user_id: str, tier: str) -> RetentionPolicy:
        """
        Returns the effective retention policy for a specific user.
        Per-user override takes precedence over tier default.
        """
        if user_id in self._overrides:
            return self._overrides[user_id]
        return self.get_policy(tier)

    def should_purge_version(
        self,
        saved_at: str,
        policy: RetentionPolicy,
    ) -> bool:
        """
        Returns True if a version record should be purged based on policy.

        Args:
            saved_at: ISO timestamp of the version
            policy:   Applicable retention policy
        """
        try:
            saved = datetime.fromisoformat(saved_at)
            if saved.tzinfo is None:
                saved = saved.replace(tzinfo=timezone.utc)
            cutoff = datetime.now(timezone.utc) - timedelta(
                days=policy.cv_version_days
            )
            return saved < cutoff
        except (ValueError, TypeError):
            return False

    def should_hard_delete_cv(
        self,
        deleted_at: str,
        policy: RetentionPolicy,
    ) -> bool:
        """
        Returns True if a soft-deleted CV should be permanently deleted.

        Args:
            deleted_at: ISO timestamp of soft deletion
            policy:     Applicable retention policy
        """
        try:
            deleted = datetime.fromisoformat(deleted_at)
            if deleted.tzinfo is None:
                deleted = deleted.replace(tzinfo=timezone.utc)
            cutoff = datetime.now(timezone.utc) - timedelta(
                days=policy.deleted_cv_days
            )
            return deleted < cutoff
        except (ValueError, TypeError):
            return False

    def list_policies(self) -> List[Dict[str, Any]]:
        """Returns all active tier policies as a list of dicts."""
        return [p.to_dict() for p in self._policies.values()]


def apply_retention_policy(
    records: List[Dict[str, Any]],
    policy: RetentionPolicy,
    date_field: str = "saved_at",
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Applies a retention policy to a list of records.

    Args:
        records:    List of dicts, each with a date_field timestamp
        policy:     RetentionPolicy to apply
        date_field: Name of the timestamp field to check

    Returns:
        Dict with 'keep' and 'purge' lists
    """
    service = RetentionService()
    keep: List[Dict[str, Any]] = []
    purge: List[Dict[str, Any]] = []

    for record in records:
        ts = record.get(date_field, "")
        if service.should_purge_version(ts, policy):
            purge.append(record)
        else:
            keep.append(record)

    return {"keep": keep, "purge": purge}
