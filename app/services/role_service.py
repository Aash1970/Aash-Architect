"""
Role Service — Production Grade
Central authority for role-based access control at the service layer.
All permission checks MUST use this service.
UI MUST NOT check permissions directly.
"""

from typing import Optional
from app.roles.permission_matrix import has_permission, role_gte, validate_role


class PermissionDeniedError(Exception):
    """Raised when a user attempts an action beyond their role."""

    def __init__(self, role: str, permission: str):
        self.role = role
        self.permission = permission
        super().__init__(
            f"Role '{role}' does not have permission '{permission}'."
        )


class RoleService:
    """
    Service wrapper for all role and permission operations.
    Used by other services and UI layer (never directly checks matrix in UI).
    """

    def check_permission(self, role: str, permission: str) -> bool:
        """
        Returns True if role has the given permission.
        Does NOT raise — use require_permission for that.
        """
        return has_permission(role, permission)

    def require_permission(self, role: str, permission: str) -> None:
        """
        Asserts that the role has the given permission.

        Raises:
            PermissionDeniedError if not permitted
        """
        if not has_permission(role, permission):
            raise PermissionDeniedError(role, permission)

    def is_at_least(self, role: str, minimum_role: str) -> bool:
        """
        Returns True if role is equal to or higher in hierarchy than minimum_role.
        """
        return role_gte(role, minimum_role)

    def require_minimum_role(self, role: str, minimum_role: str) -> None:
        """
        Asserts that the user's role meets the minimum hierarchy level.

        Raises:
            PermissionDeniedError if role is below minimum
        """
        if not role_gte(role, minimum_role):
            raise PermissionDeniedError(
                role=role,
                permission=f"minimum role: {minimum_role}"
            )

    def can_access_cv(self, role: str, requester_id: str, cv_owner_id: str) -> bool:
        """
        Returns True if the requester can read the given CV.
        Own CV: always True (if cv.read_own permitted).
        Other CVs: requires cv.read_all or cv.read_assigned.
        """
        if requester_id == cv_owner_id:
            return has_permission(role, "cv.read_own")
        if has_permission(role, "cv.read_all"):
            return True
        # Coach with assigned access checked separately in CV service
        return has_permission(role, "cv.read_assigned")

    def can_modify_cv(
        self, role: str, requester_id: str, cv_owner_id: str
    ) -> bool:
        """Returns True if requester can modify the CV."""
        if requester_id == cv_owner_id:
            return has_permission(role, "cv.update_own")
        return has_permission(role, "cv.update_all")

    def can_delete_cv(
        self, role: str, requester_id: str, cv_owner_id: str
    ) -> bool:
        """Returns True if requester can delete the CV."""
        if requester_id == cv_owner_id:
            return has_permission(role, "cv.delete_own")
        return has_permission(role, "cv.delete_all")

    def validate_role_string(self, role: str) -> bool:
        """Returns True if role is a known valid role string."""
        return validate_role(role)
