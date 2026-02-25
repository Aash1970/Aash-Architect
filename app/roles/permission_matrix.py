"""
Role Permission Matrix — Production Grade
Central authority for all permission checks.
NO hardcoded permissions anywhere else in the codebase.
All permission checks MUST call has_permission() from this module.

Roles:
  User        — Standard authenticated user
  Coach       — CV reviewer assigned to users
  Admin       — Platform administrator
  SystemAdmin — Super administrator with override capabilities
"""

from typing import Dict, Set

# ── Role hierarchy (higher value = more authority) ─────────────────────────
ROLE_HIERARCHY: Dict[str, int] = {
    "User": 1,
    "Coach": 2,
    "Admin": 3,
    "SystemAdmin": 4,
}

# ── Permission catalogue ────────────────────────────────────────────────────
ALL_PERMISSIONS: Set[str] = {
    # CV operations — own
    "cv.create",
    "cv.read_own",
    "cv.update_own",
    "cv.delete_own",
    "cv.export_own",
    "cv.submit_to_coach",
    # CV operations — assigned (Coach)
    "cv.read_assigned",
    "cv.comment_assigned",
    # CV operations — all (Admin+)
    "cv.read_all",
    "cv.update_all",
    "cv.delete_all",
    # ATS
    "ats.basic",
    "ats.advanced",
    "ats.analytics",
    # Coach management
    "coach.view_assigned_users",
    "coach.submit_feedback",
    # User management
    "user.list",
    "user.create",
    "user.update",
    "user.deactivate",
    "user.delete",
    "user.assign_coach",
    "user.change_role",
    "user.change_tier",
    # Admin panel
    "admin.panel.access",
    "admin.metrics.view",
    "admin.coach.manage",
    "admin.export.reports",
    # SystemAdmin exclusives
    "sysadmin.panel.access",
    "sysadmin.retention.override",
    "sysadmin.data.all",
    "sysadmin.language.control",
    "sysadmin.tier.manage",
    "sysadmin.user.impersonate",
}

