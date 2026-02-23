from __future__ import annotations
from db.client import get_client

VALID_ROLES = ("User", "Coach", "Admin", "SystemAdmin")


def fetch_user_role(user_id: str) -> str:
    """
    Fetch the role for user_id from user_roles table.
    Inserts a default 'User' row if none exists.
    Returns the role string.
    """
    try:
        result = (
            get_client()
            .table("user_roles")
            .select("role")
            .eq("user_id", user_id)
            .single()
            .execute()
        )
        if result.data and result.data.get("role"):
            return result.data["role"]
    except Exception:
        pass

    # Row missing — insert default
    try:
        get_client().table("user_roles").insert(
            {"user_id": user_id, "role": "User"}
        ).execute()
    except Exception:
        pass

    return "User"


def list_all_users() -> list[dict]:
    """
    Returns all rows from user_roles (admin/sysadmin use only).
    Columns: user_id, email, role, created_at, updated_at.
    """
    try:
        result = (
            get_client()
            .table("user_roles")
            .select("user_id, email, role, created_at, updated_at")
            .order("created_at", desc=False)
            .execute()
        )
        return result.data or []
    except Exception:
        return []


def update_user_role(target_user_id: str, new_role: str) -> bool:
    """
    Update the role of a user.  Only Admin/SystemAdmin should call this.
    Returns True on success.
    """
    if new_role not in VALID_ROLES:
        return False
    try:
        get_client().table("user_roles").update(
            {"role": new_role}
        ).eq("user_id", target_user_id).execute()
        return True
    except Exception:
        return False
