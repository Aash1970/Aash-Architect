from __future__ import annotations
import json
from db.client import get_client
from modules.encryption import encrypt_data, decrypt_data, generate_checksum

# Canonical empty CV structure
EMPTY_CV: dict = {
    "personal": {
        "full_name": "",
        "email":     "",
        "phone":     "",
        "location":  "",
        "linkedin":  "",
        "website":   "",
    },
    "profile_summary": "",
    "skills":          [],
    "experience": [],
    "education":  [],
    "certifications": [],
    "languages":      [],
}


def save_cv(user_id: str, cv_data: dict) -> tuple[bool, str]:
    """
    Encrypt cv_data and upsert to cvs table.
    Returns (success: bool, message: str).
    """
    try:
        plaintext   = json.dumps(cv_data, ensure_ascii=False)
        encrypted   = encrypt_data(plaintext, user_id)
        checksum    = generate_checksum(plaintext)

        # Fetch current version to increment
        existing = (
            get_client()
            .table("cvs")
            .select("version")
            .eq("user_id", user_id)
            .execute()
        )
        version = 1
        if existing.data:
            version = (existing.data[0].get("version") or 0) + 1

        get_client().table("cvs").upsert(
            {
                "user_id":        user_id,
                "encrypted_data": encrypted,
                "checksum":       checksum,
                "version":        version,
            },
            on_conflict="user_id",
        ).execute()
        return True, f"CV saved (version {version})."
    except Exception as exc:
        return False, f"Save failed: {exc}"


def load_cv(user_id: str) -> tuple[dict | None, str]:
    """
    Fetch and decrypt CV for user_id.
    Returns (cv_data | None, message).
    """
    try:
        result = (
            get_client()
            .table("cvs")
            .select("encrypted_data, checksum, version")
            .eq("user_id", user_id)
            .single()
            .execute()
        )
        if not result.data:
            return None, "No CV found."

        row         = result.data
        plaintext   = decrypt_data(row["encrypted_data"], user_id)
        integrity   = generate_checksum(plaintext)

        if integrity != row["checksum"]:
            return None, "Integrity check failed — CV data may be corrupt."

        cv_data = json.loads(plaintext)
        return cv_data, f"CV loaded (version {row['version']})."
    except Exception as exc:
        return None, f"Load failed: {exc}"


def load_cv_for_coach(target_user_id: str, coach_user_id: str) -> tuple[dict | None, str]:
    """
    Fetch and decrypt another user's CV.
    The caller must be Coach/Admin/SystemAdmin — enforced by RLS.
    Decryption uses the target user's key.
    """
    return load_cv(target_user_id)