# ── Permission matrix ───────────────────────────────────────────────────────
PERMISSIONS: Dict[str, Dict[str, bool]] = {
    "User": {
        "cv.create": True,
        "cv.read_own": True,
        "cv.update_own": True,
        "cv.delete_own": True,
        "cv.export_own": True,
        "cv.submit_to_coach": False,   # unlocked at Premium tier
        "cv.read_assigned": False,
        "cv.comment_assigned": False,
        "cv.read_all": False,
        "cv.update_all": False,
        "cv.delete_all": False,
        "ats.basic": False,            # unlocked at Premium tier
        "ats.advanced": False,
        "ats.analytics": False,
        "coach.view_assigned_users": False,
        "coach.submit_feedback": False,
        "user.list": False,
        "user.create": False,
        "user.update": False,
        "user.deactivate": False,
        "user.delete": False,
        "user.assign_coach": False,
        "user.change_role": False,
        "user.change_tier": False,
        "admin.panel.access": False,
        "admin.metrics.view": False,
        "admin.coach.manage": False,
        "admin.export.reports": False,
        "sysadmin.panel.access": False,
        "sysadmin.retention.override": False,
        "sysadmin.data.all": False,
        "sysadmin.language.control": False,
        "sysadmin.tier.manage": False,
        "sysadmin.user.impersonate": False,
    },
    "Coach": {
        "cv.create": True,
        "cv.read_own": True,
        "cv.update_own": True,
        "cv.delete_own": True,
        "cv.export_own": True,
        "cv.submit_to_coach": True,
        "cv.read_assigned": True,
        "cv.comment_assigned": True,
        "cv.read_all": False,
        "cv.update_all": False,
        "cv.delete_all": False,
        "ats.basic": True,
        "ats.advanced": False,
        "ats.analytics": False,
        "coach.view_assigned_users": True,
        "coach.submit_feedback": True,
        "user.list": False,
        "user.create": False,
        "user.update": False,
        "user.deactivate": False,
        "user.delete": False,
        "user.assign_coach": False,
        "user.change_role": False,
        "user.change_tier": False,
        "admin.panel.access": False,
        "admin.metrics.view": False,
        "admin.coach.manage": False,
        "admin.export.reports": False,
        "sysadmin.panel.access": False,
        "sysadmin.retention.override": False,
        "sysadmin.data.all": False,
        "sysadmin.language.control": False,
        "sysadmin.tier.manage": False,
        "sysadmin.user.impersonate": False,
    },
    "Admin": {
        "cv.create": True,
        "cv.read_own": True,
        "cv.update_own": True,
        "cv.delete_own": True,
        "cv.export_own": True,
        "cv.submit_to_coach": True,
        "cv.read_assigned": True,
        "cv.comment_assigned": True,
        "cv.read_all": True,
        "cv.update_all": True,
        "cv.delete_all": True,
        "ats.basic": True,
        "ats.advanced": True,
        "ats.analytics": True,
        "coach.view_assigned_users": True,
        "coach.submit_feedback": True,
        "user.list": True,
        "user.create": True,
        "user.update": True,
        "user.deactivate": True,
        "user.delete": False,          # SystemAdmin only
        "user.assign_coach": True,
        "user.change_role": True,
        "user.change_tier": True,
        "admin.panel.access": True,
        "admin.metrics.view": True,
        "admin.coach.manage": True,
        "admin.export.reports": True,
        "sysadmin.panel.access": False,
        "sysadmin.retention.override": False,
        "sysadmin.data.all": False,
        "sysadmin.language.control": False,
        "sysadmin.tier.manage": False,
        "sysadmin.user.impersonate": False,
    },
    "SystemAdmin": {
        "cv.create": True,
        "cv.read_own": True,
        "cv.update_own": True,
        "cv.delete_own": True,
        "cv.export_own": True,
        "cv.submit_to_coach": True,
        "cv.read_assigned": True,
        "cv.comment_assigned": True,
        "cv.read_all": True,
        "cv.update_all": True,
        "cv.delete_all": True,
        "ats.basic": True,
        "ats.advanced": True,
        "ats.analytics": True,
        "coach.view_assigned_users": True,
        "coach.submit_feedback": True,
        "user.list": True,
        "user.create": True,
        "user.update": True,
        "user.deactivate": True,
        "user.delete": True,
        "user.assign_coach": True,
        "user.change_role": True,
        "user.change_tier": True,
        "admin.panel.access": True,
        "admin.metrics.view": True,
        "admin.coach.manage": True,
        "admin.export.reports": True,
        "sysadmin.panel.access": True,
        "sysadmin.retention.override": True,
        "sysadmin.data.all": True,
        "sysadmin.language.control": True,
        "sysadmin.tier.manage": True,
        "sysadmin.user.impersonate": True,
    },
}


def has_permission(role: str, permission: str) -> bool:
    """
    Central permission check. All access control MUST use this function.

    Args:
        role:       Role string ('User' | 'Coach' | 'Admin' | 'SystemAdmin')
        permission: Permission key from ALL_PERMISSIONS catalogue

    Returns:
        True if the role has the given permission, False otherwise.
    """
    if role not in PERMISSIONS:
        return False
    if permission not in ALL_PERMISSIONS:
        return False
    return PERMISSIONS[role].get(permission, False)


def role_gte(role_a: str, role_b: str) -> bool:
    """
    Returns True if role_a has equal or higher authority than role_b.
    Used for hierarchical access checks.
    """
    return ROLE_HIERARCHY.get(role_a, 0) >= ROLE_HIERARCHY.get(role_b, 0)


def get_role_permissions(role: str) -> Dict[str, bool]:
    """
    Returns the full permission dict for a given role.
    Returns empty dict for unknown roles.
    """
    return PERMISSIONS.get(role, {})


def validate_role(role: str) -> bool:
    """Returns True if the role string is a recognised role."""
    return role in PERMISSIONS
