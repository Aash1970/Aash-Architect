"""
CV Versioning — Production Grade
CV version increments on every save.
Maintains a history of CV states for audit and rollback.
No UI dependencies. Pure Python service layer module.
"""

from __future__ import annotations

import copy
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional


@dataclass
class CVVersion:
    """
    Represents a single version snapshot of a CV.

    Attributes:
        version_id:   Unique ID for this version record
        cv_id:        ID of the parent CV
        version_num:  Monotonically incrementing version number (starts at 1)
        snapshot:     Full CV dict at time of save
        saved_at:     UTC ISO timestamp when this version was saved
        saved_by:     user_id of who performed the save
        is_deleted:   Soft delete flag
        change_note:  Optional human-readable note about this version
    """
    version_id: str
    cv_id: str
    version_num: int
    snapshot: Dict[str, Any]
    saved_at: str
    saved_by: str
    is_deleted: bool = False
    change_note: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "version_id": self.version_id,
            "cv_id": self.cv_id,
            "version_num": self.version_num,
            "snapshot": self.snapshot,
            "saved_at": self.saved_at,
            "saved_by": self.saved_by,
            "is_deleted": self.is_deleted,
            "change_note": self.change_note,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CVVersion":
        return cls(
            version_id=data["version_id"],
            cv_id=data["cv_id"],
            version_num=data["version_num"],
            snapshot=data["snapshot"],
            saved_at=data["saved_at"],
            saved_by=data["saved_by"],
            is_deleted=data.get("is_deleted", False),
            change_note=data.get("change_note"),
        )


class VersioningService:
    """
    Manages CV versioning lifecycle.

    In-memory implementation used by tests and local mode.
    In production, the data_service replaces the in-memory store with DB calls.
    """

    def __init__(self):
        # version_store: cv_id → list of CVVersion (sorted ascending by version_num)
        self._store: Dict[str, List[CVVersion]] = {}

    def create_version(
        self,
        cv_dict: Dict[str, Any],
        cv_id: str,
        saved_by: str,
        change_note: Optional[str] = None,
    ) -> CVVersion:
        """
        Creates and stores a new version snapshot for a CV.
        Increments version number automatically.

        Args:
            cv_dict:     Current state of the CV (will be deep-copied)
            cv_id:       ID of the CV
            saved_by:    user_id performing the save
            change_note: Optional note describing what changed

        Returns:
            The newly created CVVersion
        """
        history = self._store.get(cv_id, [])
        next_version_num = (
            max((v.version_num for v in history), default=0) + 1
        )

        version = CVVersion(
            version_id=str(uuid.uuid4()),
            cv_id=cv_id,
            version_num=next_version_num,
            snapshot=copy.deepcopy(cv_dict),
            saved_at=datetime.now(timezone.utc).isoformat(),
            saved_by=saved_by,
            is_deleted=False,
            change_note=change_note,
        )

        if cv_id not in self._store:
            self._store[cv_id] = []
        self._store[cv_id].append(version)

        return version

    def get_history(
        self,
        cv_id: str,
        include_deleted: bool = False,
    ) -> List[CVVersion]:
        """
        Returns all versions for a CV, newest first.

        Args:
            cv_id:           ID of the CV
            include_deleted: If True, include soft-deleted versions

        Returns:
            List of CVVersion sorted by version_num descending
        """
        history = self._store.get(cv_id, [])
        if not include_deleted:
            history = [v for v in history if not v.is_deleted]
        return sorted(history, key=lambda v: v.version_num, reverse=True)

    def get_version(
        self,
        cv_id: str,
        version_num: int,
    ) -> Optional[CVVersion]:
        """
        Retrieves a specific version by number.

        Returns:
            CVVersion or None if not found
        """
        for v in self._store.get(cv_id, []):
            if v.version_num == version_num:
                return v
        return None

    def get_latest_version(self, cv_id: str) -> Optional[CVVersion]:
        """Returns the most recent non-deleted version of a CV."""
        history = self.get_history(cv_id, include_deleted=False)
        return history[0] if history else None

    def soft_delete_version(
        self, cv_id: str, version_num: int, deleted_by: str
    ) -> bool:
        """
        Soft-deletes a specific version.

        Returns:
            True if found and deleted, False if not found
        """
        for v in self._store.get(cv_id, []):
            if v.version_num == version_num and not v.is_deleted:
                v.is_deleted = True
                return True
        return False

    def restore_version(
        self,
        cv_id: str,
        version_num: int,
        restored_by: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Restores a CV to a specific historical version.
        Creates a new version snapshot with the old data.

        Returns:
            New CVVersion dict (the restored state as a new save), or None
        """
        target = self.get_version(cv_id, version_num)
        if not target:
            return None

        restored = self.create_version(
            cv_dict=target.snapshot,
            cv_id=cv_id,
            saved_by=restored_by,
            change_note=f"Restored from version {version_num}",
        )
        return restored.to_dict()

    def purge_versions_older_than(
        self,
        cv_id: str,
        retention_days: int,
        override_by: Optional[str] = None,
    ) -> int:
        """
        Hard-deletes version records older than retention_days.
        Requires SystemAdmin override_by to hard-delete non-soft-deleted records.

        Args:
            cv_id:          CV to purge versions for
            retention_days: Age threshold in days
            override_by:    SystemAdmin user_id for override; required for hard purge

        Returns:
            Number of versions purged
        """
        from datetime import timedelta

        cutoff = datetime.now(timezone.utc) - timedelta(days=retention_days)
        to_purge: List[CVVersion] = []

        for v in self._store.get(cv_id, []):
            try:
                saved = datetime.fromisoformat(v.saved_at)
                if saved < cutoff and (v.is_deleted or override_by):
                    to_purge.append(v)
            except (ValueError, TypeError):
                continue

        purged = len(to_purge)
        remaining = [
            v for v in self._store.get(cv_id, []) if v not in to_purge
        ]
        self._store[cv_id] = remaining
        return purged


def increment_version(current_version: int) -> int:
    """
    Simple version number incrementer.
    Used in CV dict before saving.
    """
    return current_version + 1
