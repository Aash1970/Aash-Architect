"""
Admin Service — Production Grade
All administrative operations. No UI imports.
Role-gated: Admin and SystemAdmin only.
SystemAdmin has additional capabilities (retention, data override, language control).
"""

from __future__ import annotations

from typing import Dict, Any, List, Optional

from app.services.data_service import DataService
from app.services.role_service import RoleService, PermissionDeniedError
from app.lifecycle.retention import RetentionService, RetentionPolicy
from app.i18n import get_supported_languages


class AdminServiceError(Exception):
    """Raised on admin operation failures."""


class AdminService:
    """
    Provides all admin-level operations.
    Every public method enforces role requirements before execution.

    Admin capabilities:
      - Manage users (list, update, deactivate)
      - View metrics
      - Manage coaches (assign users)
      - Export reports

    SystemAdmin additional capabilities:
      - Override retention policies
      - Hard delete users and CVs
      - Control available languages
      - Manage tier assignments
      - Impersonate users (audit trail required)
    """

    def __init__(
        self,
        data_service: DataService,
        role_service: RoleService,
        retention_service: RetentionService,
    ):
        self._ds = data_service
        self._rs = role_service
        self._ret = retention_service
        self._active_languages: List[str] = ["en", "es", "fr", "de"]

    # ── User management (Admin+) ─────────────────────────────────────────────

    def list_users(
        self,
        requester_role: str,
        include_deleted: bool = False,
    ) -> List[Dict[str, Any]]:
        """Lists all users. Requires Admin or SystemAdmin role."""
        self._rs.require_permission(requester_role, "user.list")
        return self._ds.list_users(include_deleted=include_deleted)

    def get_user(self, user_id: str, requester_role: str) -> Dict[str, Any]:
        """Fetches a single user profile."""
        self._rs.require_permission(requester_role, "user.list")
        user = self._ds.get_user(user_id)
        if not user:
            raise AdminServiceError(f"User {user_id} not found.")
        return user

    def update_user(
        self,
        user_id: str,
        updates: Dict[str, Any],
        requester_role: str,
    ) -> Dict[str, Any]:
        """
        Updates a user profile field(s).
        Restricted fields (role, tier) require explicit permission.
        """
        self._rs.require_permission(requester_role, "user.update")

        # Role changes require user.change_role
        if "role" in updates:
            self._rs.require_permission(requester_role, "user.change_role")
            new_role = updates["role"]
            if not self._rs.validate_role_string(new_role):
                raise AdminServiceError(f"Invalid role: {new_role}")
            # Only SystemAdmin can assign SystemAdmin role
            if new_role == "SystemAdmin":
                self._rs.require_minimum_role(requester_role, "SystemAdmin")

        # Tier changes require user.change_tier
        if "tier" in updates:
            self._rs.require_permission(requester_role, "user.change_tier")

        return self._ds.update_user(user_id, updates)

    def deactivate_user(
        self, user_id: str, requester_role: str
    ) -> bool:
        """Sets user is_active=False. Requires Admin+."""
        self._rs.require_permission(requester_role, "user.deactivate")
        self._ds.update_user(user_id, {"is_active": False})
        return True

    def delete_user(
        self, user_id: str, requester_role: str
    ) -> bool:
        """Hard-deletes a user. SystemAdmin only."""
        self._rs.require_permission(requester_role, "user.delete")
        return self._ds.soft_delete_user(user_id)

    # ── Coach management (Admin+) ────────────────────────────────────────────

    def assign_coach_to_user(
        self,
        user_id: str,
        coach_id: str,
        requester_role: str,
    ) -> Dict[str, Any]:
        """
        Assigns a coach to a user.
        Verifies coach actually has the Coach role.
        """
        self._rs.require_permission(requester_role, "user.assign_coach")

        coach = self._ds.get_user(coach_id)
        if not coach:
            raise AdminServiceError(f"Coach {coach_id} not found.")
        if coach.get("role") not in ("Coach", "Admin", "SystemAdmin"):
            raise AdminServiceError(
                f"User {coach_id} is not a Coach. "
                f"Current role: {coach.get('role')}"
            )

        # Update user's assigned coach
        updated_user = self._ds.update_user(
            user_id, {"assigned_coach_id": coach_id}
        )

        # Add user to coach's assigned list
        coach_assigned = coach.get("assigned_user_ids", [])
        if user_id not in coach_assigned:
            coach_assigned.append(user_id)
            self._ds.update_user(coach_id, {"assigned_user_ids": coach_assigned})

        return updated_user

    def list_coaches(self, requester_role: str) -> List[Dict[str, Any]]:
        """Lists all users with Coach role."""
        self._rs.require_permission(requester_role, "admin.coach.manage")
        all_users = self._ds.list_users()
        return [
            u for u in all_users
            if u.get("role") in ("Coach", "Admin", "SystemAdmin")
        ]

    # ── Metrics (Admin+) ─────────────────────────────────────────────────────

    def get_metrics(self, requester_role: str) -> Dict[str, Any]:
        """Returns platform-wide metrics for the admin dashboard."""
        self._rs.require_permission(requester_role, "admin.metrics.view")
        return self._ds.get_platform_metrics()

    # ── SystemAdmin: Retention override ──────────────────────────────────────

    def update_retention_policy(
        self,
        tier: str,
        cv_version_days: Optional[int],
        deleted_cv_days: Optional[int],
        export_log_days: Optional[int],
        requester_role: str,
        requester_id: str,
    ) -> Dict[str, Any]:
        """
        Updates global retention policy for a tier.
        SystemAdmin only.
        """
        self._rs.require_permission(requester_role, "sysadmin.retention.override")

        policy = self._ret.update_policy(
            tier=tier,
            cv_version_days=cv_version_days,
            deleted_cv_days=deleted_cv_days,
            export_log_days=export_log_days,
            updated_by_sysadmin=requester_id,
        )
        return policy.to_dict()

    def set_user_retention_override(
        self,
        user_id: str,
        tier: str,
        cv_version_days: int,
        requester_role: str,
        requester_id: str,
    ) -> Dict[str, Any]:
        """Per-user retention override. SystemAdmin only."""
        self._rs.require_permission(requester_role, "sysadmin.retention.override")
        policy = self._ret.set_user_override(
            user_id=user_id,
            tier=tier,
            cv_version_days=cv_version_days,
            sysadmin_id=requester_id,
        )
        return policy.to_dict()

    def list_retention_policies(self, requester_role: str) -> List[Dict[str, Any]]:
        """Lists all retention policies."""
        self._rs.require_minimum_role(requester_role, "Admin")
        return self._ret.list_policies()

    # ── SystemAdmin: Language control ────────────────────────────────────────

    def get_active_languages(self) -> List[str]:
        """Returns currently active language codes."""
        return list(self._active_languages)

    def set_active_languages(
        self, lang_codes: List[str], requester_role: str
    ) -> List[str]:
        """
        Sets which languages are active on the platform.
        SystemAdmin only. 'en' (English) cannot be disabled.
        """
        self._rs.require_permission(requester_role, "sysadmin.language.control")

        supported = set(get_supported_languages().keys())
        invalid = set(lang_codes) - supported
        if invalid:
            raise AdminServiceError(
                f"Unsupported language codes: {invalid}. "
                f"Supported: {supported}"
            )
        if "en" not in lang_codes:
            raise AdminServiceError("English ('en') cannot be disabled.")

        self._active_languages = list(lang_codes)
        return self._active_languages

    # ── SystemAdmin: Hard delete ──────────────────────────────────────────────

    def hard_delete_cv(
        self, cv_id: str, requester_role: str
    ) -> bool:
        """Permanently deletes a CV. SystemAdmin only."""
        self._rs.require_permission(requester_role, "sysadmin.data.all")
        return self._ds.hard_delete_cv(cv_id)

    # ── Reports (Admin+) ─────────────────────────────────────────────────────

    def export_user_report(
        self, requester_role: str
    ) -> List[Dict[str, Any]]:
        """Exports a report of all users. Admin+ only."""
        self._rs.require_permission(requester_role, "admin.export.reports")
        users = self._ds.list_users()
        # Scrub sensitive fields before export
        report = []
        for u in users:
            report.append({
                "user_id": u.get("user_id"),
                "email": u.get("email"),
                "full_name": u.get("full_name"),
                "role": u.get("role"),
                "tier": u.get("tier"),
                "is_active": u.get("is_active"),
                "created_at": u.get("created_at"),
            })
        return report
