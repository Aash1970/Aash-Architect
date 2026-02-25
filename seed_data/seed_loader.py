"""
Seed Data Loader — Development/Testing Only
Loads seed data into the DataService in-memory store.
MUST NOT be imported or called in production code.
Usage: python seed_data/seed_loader.py
"""

import json
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.services.data_service import DataService
from app.services.auth_service import AuthService


def load_seed_data(data_service: DataService, auth_service: AuthService) -> None:
    """
    Loads all seed data into the provided DataService instance.

    Args:
        data_service: DataService to populate
        auth_service: AuthService for password hashing
    """
    seed_dir = os.path.dirname(__file__)

    print("Loading seed data...")

    # ── Load users ────────────────────────────────────────────────────────────
    users_path = os.path.join(seed_dir, "users.json")
    with open(users_path, "r", encoding="utf-8") as f:
        users = json.load(f)

    for user in users:
        password = user.pop("_password_plain", "DefaultPass@123!")
        data_service.create_user(user)
        # Register password hash in auth service
        auth_service._password_hashes[user["user_id"]] = (
            AuthService._hash_password(password)
        )
        print(f"  ✓ User: {user['email']} [{user['role']} / {user['tier']}]")

    # ── Load CVs ──────────────────────────────────────────────────────────────
    cvs_path = os.path.join(seed_dir, "cvs.json")
    with open(cvs_path, "r", encoding="utf-8") as f:
        cvs = json.load(f)

    for cv in cvs:
        data_service.create_cv(cv)
        print(
            f"  ✓ CV: {cv['title']} "
            f"[User: {cv['user_id']}, Tier: {cv['tier']}]"
        )

    print(
        f"\nSeed data loaded: {len(users)} users, {len(cvs)} CVs."
    )
    print("\nLogin credentials:")
    print("-" * 60)

    users_path2 = os.path.join(seed_dir, "users.json")
    with open(users_path2, "r", encoding="utf-8") as f:
        users_display = json.load(f)

    for u in users_display:
        print(
            f"  {u['role']:12} | {u['email']:40} | {u['_password_plain']}"
        )
    print("-" * 60)


def verify_seed_data(data_service: DataService) -> bool:
    """
    Verifies seed data is loaded and consistent.

    Returns:
        True if all expected records are present
    """
    users = data_service.list_users()
    cvs = data_service.list_all_cvs()

    expected_roles = {"User", "Coach", "Admin", "SystemAdmin"}
    loaded_roles = {u["role"] for u in users}

    if not expected_roles.issubset(loaded_roles):
        missing = expected_roles - loaded_roles
        print(f"WARN: Missing roles in seed data: {missing}")
        return False

    expected_tiers = {"Free", "Premium", "Enterprise"}
    loaded_tiers = {u["tier"] for u in users}

    if not expected_tiers.issubset(loaded_tiers):
        missing = expected_tiers - loaded_tiers
        print(f"WARN: Missing tiers in seed data: {missing}")
        return False

    if len(cvs) < 3:
        print(f"WARN: Expected 3 CVs, found {len(cvs)}")
        return False

    print(f"Seed verification: OK ({len(users)} users, {len(cvs)} CVs)")
    return True


if __name__ == "__main__":
    ds = DataService()
    auth_svc = AuthService(ds)
    load_seed_data(ds, auth_svc)
    verify_seed_data(ds)
