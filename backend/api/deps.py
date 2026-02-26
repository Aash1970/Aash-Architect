"""
FastAPI dependency providers.

Service singletons are stored on app.state (initialised in main.py lifespan).
Per-request dependencies resolve the authenticated user from the Bearer token.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.admin.admin_service import AdminService
from app.services.ats_service import ATSService
from app.services.auth_service import AuthService
from app.services.cv_service import CVService
from app.services.data_service import DataService
from app.services.role_service import RoleService
from app.services.tier_service import TierService

from backend.api.middleware.auth import (
    JWTConfigurationError,
    JWTExpiredError,
    JWTInvalidError,
    extract_user_id,
    verify_token,
)

_bearer = HTTPBearer(auto_error=False)


# ── Service accessors ─────────────────────────────────────────────────────────

def get_data_service(request: Request) -> DataService:
    return request.app.state.data_service


def get_auth_service(request: Request) -> AuthService:
    return request.app.state.auth_service


def get_cv_service(request: Request) -> CVService:
    return request.app.state.cv_service


def get_role_service(request: Request) -> RoleService:
    return request.app.state.role_service


def get_tier_service(request: Request) -> TierService:
    return request.app.state.tier_service


def get_ats_service(request: Request) -> ATSService:
    return request.app.state.ats_service


def get_admin_service(request: Request) -> AdminService:
    return request.app.state.admin_service


# ── Authenticated user context ────────────────────────────────────────────────

@dataclass(frozen=True)
class CurrentUser:
    user_id: str
    email: str
    role: str
    tier: str
    full_name: str
    language: str


async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer),
) -> CurrentUser:
    """
    FastAPI dependency that resolves the authenticated caller.

    1. Extracts Bearer token from Authorization header.
    2. Verifies JWT signature and expiry using SUPABASE_JWT_SECRET.
    3. Resolves user profile from DataService for authoritative role/tier.

    Raises 401 if the token is absent, expired, or invalid.
    Raises 500 if JWT is not configured (misconfiguration).
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header missing or not Bearer.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = verify_token(credentials.credentials)
    except JWTConfigurationError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc
    except JWTExpiredError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except JWTInvalidError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        user_id = extract_user_id(payload)
    except JWTInvalidError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        ) from exc

    ds: DataService = request.app.state.data_service
    user = ds.get_user(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account not found.",
        )
    if not user.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is deactivated.",
        )

    return CurrentUser(
        user_id=user["user_id"],
        email=user.get("email", ""),
        role=user.get("role", "User"),
        tier=user.get("tier", "Free"),
        full_name=user.get("full_name", ""),
        language=user.get("language", "en"),
    )
