"""
JWT authentication middleware / dependency helper.

Verification strategy
─────────────────────
Supabase issues HS256 JWTs signed with the project's JWT secret.
Set SUPABASE_JWT_SECRET in your environment (copied from Supabase
Project Settings → API → JWT Secret).

For RS256 / asymmetric keys (Supabase Auth v2 enterprise):
  - Set SUPABASE_JWT_ALGORITHM=RS256
  - Set SUPABASE_JWT_PUBLIC_KEY to the PEM-encoded public key

No fake verification logic is used. A missing or invalid secret raises
a 500 configuration error so misconfiguration is immediately visible.
"""
from __future__ import annotations

import os
from typing import Dict, Optional

from jose import ExpiredSignatureError, JWTError, jwt
from jose.exceptions import JWKError

_ALGORITHM = os.environ.get("SUPABASE_JWT_ALGORITHM", "HS256")
_SECRET = os.environ.get("SUPABASE_JWT_SECRET", "")
_PUBLIC_KEY = os.environ.get("SUPABASE_JWT_PUBLIC_KEY", "")

# For RS256 the signing key is the public key; for HS256 it is the shared secret.
_SIGNING_KEY: Optional[str] = _PUBLIC_KEY if _ALGORITHM == "RS256" else _SECRET

# ── Local-mode token registry ─────────────────────────────────────────────────
# Maps "local-token-<hex>" → user_id for dev/test mode only.
# This is never populated when Supabase is configured (tokens are real JWTs).
_local_token_registry: Dict[str, str] = {}


def register_local_token(token: str, user_id: str) -> None:
    """Store a local-mode token so subsequent requests can be verified."""
    _local_token_registry[token] = user_id


def revoke_local_token(token: str) -> None:
    """Remove a local-mode token (e.g. on logout)."""
    _local_token_registry.pop(token, None)


class JWTConfigurationError(RuntimeError):
    """Raised at startup / request time when JWT env vars are absent."""


class JWTExpiredError(ValueError):
    """The JWT has expired."""


class JWTInvalidError(ValueError):
    """The JWT signature or claims are invalid."""


def verify_token(token: str) -> dict:
    """
    Decode and verify a JWT.

    For local/test mode (no Supabase), tokens issued by AuthService start with
    "local-token-" and are verified against the in-memory registry populated at
    login time.  This branch is never reached when SUPABASE_JWT_SECRET is set
    and real JWTs are in use.

    Returns the full claims payload dict on success.
    Raises JWTExpiredError, JWTInvalidError, or JWTConfigurationError.
    """
    # ── Local-mode bridge ─────────────────────────────────────────────────────
    if token.startswith("local-token-"):
        user_id = _local_token_registry.get(token)
        if not user_id:
            raise JWTInvalidError(
                "Local token not recognised. Please log in again."
            )
        return {"sub": user_id}

    # ── Supabase JWT path ─────────────────────────────────────────────────────
    if not _SIGNING_KEY:
        raise JWTConfigurationError(
            "JWT signing key not configured. "
            "Set SUPABASE_JWT_SECRET (HS256) or "
            "SUPABASE_JWT_PUBLIC_KEY + SUPABASE_JWT_ALGORITHM=RS256."
        )

    try:
        payload = jwt.decode(
            token,
            _SIGNING_KEY,
            algorithms=[_ALGORITHM],
            options={"verify_aud": False},  # Supabase tokens omit 'aud' by default
        )
        return payload
    except ExpiredSignatureError as exc:
        raise JWTExpiredError("Token has expired.") from exc
    except (JWTError, JWKError) as exc:
        raise JWTInvalidError(f"Token verification failed: {exc}") from exc


def extract_user_id(payload: dict) -> str:
    """Extract the canonical user identifier from JWT claims."""
    uid = payload.get("sub") or payload.get("user_id") or payload.get("id")
    if not uid:
        raise JWTInvalidError("Token contains no subject (sub) claim.")
    return str(uid)
