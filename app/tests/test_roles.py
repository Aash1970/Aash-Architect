"""
Test Suite: Role & Permission System
Covers app/roles/permission_matrix.py and app/services/role_service.py
"""

import pytest
from app.roles.permission_matrix import (
    has_permission, role_gte, get_role_permissions,
    validate_role, PERMISSIONS, ROLE_HIERARCHY, ALL_PERMISSIONS
)
from app.services.role_service import RoleService, PermissionDeniedError


# ── Permission Matrix ────────────────────────────────────────────────────────

class TestPermissionMatrix:
    def test_user_can_create_cv(self):
        assert has_permission("User", "cv.create") is True

    def test_user_cannot_access_admin_panel(self):
        assert has_permission("User", "admin.panel.access") is False

    def test_user_cannot_access_sysadmin_panel(self):
        assert has_permission("User", "sysadmin.panel.access") is False

    def test_coach_can_read_assigned(self):
        assert has_permission("Coach", "cv.read_assigned") is True

    def test_coach_cannot_access_admin_panel(self):
        assert has_permission("Coach", "admin.panel.access") is False

    def test_admin_can_access_admin_panel(self):
        assert has_permission("Admin", "admin.panel.access") is True

    def test_admin_cannot_access_sysadmin_panel(self):
        assert has_permission("Admin", "sysadmin.panel.access") is False

    def test_admin_cannot_delete_users(self):
        # Hard delete is SystemAdmin only
        assert has_permission("Admin", "user.delete") is False

    def test_sysadmin_has_full_access(self):
        critical_perms = [
            "sysadmin.panel.access",
            "sysadmin.retention.override",
            "sysadmin.data.all",
            "sysadmin.language.control",
            "sysadmin.tier.manage",
            "sysadmin.user.impersonate",
            "user.delete",
            "cv.read_all",
            "admin.panel.access",
        ]
        for perm in critical_perms:
            assert has_permission("SystemAdmin", perm) is True, (
                f"SystemAdmin should have '{perm}'"
            )

    def test_unknown_role_returns_false(self):
        assert has_permission("SuperUser", "cv.create") is False

    def test_unknown_permission_returns_false(self):
        assert has_permission("Admin", "make.coffee") is False

    def test_all_permissions_covered_in_matrix(self):
        """Every known permission must appear in all role matrices."""
        for role in PERMISSIONS:
            for perm in ALL_PERMISSIONS:
                assert perm in PERMISSIONS[role], (
                    f"Permission '{perm}' missing from '{role}' matrix"
                )


# ── Role Hierarchy ───────────────────────────────────────────────────────────

class TestRoleHierarchy:
    def test_sysadmin_above_admin(self):
        assert role_gte("SystemAdmin", "Admin") is True

    def test_admin_above_coach(self):
        assert role_gte("Admin", "Coach") is True

    def test_coach_above_user(self):
        assert role_gte("Coach", "User") is True

    def test_user_not_above_coach(self):
        assert role_gte("User", "Coach") is False

    def test_same_role_returns_true(self):
        for role in ["User", "Coach", "Admin", "SystemAdmin"]:
            assert role_gte(role, role) is True

    def test_unknown_role_returns_false(self):
        assert role_gte("Unknown", "User") is False


# ── validate_role ────────────────────────────────────────────────────────────

class TestValidateRole:
    def test_valid_roles(self):
        for role in ["User", "Coach", "Admin", "SystemAdmin"]:
            assert validate_role(role) is True

    def test_invalid_roles(self):
        for role in ["superuser", "guest", "root", "", "ADMIN"]:
            assert validate_role(role) is False


# ── get_role_permissions ──────────────────────────────────────────────────────

class TestGetRolePermissions:
    def test_returns_dict_for_valid_role(self):
        perms = get_role_permissions("User")
        assert isinstance(perms, dict)
        assert "cv.create" in perms

    def test_returns_empty_for_invalid_role(self):
        perms = get_role_permissions("invalid_role")
        assert perms == {}


# ── RoleService ───────────────────────────────────────────────────────────────

class TestRoleService:
    def setup_method(self):
        self.svc = RoleService()

    def test_check_permission_true(self):
        assert self.svc.check_permission("Admin", "admin.panel.access") is True

    def test_check_permission_false(self):
        assert self.svc.check_permission("User", "admin.panel.access") is False

    def test_require_permission_passes(self):
        self.svc.require_permission("Admin", "admin.panel.access")  # should not raise

    def test_require_permission_raises(self):
        with pytest.raises(PermissionDeniedError) as exc_info:
            self.svc.require_permission("User", "admin.panel.access")
        assert exc_info.value.role == "User"
        assert exc_info.value.permission == "admin.panel.access"

    def test_is_at_least_true(self):
        assert self.svc.is_at_least("Admin", "Coach") is True

    def test_is_at_least_false(self):
        assert self.svc.is_at_least("User", "Admin") is False

    def test_require_minimum_role_passes(self):
        self.svc.require_minimum_role("Admin", "Coach")  # should not raise

    def test_require_minimum_role_raises(self):
        with pytest.raises(PermissionDeniedError):
            self.svc.require_minimum_role("User", "Admin")

    def test_can_access_own_cv(self):
        assert self.svc.can_access_cv("User", "u1", "u1") is True

    def test_user_cannot_access_others_cv(self):
        # User role can only read own — they don't have cv.read_all or cv.read_assigned
        assert self.svc.can_access_cv("User", "u1", "u2") is False

    def test_admin_can_access_any_cv(self):
        assert self.svc.can_access_cv("Admin", "u1", "u2") is True

    def test_can_modify_own_cv(self):
        assert self.svc.can_modify_cv("User", "u1", "u1") is True

    def test_user_cannot_modify_others_cv(self):
        assert self.svc.can_modify_cv("User", "u1", "u2") is False

    def test_admin_can_modify_any_cv(self):
        assert self.svc.can_modify_cv("Admin", "u1", "u2") is True

    def test_can_delete_own_cv(self):
        assert self.svc.can_delete_cv("User", "u1", "u1") is True

    def test_user_cannot_delete_others_cv(self):
        assert self.svc.can_delete_cv("User", "u1", "u2") is False

    def test_validate_role_string(self):
        assert self.svc.validate_role_string("Admin") is True
        assert self.svc.validate_role_string("Hacker") is False
