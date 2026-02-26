"""
/admin router — platform administration (Admin+ and SystemAdmin).

GET    /admin/users                          List all users
GET    /admin/users/{user_id}                Fetch a single user
PATCH  /admin/users/{user_id}                Update user fields (role, tier, active)
DELETE /admin/users/{user_id}                Deactivate a user
GET    /admin/coaches                        List all coaches
POST   /admin/coaches/assign                 Assign a coach to a user
GET    /admin/metrics                        Platform metrics dashboard
GET    /admin/reports/users                  Exportable user report
GET    /admin/retention-policies             List all retention policies
PATCH  /admin/retention-policies/{tier}      Update tier retention policy (SystemAdmin)
DELETE /admin/cv/{cv_id}                     Hard-delete a CV (SystemAdmin)
GET    /admin/languages                      Get active platform languages
PUT    /admin/languages                      Set active platform languages (SystemAdmin)
"""
from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status

from app.admin.admin_service import AdminService, AdminServiceError
from app.services.role_service import PermissionDeniedError
from backend.api.deps import CurrentUser, get_admin_service, get_current_user
from backend.api.schemas.admin import (
    AdminUserReport,
    AssignCoachRequest,
    RetentionPolicyUpdateRequest,
    SetLanguagesRequest,
    UserRetentionOverrideRequest,
    UserUpdateRequest,
)
from backend.api.schemas.common import DataResponse, MessageResponse

router = APIRouter()


def _permission_error(exc: PermissionDeniedError) -> HTTPException:
    return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))


def _admin_error(exc: AdminServiceError) -> HTTPException:
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


# ── Users ─────────────────────────────────────────────────────────────────────

@router.get("/users", response_model=DataResponse, summary="List all users")
async def list_users(
    include_deleted: bool = False,
    current_user: CurrentUser = Depends(get_current_user),
    admin_svc: AdminService = Depends(get_admin_service),
) -> DataResponse:
    try:
        users = admin_svc.list_users(
            requester_role=current_user.role,
            include_deleted=include_deleted,
        )
    except PermissionDeniedError as exc:
        raise _permission_error(exc)
    return DataResponse(data=users)


@router.get("/users/{user_id}", response_model=DataResponse, summary="Fetch a user")
async def get_user(
    user_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    admin_svc: AdminService = Depends(get_admin_service),
) -> DataResponse:
    try:
        user = admin_svc.get_user(user_id=user_id, requester_role=current_user.role)
    except PermissionDeniedError as exc:
        raise _permission_error(exc)
    except AdminServiceError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    return DataResponse(data=user)


@router.patch("/users/{user_id}", response_model=DataResponse, summary="Update user fields")
async def update_user(
    user_id: str,
    body: UserUpdateRequest,
    current_user: CurrentUser = Depends(get_current_user),
    admin_svc: AdminService = Depends(get_admin_service),
) -> DataResponse:
    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    if not updates:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No update fields provided.",
        )
    try:
        updated = admin_svc.update_user(
            user_id=user_id,
            updates=updates,
            requester_role=current_user.role,
        )
    except PermissionDeniedError as exc:
        raise _permission_error(exc)
    except AdminServiceError as exc:
        raise _admin_error(exc)
    return DataResponse(data=updated)


@router.delete(
    "/users/{user_id}",
    response_model=MessageResponse,
    summary="Deactivate a user account",
)
async def deactivate_user(
    user_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    admin_svc: AdminService = Depends(get_admin_service),
) -> MessageResponse:
    try:
        admin_svc.deactivate_user(
            user_id=user_id, requester_role=current_user.role
        )
    except PermissionDeniedError as exc:
        raise _permission_error(exc)
    except AdminServiceError as exc:
        raise _admin_error(exc)
    return MessageResponse(message=f"User {user_id} deactivated.")


# ── Coaches ───────────────────────────────────────────────────────────────────

@router.get("/coaches", response_model=DataResponse, summary="List all coaches")
async def list_coaches(
    current_user: CurrentUser = Depends(get_current_user),
    admin_svc: AdminService = Depends(get_admin_service),
) -> DataResponse:
    try:
        coaches = admin_svc.list_coaches(requester_role=current_user.role)
    except PermissionDeniedError as exc:
        raise _permission_error(exc)
    return DataResponse(data=coaches)


@router.post(
    "/coaches/assign",
    response_model=DataResponse,
    summary="Assign a coach to a user",
)
async def assign_coach(
    body: AssignCoachRequest,
    current_user: CurrentUser = Depends(get_current_user),
    admin_svc: AdminService = Depends(get_admin_service),
) -> DataResponse:
    try:
        result = admin_svc.assign_coach_to_user(
            user_id=body.user_id,
            coach_id=body.coach_id,
            requester_role=current_user.role,
        )
    except PermissionDeniedError as exc:
        raise _permission_error(exc)
    except AdminServiceError as exc:
        raise _admin_error(exc)
    return DataResponse(data=result)


