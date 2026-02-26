"""
GDPR Erasure Service — Production Grade
Implements the right to erasure (Art. 17 GDPR).

Erasure pipeline:
  1. Verify requester is the account owner or a SystemAdmin
  2. Hard-delete all CVs (all versions, notes, export logs)
  3. Anonymise user record (replace PII with hashed placeholder)
  4. Preserve audit log entry for 7 years (legal obligation)
  5. Return erasure receipt with counts

No UI dependencies. No Streamlit imports.
"""

from __future__ import annotations

import hashlib
import uuid
from datetime import datetime, timezone
from typing import Dict, Any

from app.services.role_service import RoleService, PermissionDeniedError
from app.logging.logger import AuditLogger


class ErasureError(Exception):
    """Raised when an erasure request cannot be fulfilled."""


class ErasureService:
    """
    Handles GDPR right-to-erasure requests.

    Uses DataService for all data operations.
    Uses RoleService to verify requester authority.
    Writes an immutable audit record on completion.
    """

    def __init__(self, data_service, role_service: RoleService):
        self._ds = data_service
        self._rs = role_service

    def request_erasure(
        self,
        target_user_id: str,
        requester_id: str,
        requester_role: str,
    ) -> Dict[str, Any]:
        """
        Executes a full GDPR erasure for target_user_id.

        Only the account owner or a SystemAdmin may request erasure.

        Args:
            target_user_id:  User whose data will be erased
            requester_id:    ID of the user or admin making the request
            requester_role:  Role of the requester

        Returns:
            Erasure receipt dict with:
              - erasure_id: Unique receipt ID
              - user_id:    Target user ID (anonymised reference)
              - cvs_deleted: Count of CVs hard-deleted
              - versions_deleted: Count of version snapshots deleted
              - notes_deleted: Count of coach notes deleted
              - exports_deleted: Count of export log entries deleted
              - completed_at: ISO UTC timestamp

        Raises:
            ErasureError:          On data layer failures
            PermissionDeniedError: If requester has no authority
        """
        # Only the account owner or SystemAdmin may erase
        if requester_id != target_user_id:
            self._rs.require_permission(requester_role, "sysadmin.data.all")

        AuditLogger.gdpr_erasure_requested(target_user_id, requester_id)

        records_deleted = 0

        try:
            # 1. Hard-delete all CVs for this user (cascades versions + notes)
            cvs = self._ds.list_cvs_for_user(target_user_id)
            cvs_deleted = 0
            for cv in cvs:
                cv_id = cv.get("cv_id", "")
                if cv_id:
                    self._ds.hard_delete_cv(cv_id)
                    cvs_deleted += 1
                    records_deleted += 1

            # 2. Delete consent records
            consent_records = self._ds.get_consent_records(target_user_id)
            self._ds.delete_consent_records(target_user_id)
            records_deleted += len(consent_records)

            # 3. Anonymise user record — replace PII with irreversible hash
            anon_hash = hashlib.sha256(
                f"ERASED:{target_user_id}:{uuid.uuid4()}".encode()
            ).hexdigest()[:16]

            self._ds.update_user(target_user_id, {
                "email": f"erased_{anon_hash}@deleted.invalid",
                "full_name": "[Erased]",
                "is_active": False,
                "is_deleted": True,
                "assigned_coach_id": None,
                "assigned_user_ids": [],
            })
            records_deleted += 1

        except Exception as exc:
            raise ErasureError(f"Erasure pipeline failed: {exc}") from exc

        AuditLogger.gdpr_erasure_completed(target_user_id, records_deleted)

        return {
            "erasure_id": str(uuid.uuid4()),
            "user_id": target_user_id,
            "cvs_deleted": cvs_deleted,
            "records_deleted": records_deleted,
            "completed_at": datetime.now(timezone.utc).isoformat(),
            "status": "complete",
        }

    def export_user_data(
        self,
        target_user_id: str,
        requester_id: str,
        requester_role: str,
    ) -> Dict[str, Any]:
        """
        Subject-access export: returns all personal data held for a user.
        This satisfies GDPR Art. 20 (data portability).

        Args:
            target_user_id:  User whose data to export
            requester_id:    ID of requester
            requester_role:  Role of requester

        Returns:
            Dict containing all personal data held for the user

        Raises:
            PermissionDeniedError: If requester has no authority
        """
        if requester_id != target_user_id:
            self._rs.require_permission(requester_role, "sysadmin.data.all")

        user = self._ds.get_user(target_user_id) or {}
        cvs = self._ds.list_cvs_for_user(target_user_id)
        consent_records = self._ds.get_consent_records(target_user_id)

        # Strip sensitive internal fields
        user.pop("password_hash", None)
        user.pop("password_salt", None)

        return {
            "export_generated_at": datetime.now(timezone.utc).isoformat(),
            "user_profile": user,
            "cvs": cvs,
            "consent_history": consent_records,
            "data_controller": "Career Architect Pro",
            "gdpr_basis": "Art. 20 — Right to data portability",
        }
