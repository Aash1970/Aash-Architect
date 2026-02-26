"""
/tier router — tier limits and feature gating information.

GET /tier/limits           Return tier limits for the current user
GET /tier/limits/{tier}    Return tier limits for a specific tier (Admin+)
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.services.role_service import PermissionDeniedError, RoleService
from app.services.tier_service import TierService
from backend.api.deps import (
    CurrentUser,
    get_current_user,
    get_role_service,
    get_tier_service,
)
from backend.api.schemas.tier import TierLimitsResponse

router = APIRouter()

_VALID_TIERS = {"Free", "Premium", "Enterprise"}


@router.get(
    "/limits",
    response_model=TierLimitsResponse,
    summary="Return tier limits for the authenticated user",
)
async def my_tier_limits(
    current_user: CurrentUser = Depends(get_current_user),
    tier_svc: TierService = Depends(get_tier_service),
) -> TierLimitsResponse:
    summary = tier_svc.get_limits_summary(current_user.tier)
    return TierLimitsResponse.from_dict(current_user.tier, summary)


@router.get(
    "/limits/{tier}",
    response_model=TierLimitsResponse,
    summary="Return tier limits for a specific tier (Admin+ only)",
)
async def tier_limits_by_name(
    tier: str,
    current_user: CurrentUser = Depends(get_current_user),
    tier_svc: TierService = Depends(get_tier_service),
    rs: RoleService = Depends(get_role_service),
) -> TierLimitsResponse:
    try:
        rs.require_minimum_role(current_user.role, "Admin")
    except PermissionDeniedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))

    if tier not in _VALID_TIERS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown tier '{tier}'. Valid tiers: {sorted(_VALID_TIERS)}",
        )

    summary = tier_svc.get_limits_summary(tier)
    return TierLimitsResponse.from_dict(tier, summary)
