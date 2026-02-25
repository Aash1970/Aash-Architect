"""
CV Service — Production Grade
All CV CRUD, export, and coach operations.
Enforces role checks, tier checks, and validation before any write.
No UI imports.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

from app.models.cv_model import CVModel
from app.services.data_service import DataService
from app.services.role_service import RoleService, PermissionDeniedError
from app.services.tier_service import TierService
from app.validation.validators import (
    validate_personal_info, ValidationError
)
from app.lifecycle.versioning import VersioningService, increment_version
from app.security.package_builder import PackageBuilder, PackageError
from app.tier.tier_rules import TierGateError


class CVServiceError(Exception):
    """Raised on CV service operation failures."""


class CVService:
    """
    Orchestrates CV operations with full enforcement of:
      - Role-based access control (via RoleService)
      - Tier limits (via TierService)
      - Validation (via validators)
      - Versioning (via VersioningService)
      - Encryption for exports (via PackageBuilder)
    """

    def __init__(
        self,
        data_service: DataService,
        role_service: RoleService,
        tier_service: TierService,
        versioning_service: VersioningService,
        package_builder: PackageBuilder,
    ):
        self._ds = data_service
        self._rs = role_service
        self._ts = tier_service
        self._vs = versioning_service
        self._pb = package_builder

    # ── CV CRUD ──────────────────────────────────────────────────────────────

    def create_cv(
        self,
        cv_data: Dict[str, Any],
        requester_id: str,
        requester_role: str,
        requester_tier: str,
    ) -> Dict[str, Any]:
        """
        Creates a new CV.

        Enforces:
          - Role: cv.create permission
          - Tier: CV count limit
          - Validation: personal info required fields

        Returns the created CV dict.
        """
        self._rs.require_permission(requester_role, "cv.create")
        self._ts.assert_can_create_cv(requester_id, requester_tier)

        pi = cv_data.get("personal_info", {})
        errors = validate_personal_info(pi)
        if errors:
            raise ValidationError(errors)

        cv_data["user_id"] = requester_id
        cv_data["tier"] = requester_tier
        cv_data["version"] = 1
        cv_data.setdefault("cv_id", str(uuid.uuid4()))
        cv_data.setdefault("title", "My CV")
        cv_data.setdefault("is_deleted", False)

        created = self._ds.create_cv(cv_data)

        # Save initial version snapshot
        self._vs.create_version(
            cv_dict=created,
            cv_id=created["cv_id"],
            saved_by=requester_id,
            change_note="Initial creation",
        )

        return created

    def get_cv(
        self,
        cv_id: str,
        requester_id: str,
        requester_role: str,
    ) -> Dict[str, Any]:
        """
        Fetches a CV by ID.
        Enforces role-based read access.
        """
        cv = self._ds.get_cv(cv_id)
        if not cv:
            raise CVServiceError(f"CV {cv_id} not found.")

        owner_id = cv["user_id"]
        if not self._rs.can_access_cv(requester_role, requester_id, owner_id):
            raise PermissionDeniedError(requester_role, "cv.read")

        return cv

    def list_cvs(
        self,
        requester_id: str,
        requester_role: str,
        target_user_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Lists CVs. Admins can request all CVs; users only get their own.
        """
        if self._rs.check_permission(requester_role, "cv.read_all"):
            if target_user_id:
                return self._ds.list_cvs_for_user(target_user_id)
            return self._ds.list_all_cvs()

        return self._ds.list_cvs_for_user(requester_id)

    def update_cv(
        self,
        cv_id: str,
        updates: Dict[str, Any],
        requester_id: str,
        requester_role: str,
    ) -> Dict[str, Any]:
        """
        Updates a CV.

        Enforces:
          - Role: cv.update_own or cv.update_all
          - Validation: if personal_info in updates
          - Versioning: creates version snapshot on save
        """
        cv = self._ds.get_cv(cv_id)
        if not cv:
            raise CVServiceError(f"CV {cv_id} not found.")

        owner_id = cv["user_id"]
        if not self._rs.can_modify_cv(requester_role, requester_id, owner_id):
            raise PermissionDeniedError(requester_role, "cv.update")

        # Validate personal info if being updated
        if "personal_info" in updates:
            errors = validate_personal_info(updates["personal_info"])
            if errors:
                raise ValidationError(errors)

        # Increment version number
        current_version = cv.get("version", 1)
        updates["version"] = increment_version(current_version)

        updated = self._ds.update_cv(cv_id, updates)

        # Save version snapshot
        self._vs.create_version(
            cv_dict=updated,
            cv_id=cv_id,
            saved_by=requester_id,
            change_note="Updated",
        )

        return updated

    def delete_cv(
        self,
        cv_id: str,
        requester_id: str,
        requester_role: str,
    ) -> bool:
        """
        Soft-deletes a CV.
        SystemAdmin can hard-delete via admin service.
        """
        cv = self._ds.get_cv(cv_id)
        if not cv:
            raise CVServiceError(f"CV {cv_id} not found.")

        owner_id = cv["user_id"]
        if not self._rs.can_delete_cv(requester_role, requester_id, owner_id):
            raise PermissionDeniedError(requester_role, "cv.delete")

        return self._ds.soft_delete_cv(cv_id)

    # ── Export ───────────────────────────────────────────────────────────────

    def export_cv(
        self,
        cv_id: str,
        requester_id: str,
        requester_role: str,
        requester_tier: str,
        export_format: str = "pdf",
    ) -> bytes:
        """
        Exports a CV as an encrypted package.

        Enforces:
          - Role: cv.export_own
          - Tier: export limits and format restrictions
          - Validation: CV must have complete personal info

        Returns:
            ZIP archive bytes of the encrypted CV package.

        Raises:
            CVServiceError, TierGateError, PackageError, ValidationError
        """
        self._rs.require_permission(requester_role, "cv.export_own")
        self._ts.assert_can_export(requester_id, requester_tier, export_format)

        cv = self.get_cv(cv_id, requester_id, requester_role)

        # Validate CV is exportable
        pi = cv.get("personal_info", {})
        errors = validate_personal_info(pi)
        if errors:
            raise ValidationError(errors)

        # Build encrypted package
        pkg = self._pb.build(
            cv_dict=cv,
            user_id=requester_id,
            tier=requester_tier,
        )

        # Log export
        self._ds.log_export({
            "user_id": requester_id,
            "cv_id": cv_id,
            "format": export_format,
            "package_checksum": pkg.checksum,
        })

        return pkg.archive_bytes

    # ── Coach submission ──────────────────────────────────────────────────────

    def submit_to_coach(
        self,
        cv_id: str,
        coach_id: str,
        requester_id: str,
        requester_role: str,
        requester_tier: str,
    ) -> Dict[str, Any]:
        """
        Assigns a CV to a coach for review.

        Enforces:
          - Role: cv.submit_to_coach
          - Tier: coach_submission feature
        """
        self._rs.require_permission(requester_role, "cv.submit_to_coach")
        self._ts.assert_can_submit_to_coach(requester_tier)

        cv = self.get_cv(cv_id, requester_id, requester_role)
        if cv["user_id"] != requester_id:
            raise PermissionDeniedError(requester_role, "cv.submit_to_coach")

        updated = self._ds.update_cv(cv_id, {
            "assigned_coach_id": coach_id
        })
        return updated

    # ── Coach notes ──────────────────────────────────────────────────────────

    def add_coach_note(
        self,
        cv_id: str,
        note_text: str,
        coach_id: str,
        coach_role: str,
    ) -> Dict[str, Any]:
        """
        Adds a coach note to a CV.

        Enforces:
          - Role: cv.comment_assigned
        """
        self._rs.require_permission(coach_role, "cv.comment_assigned")

        cv = self._ds.get_cv(cv_id)
        if not cv:
            raise CVServiceError(f"CV {cv_id} not found.")
        if cv.get("assigned_coach_id") != coach_id:
            if not self._rs.check_permission(coach_role, "cv.read_all"):
                raise PermissionDeniedError(coach_role, "cv.comment_assigned")

        note = self._ds.save_coach_note({
            "cv_id": cv_id,
            "coach_id": coach_id,
            "note_text": note_text,
        })
        return note

    def get_coach_notes(
        self,
        cv_id: str,
        requester_id: str,
        requester_role: str,
    ) -> List[Dict[str, Any]]:
        """Fetches all coach notes for a CV."""
        cv = self.get_cv(cv_id, requester_id, requester_role)
        return self._ds.get_coach_notes(cv_id)

    # ── Version history ───────────────────────────────────────────────────────

    def get_version_history(
        self,
        cv_id: str,
        requester_id: str,
        requester_role: str,
    ) -> List[Dict[str, Any]]:
        """Returns version history for a CV (newest first)."""
        cv = self.get_cv(cv_id, requester_id, requester_role)
        versions = self._vs.get_history(cv_id)
        return [v.to_dict() for v in versions]
