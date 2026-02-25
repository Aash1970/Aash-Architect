"""
Auth Service — Production Grade
Handles authentication operations against Supabase Auth.
Falls back to in-memory user store when Supabase not configured.
No UI imports. No st.session_state.
"""

from __future__ import annotations

import os
import uuid
import hashlib
import secrets
from datetime import datetime, timezone
from typing import Optional, Dict, Any

from app.models.user_model import UserModel, UserProfile
from app.services.data_service import DataService


class AuthError(Exception):
    """Raised on authentication failures."""


class AuthService:
    """
    Manages authentication: login, logout, registration, session validation.

    In production (Supabase):
      - Delegates auth to Supabase Auth (JWT tokens)
      - Fetches user profile from users table

    In local/test mode (no Supabase):
      - Uses in-memory user store with hashed passwords
    """

    def __init__(self, data_service: DataService):
        self._ds = data_service
        self._use_supabase = data_service._use_supabase
        # Local mode: password_hashes keyed by user_id
        self._password_hashes: Dict[str, str] = {}

    def register(
        self,
        email: str,
        password: str,
        full_name: str,
        role: str = "User",
        tier: str = "Free",
    ) -> UserModel:
        """
        Registers a new user.

        Args:
            email:     User's email address
            password:  Plain-text password (min 8 chars enforced)
            full_name: Display name
            role:      Initial role (default: User)
            tier:      Initial tier (default: Free)

        Returns:
            UserModel for the newly created user

        Raises:
            AuthError on failure or if email already in use
        """
        if len(password) < 8:
            raise AuthError("Password must be at least 8 characters.")

        # Check for existing user
        existing = self._ds.get_user_by_email(email)
        if existing:
            raise AuthError(f"Email '{email}' is already registered.")

        user_id = str(uuid.uuid4())

        if self._use_supabase and self._ds._client:
            try:
                auth_response = self._ds._client.auth.sign_up({
                    "email": email,
                    "password": password,
                })
                if auth_response.user:
                    user_id = str(auth_response.user.id)
            except Exception as exc:
                raise AuthError(f"Registration failed: {exc}") from exc

        # Store profile
        profile_data = {
            "user_id": user_id,
            "email": email,
            "full_name": full_name,
            "role": role,
            "tier": tier,
            "language": "en",
            "is_active": True,
            "is_deleted": False,
        }
        profile_data = self._ds.create_user(profile_data)

        # Store hashed password in local mode
        if not self._use_supabase:
            self._password_hashes[user_id] = self._hash_password(password)

        return UserModel(
            user_id=user_id,
            email=email,
            role=role,
            tier=tier,
            full_name=full_name,
        )

    def login(self, email: str, password: str) -> UserModel:
        """
        Authenticates a user.

        Args:
            email:    Email address
            password: Plain-text password

        Returns:
            Authenticated UserModel with access_token set

        Raises:
            AuthError on invalid credentials
        """
        if self._use_supabase and self._ds._client:
            try:
                session = self._ds._client.auth.sign_in_with_password({
                    "email": email,
                    "password": password,
                })
                if not session.user:
                    raise AuthError("Invalid email or password.")

                user_id = str(session.user.id)
                access_token = session.session.access_token if session.session else None

                profile_data = self._ds.get_user(user_id)
                if not profile_data:
                    raise AuthError("User profile not found.")

                return UserModel(
                    user_id=user_id,
                    email=email,
                    role=profile_data.get("role", "User"),
                    tier=profile_data.get("tier", "Free"),
                    full_name=profile_data.get("full_name", ""),
                    language=profile_data.get("language", "en"),
                    is_active=profile_data.get("is_active", True),
                    access_token=access_token,
                )
            except AuthError:
                raise
            except Exception as exc:
                raise AuthError(f"Login failed: {exc}") from exc

        # Local/test mode
        profile_data = self._ds.get_user_by_email(email)
        if not profile_data:
            raise AuthError("Invalid email or password.")

        user_id = profile_data["user_id"]
        stored_hash = self._password_hashes.get(user_id, "")

        if not stored_hash or not self._verify_password(password, stored_hash):
            raise AuthError("Invalid email or password.")

        if not profile_data.get("is_active", True):
            raise AuthError("This account has been deactivated.")

        return UserModel(
            user_id=user_id,
            email=email,
            role=profile_data.get("role", "User"),
            tier=profile_data.get("tier", "Free"),
            full_name=profile_data.get("full_name", ""),
            language=profile_data.get("language", "en"),
            is_active=profile_data.get("is_active", True),
            access_token=f"local-token-{secrets.token_hex(16)}",
        )

    def logout(self, user_id: str) -> None:
        """Invalidates the user's session."""
        if self._use_supabase and self._ds._client:
            try:
                self._ds._client.auth.sign_out()
            except Exception:
                pass  # Best-effort logout

    def get_current_user(self, access_token: str) -> Optional[UserModel]:
        """
        Validates an access token and returns the authenticated user.
        Returns None if token is invalid or expired.
        """
        if not access_token:
            return None

        if self._use_supabase and self._ds._client:
            try:
                user = self._ds._client.auth.get_user(access_token)
                if not user or not user.user:
                    return None
                user_id = str(user.user.id)
                profile_data = self._ds.get_user(user_id)
                if not profile_data:
                    return None
                return UserModel(
                    user_id=user_id,
                    email=profile_data.get("email", ""),
                    role=profile_data.get("role", "User"),
                    tier=profile_data.get("tier", "Free"),
                    full_name=profile_data.get("full_name", ""),
                    language=profile_data.get("language", "en"),
                    is_active=profile_data.get("is_active", True),
                    access_token=access_token,
                )
            except Exception:
                return None

        # Local mode: token is not cryptographically verified (dev only)
        if access_token.startswith("local-token-"):
            return None  # Would need a token→user mapping for full implementation

        return None

    def change_password(
        self, user_id: str, old_password: str, new_password: str
    ) -> None:
        """
        Changes a user's password.

        Raises:
            AuthError if old password incorrect or new password too short
        """
        if len(new_password) < 8:
            raise AuthError("New password must be at least 8 characters.")

        if not self._use_supabase:
            stored_hash = self._password_hashes.get(user_id, "")
            if not self._verify_password(old_password, stored_hash):
                raise AuthError("Current password is incorrect.")
            self._password_hashes[user_id] = self._hash_password(new_password)

    @staticmethod
    def _hash_password(password: str) -> str:
        """PBKDF2-HMAC-SHA256 password hash for local mode."""
        salt = secrets.token_bytes(32)
        key = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 260_000)
        return salt.hex() + ":" + key.hex()

    @staticmethod
    def _verify_password(password: str, stored_hash: str) -> bool:
        """Verifies a password against a stored PBKDF2 hash."""
        try:
            salt_hex, key_hex = stored_hash.split(":")
            salt = bytes.fromhex(salt_hex)
            expected_key = bytes.fromhex(key_hex)
            actual_key = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 260_000)
            return secrets.compare_digest(actual_key, expected_key)
        except (ValueError, AttributeError):
            return False