# ── Metrics ───────────────────────────────────────────────────────────────────

@router.get("/metrics", response_model=DataResponse, summary="Platform metrics")
async def get_metrics(
    current_user: CurrentUser = Depends(get_current_user),
    admin_svc: AdminService = Depends(get_admin_service),
) -> DataResponse:
    try:
        metrics = admin_svc.get_metrics(requester_role=current_user.role)
    except PermissionDeniedError as exc:
        raise _permission_error(exc)
    return DataResponse(data=metrics)


# ── Reports ───────────────────────────────────────────────────────────────────

@router.get(
    "/reports/users",
    response_model=DataResponse,
    summary="Export user report (PII-scrubbed)",
)
async def export_user_report(
    current_user: CurrentUser = Depends(get_current_user),
    admin_svc: AdminService = Depends(get_admin_service),
) -> DataResponse:
    try:
        report = admin_svc.export_user_report(requester_role=current_user.role)
    except PermissionDeniedError as exc:
        raise _permission_error(exc)
    return DataResponse(data=report)


# ── Retention (SystemAdmin) ───────────────────────────────────────────────────

@router.get(
    "/retention-policies",
    response_model=DataResponse,
    summary="List all retention policies",
)
async def list_retention_policies(
    current_user: CurrentUser = Depends(get_current_user),
    admin_svc: AdminService = Depends(get_admin_service),
) -> DataResponse:
    try:
        policies = admin_svc.list_retention_policies(requester_role=current_user.role)
    except PermissionDeniedError as exc:
        raise _permission_error(exc)
    return DataResponse(data=policies)


@router.patch(
    "/retention-policies/{tier}",
    response_model=DataResponse,
    summary="Update retention policy for a tier (SystemAdmin only)",
)
async def update_retention_policy(
    tier: str,
    body: RetentionPolicyUpdateRequest,
    current_user: CurrentUser = Depends(get_current_user),
    admin_svc: AdminService = Depends(get_admin_service),
) -> DataResponse:
    try:
        policy = admin_svc.update_retention_policy(
            tier=tier,
            cv_version_days=body.cv_version_days,
            deleted_cv_days=body.deleted_cv_days,
            export_log_days=body.export_log_days,
            requester_role=current_user.role,
            requester_id=current_user.user_id,
        )
    except PermissionDeniedError as exc:
        raise _permission_error(exc)
    except AdminServiceError as exc:
        raise _admin_error(exc)
    return DataResponse(data=policy)


@router.post(
    "/retention-policies/user-override",
    response_model=DataResponse,
    summary="Set per-user retention override (SystemAdmin only)",
)
async def user_retention_override(
    body: UserRetentionOverrideRequest,
    current_user: CurrentUser = Depends(get_current_user),
    admin_svc: AdminService = Depends(get_admin_service),
) -> DataResponse:
    try:
        policy = admin_svc.set_user_retention_override(
            user_id=body.user_id,
            tier=current_user.tier,
            cv_version_days=body.cv_version_days,
            requester_role=current_user.role,
            requester_id=current_user.user_id,
        )
    except PermissionDeniedError as exc:
        raise _permission_error(exc)
    except AdminServiceError as exc:
        raise _admin_error(exc)
    return DataResponse(data=policy)


# ── Hard delete (SystemAdmin) ─────────────────────────────────────────────────

@router.delete(
    "/cv/{cv_id}",
    response_model=MessageResponse,
    summary="Hard-delete a CV permanently (SystemAdmin only)",
)
async def hard_delete_cv(
    cv_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    admin_svc: AdminService = Depends(get_admin_service),
) -> MessageResponse:
    try:
        admin_svc.hard_delete_cv(cv_id=cv_id, requester_role=current_user.role)
    except PermissionDeniedError as exc:
        raise _permission_error(exc)
    return MessageResponse(message=f"CV {cv_id} permanently deleted.")


# ── Languages (SystemAdmin) ───────────────────────────────────────────────────

@router.get(
    "/languages",
    response_model=DataResponse,
    summary="Get active platform languages",
)
async def get_active_languages(
    current_user: CurrentUser = Depends(get_current_user),
    admin_svc: AdminService = Depends(get_admin_service),
) -> DataResponse:
    langs = admin_svc.get_active_languages()
    return DataResponse(data={"active_languages": langs})


@router.put(
    "/languages",
    response_model=DataResponse,
    summary="Set active platform languages (SystemAdmin only)",
)
async def set_active_languages(
    body: SetLanguagesRequest,
    current_user: CurrentUser = Depends(get_current_user),
    admin_svc: AdminService = Depends(get_admin_service),
) -> DataResponse:
    try:
        langs = admin_svc.set_active_languages(
            lang_codes=body.lang_codes,
            requester_role=current_user.role,
        )
    except PermissionDeniedError as exc:
        raise _permission_error(exc)
    except AdminServiceError as exc:
        raise _admin_error(exc)
    return DataResponse(data={"active_languages": langs})
