"""
/gdpr router — GDPR consent and right-to-erasure.

POST /gdpr/erase-user          GDPR Art. 17 — right to erasure
GET  /gdpr/export-user-data    GDPR Art. 20 — subject access / data portability
POST /gdpr/consent             Record or update a consent decision
GET  /gdpr/consent-status      Current consent state for the authenticated user
"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from app.gdpr.consent import ConsentService, ConsentServiceError
from app.gdpr.erasure import ErasureError, ErasureService
from app.services.role_service import PermissionDeniedError
from backend.api.deps import (
    CurrentUser,
    get_consent_service,
    get_current_user,
    get_erasure_service,
)
from backend.api.schemas.common import DataResponse
from backend.api.schemas.gdpr import (
    ConsentRecordResponse,
    ConsentRequest,
    ConsentStatusResponse,
    EraseUserRequest,
    ErasureReceiptResponse,
)

router = APIRouter()


@router.post(
    "/erase-user",
    response_model=ErasureReceiptResponse,
    summary="Request GDPR erasure for a user account (Art. 17)",
)
async def erase_user(
    body: EraseUserRequest,
    current_user: CurrentUser = Depends(get_current_user),
    erasure_svc: ErasureService = Depends(get_erasure_service),
) -> ErasureReceiptResponse:
    try:
        receipt = erasure_svc.request_erasure(
            target_user_id=body.target_user_id,
            requester_id=current_user.user_id,
            requester_role=current_user.role,
        )
    except PermissionDeniedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    except ErasureError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    return ErasureReceiptResponse.from_dict(receipt)


@router.get(
    "/export-user-data",
    response_model=DataResponse,
    summary="Export all personal data held for a user (GDPR Art. 20 SAR)",
)
async def export_user_data(
    target_user_id: Optional[str] = Query(
        default=None,
        description="User ID to export. Defaults to authenticated user. SystemAdmin may specify others.",
    ),
    current_user: CurrentUser = Depends(get_current_user),
    erasure_svc: ErasureService = Depends(get_erasure_service),
) -> DataResponse:
    subject = target_user_id or current_user.user_id
    try:
        data = erasure_svc.export_user_data(
            target_user_id=subject,
            requester_id=current_user.user_id,
            requester_role=current_user.role,
        )
    except PermissionDeniedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    return DataResponse(data=data)


@router.post(
    "/consent",
    response_model=ConsentRecordResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Record or update a consent decision",
)
async def record_consent(
    body: ConsentRequest,
    request: Request,
    current_user: CurrentUser = Depends(get_current_user),
    consent_svc: ConsentService = Depends(get_consent_service),
) -> ConsentRecordResponse:
    ip = request.client.host if request.client else ""
    ua = request.headers.get("User-Agent", "")
    try:
        record = consent_svc.record_consent(
            user_id=current_user.user_id,
            level=body.level,
            granted=body.granted,
            ip_address=ip,
            user_agent=ua,
        )
    except ConsentServiceError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    return ConsentRecordResponse.from_dict(record.to_dict())


@router.get(
    "/consent-status",
    response_model=ConsentStatusResponse,
    summary="Return current consent state for the authenticated user",
)
async def consent_status(
    current_user: CurrentUser = Depends(get_current_user),
    consent_svc: ConsentService = Depends(get_consent_service),
) -> ConsentStatusResponse:
    state = consent_svc.get_current_consent(current_user.user_id)
    return ConsentStatusResponse.from_state(state)
