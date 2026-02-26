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
from typing import Optional

from jose import ExpiredSignatureError, JWTError, jwt
from jose.exceptions import JWKError

_ALGORITHM = os.environ.get("SUPABASE_JWT_ALGORITHM", "HS256")
_SECRET = os.environ.get("SUPABASE_JWT_SECRET", "")
_PUBLIC_KEY = os.environ.get("SUPABASE_JWT_PUBLIC_KEY", "")

# For RS256 the signing key is the public key; for HS256 it is the shared secret.
_SIGNING_KEY: Optional[str] = _PUBLIC_KEY if _ALGORITHM == "RS256" else _SECRET


class JWTConfigurationError(RuntimeError):
    """Raised at startup / request time when JWT env vars are absent."""


class JWTExpiredError(ValueError):
    """The JWT has expired."""


class JWTInvalidError(ValueError):
    """The JWT signature or claims are invalid."""


def verify_token(token: str) -> dict:
    """
    Decode and verify a JWT.

    Returns the full claims payload dict on success.
    Raises JWTExpiredError, JWTInvalidError, or JWTConfigurationError.
    """
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
