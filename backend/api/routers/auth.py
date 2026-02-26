"""
/auth router — authentication and account management.

POST  /auth/register
POST  /auth/login
POST  /auth/logout
GET   /auth/me
PUT   /auth/change-password
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer

from app.services.auth_service import AuthError, AuthService
from backend.api.deps import CurrentUser, get_auth_service, get_current_user
from backend.api.middleware.auth import register_local_token, revoke_local_token
from backend.api.schemas.auth import (
    ChangePasswordRequest,
    LoginRequest,
    LoginResponse,
    RegisterRequest,
    UserResponse,
)
from backend.api.schemas.common import MessageResponse

router = APIRouter()


def _user_response(user_dict: dict) -> UserResponse:
    return UserResponse(
        user_id=user_dict["user_id"],
        email=user_dict.get("email", ""),
        full_name=user_dict.get("full_name", ""),
        role=user_dict.get("role", "User"),
        tier=user_dict.get("tier", "Free"),
        language=user_dict.get("language", "en"),
        is_active=user_dict.get("is_active", True),
        access_token=user_dict.get("access_token"),
        refresh_token=user_dict.get("refresh_token"),
    )


@router.post(
    "/register",
    response_model=LoginResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account",
)
async def register(
    body: RegisterRequest,
    auth_svc: AuthService = Depends(get_auth_service),
) -> LoginResponse:
    try:
        user = auth_svc.register(
            email=body.email,
            password=body.password,
            full_name=body.full_name,
            role=body.role,
            tier=body.tier,
        )
    except AuthError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    return LoginResponse(user=_user_response(user.to_dict()))


@router.post(
    "/login",
    response_model=LoginResponse,
    summary="Authenticate and obtain access token",
)
async def login(
    body: LoginRequest,
    auth_svc: AuthService = Depends(get_auth_service),
) -> LoginResponse:
    try:
        user = auth_svc.login(email=body.email, password=body.password)
    except AuthError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        )
    # Register local-mode tokens so the auth middleware can verify them.
    # No-op when Supabase is configured (token is a real JWT, not "local-token-*").
    token = user.access_token or ""
    if token.startswith("local-token-"):
        register_local_token(token, user.user_id)
    return LoginResponse(user=_user_response(user.to_dict()))


@router.post(
    "/logout",
    response_model=MessageResponse,
    summary="Invalidate the current session",
)
async def logout(
    request: Request,
    current_user: CurrentUser = Depends(get_current_user),
    auth_svc: AuthService = Depends(get_auth_service),
) -> MessageResponse:
    auth_svc.logout(current_user.user_id)
    # Revoke local-mode token from the in-memory registry if present.
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer local-token-"):
        revoke_local_token(auth_header[len("Bearer "):])
    return MessageResponse(message="Logged out successfully.")


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Return the authenticated caller's profile",
)
async def me(current_user: CurrentUser = Depends(get_current_user)) -> UserResponse:
    return UserResponse(
        user_id=current_user.user_id,
        email=current_user.email,
        full_name=current_user.full_name,
        role=current_user.role,
        tier=current_user.tier,
        language=current_user.language,
        is_active=True,
    )


@router.put(
    "/change-password",
    response_model=MessageResponse,
    summary="Change the authenticated user's password",
)
async def change_password(
    body: ChangePasswordRequest,
    current_user: CurrentUser = Depends(get_current_user),
    auth_svc: AuthService = Depends(get_auth_service),
) -> MessageResponse:
    try:
        auth_svc.change_password(
            user_id=current_user.user_id,
            old_password=body.old_password,
            new_password=body.new_password,
        )
    except AuthError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    return MessageResponse(message="Password changed successfully.")
