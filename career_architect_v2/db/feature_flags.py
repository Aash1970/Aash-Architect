from __future__ import annotations
from db.client import get_client

ROLE_HIERARCHY = {
    "User":        1,
    "Coach":       2,
    "Admin":       3,
    "SystemAdmin": 4,
}

# Canonical defaults — used as fallback if table is unreachable
_DEFAULTS: dict[str, dict] = {
    "cv_builder":         {"enabled": True,  "min_role": "User"},
    "ats_level1":         {"enabled": True,  "min_role": "User"},
    "ats_level2":         {"enabled": True,  "min_role": "User"},
    "gap_analysis":       {"enabled": True,  "min_role": "User"},
    "linkedin_generator": {"enabled": True,  "min_role": "User"},
    "reflection":         {"enabled": True,  "min_role": "User"},
    "cv_export":          {"enabled": True,  "min_role": "User"},
    "coach_console":      {"enabled": True,  "min_role": "Coach"},
    "admin_dashboard":    {"enabled": True,  "min_role": "Admin"},
    "system_config":      {"enabled": True,  "min_role": "SystemAdmin"},
}


def _role_gte(role_a: str, role_b: str) -> bool:
    """Local role comparison — avoids circular import with main."""
    return ROLE_HIERARCHY.get(role_a, 0) >= ROLE_HIERARCHY.get(role_b, 0)


def fetch_feature_flags(user_id: str | None = None) -> dict[str, dict]:
    """
    Returns merged flag dict: global flags overridden by per-user overrides.
    Shape: { flag_name: { "enabled": bool, "min_role": str } }
    """
    flags = dict(_DEFAULTS)

    # Load global flags from DB
    try:
        result = (
            get_client()
            .table("feature_flags")
            .select("flag_name, enabled, min_role")
            .execute()
        )
        for row in (result.data or []):
            flags[row["flag_name"]] = {
                "enabled":  row["enabled"],
                "min_role": row["min_role"],
            }
    except Exception:
        pass

    # Apply per-user overrides
    if user_id:
        try:
            overrides = (
                get_client()
                .table("user_feature_overrides")
                .select("flag_name, enabled")
                .eq("user_id", user_id)
                .execute()
            )
            for row in (overrides.data or []):
                if row["flag_name"] in flags:
                    flags[row["flag_name"]]["enabled"] = row["enabled"]
        except Exception:
            pass

    return flags


def is_feature_enabled(flag_name: str, role: str, flags: dict) -> bool:
    """True if the flag is enabled AND the user's role meets the min_role."""
    cfg = flags.get(flag_name, {"enabled": False, "min_role": "SystemAdmin"})
    return cfg.get("enabled", False) and _role_gte(role, cfg.get("min_role", "User"))


def update_flag(flag_name: str, enabled: bool) -> bool:
    """Update a global feature flag (SystemAdmin only)."""
    try:
        get_client().table("feature_flags").update(
            {"enabled": enabled}
        ).eq("flag_name", flag_name).execute()
        return True
    except Exception:
        return False


def set_user_override(user_id: str, flag_name: str, enabled: bool) -> bool:
    """Upsert a per-user feature override (Admin/SystemAdmin only)."""
    try:
        get_client().table("user_feature_overrides").upsert(
            {"user_id": user_id, "flag_name": flag_name, "enabled": enabled},
            on_conflict="user_id,flag_name",
        ).execute()
        return True
    except Exception:
        return False
