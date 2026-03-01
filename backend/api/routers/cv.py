"""
/cv router — CV CRUD, export, coach submission, notes, and version history.

GET    /cv               List CVs for current user (or target user for admins)
POST   /cv               Create a new CV
GET    /cv/{cv_id}       Get a specific CV
PUT    /cv/{cv_id}       Update a CV
DELETE /cv/{cv_id}       Delete a CV
GET    /cv/{cv_id}/export          Download export archive (ZIP)
POST   /cv/{cv_id}/submit-coach    Submit CV to a coach
POST   /cv/{cv_id}/notes           Add a coach note
GET    /cv/{cv_id}/notes           Retrieve coach notes
GET    /cv/{cv_id}/history         Version history
"""
from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status

from app.services.cv_service import CVService, CVServiceError
from app.services.role_service import PermissionDeniedError
from app.tier.tier_rules import TierGateError
from app.validation.validators import ValidationError
from backend.api.deps import CurrentUser, get_current_user, get_cv_service
from backend.api.schemas.cv import (
    AddCoachNoteRequest,
    CVCreateRequest,
    CVResponse,
    CVUpdateRequest,
    SubmitToCoachRequest,
)
from backend.api.schemas.common import DataResponse, MessageResponse

router = APIRouter()


def _cv_resp(d: dict) -> CVResponse:
    return CVResponse.from_dict(d)


@router.get(
    "",
    response_model=List[CVResponse],
    summary="List CVs visible to the current user",
)
async def list_cvs(
    target_user_id: Optional[str] = Query(default=None, description="Admin/Coach: list CVs for a specific user"),
    current_user: CurrentUser = Depends(get_current_user),
    cv_svc: CVService = Depends(get_cv_service),
) -> List[CVResponse]:
    try:
        cvs = cv_svc.list_cvs(
            requester_id=current_user.user_id,
            requester_role=current_user.role,
            target_user_id=target_user_id,
        )
    except PermissionDeniedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    return [_cv_resp(c) for c in cvs if not c.get("is_deleted")]


@router.post(
    "",
    response_model=CVResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new CV",
)
async def create_cv(
    body: CVCreateRequest,
    current_user: CurrentUser = Depends(get_current_user),
    cv_svc: CVService = Depends(get_cv_service),
) -> CVResponse:
    cv_data = body.model_dump()
    try:
        created = cv_svc.create_cv(
            cv_data=cv_data,
            requester_id=current_user.user_id,
            requester_role=current_user.role,
            requester_tier=current_user.tier,
        )
    except TierGateError as exc:
        raise HTTPException(status_code=status.HTTP_402_PAYMENT_REQUIRED, detail=str(exc))
    except ValidationError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=exc.errors)
    except (PermissionDeniedError, CVServiceError) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    return _cv_resp(created)


@router.get(
    "/{cv_id}",
    response_model=CVResponse,
    summary="Retrieve a specific CV",
)
async def get_cv(
    cv_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    cv_svc: CVService = Depends(get_cv_service),
) -> CVResponse:
    try:
        cv = cv_svc.get_cv(
            cv_id=cv_id,
            requester_id=current_user.user_id,
            requester_role=current_user.role,
        )
    except PermissionDeniedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    except CVServiceError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    return _cv_resp(cv)


@router.put(
    "/{cv_id}",
    response_model=CVResponse,
    summary="Update a CV",
)
async def update_cv(
    cv_id: str,
    body: CVUpdateRequest,
    current_user: CurrentUser = Depends(get_current_user),
    cv_svc: CVService = Depends(get_cv_service),
) -> CVResponse:
    # Only include fields explicitly sent by the caller (preserves False/0/"")
    updates = body.model_dump(exclude_unset=True)
    try:
        updated = cv_svc.update_cv(
            cv_id=cv_id,
            updates=updates,
            requester_id=current_user.user_id,
            requester_role=current_user.role,
        )
    except PermissionDeniedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    except ValidationError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=exc.errors)
    except CVServiceError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    return _cv_resp(updated)


@router.delete(
    "/{cv_id}",
    response_model=MessageResponse,
    summary="Delete a CV (soft delete)",
)
async def delete_cv(
    cv_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    cv_svc: CVService = Depends(get_cv_service),
) -> MessageResponse:
    try:
        cv_svc.delete_cv(
            cv_id=cv_id,
            requester_id=current_user.user_id,
            requester_role=current_user.role,
        )
    except PermissionDeniedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    except CVServiceError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    return MessageResponse(message=f"CV {cv_id} deleted.")


@router.get(
    "/{cv_id}/export",
    summary="Export CV as an encrypted ZIP archive",
    response_class=Response,
    responses={
        200: {"content": {"application/zip": {}}, "description": "ZIP archive"},
        402: {"description": "Tier gate — upgrade required"},
        403: {"description": "Permission denied"},
        404: {"description": "CV not found"},
    },
)
async def export_cv(
    cv_id: str,
    format: str = Query(default="pdf", description="Export format: pdf | docx | json | xml"),
    current_user: CurrentUser = Depends(get_current_user),
    cv_svc: CVService = Depends(get_cv_service),
) -> Response:
    try:
        archive_bytes = cv_svc.export_cv(
            cv_id=cv_id,
            requester_id=current_user.user_id,
            requester_role=current_user.role,
            requester_tier=current_user.tier,
            export_format=format,
        )
    except TierGateError as exc:
        raise HTTPException(status_code=status.HTTP_402_PAYMENT_REQUIRED, detail=str(exc))
    except PermissionDeniedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    except CVServiceError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))

    return Response(
        content=archive_bytes,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="cv_{cv_id[:8]}.zip"'},
    )


@router.post(
    "/{cv_id}/submit-coach",
    response_model=DataResponse,
    summary="Submit a CV to a coach for review",
)
async def submit_to_coach(
    cv_id: str,
    body: SubmitToCoachRequest,
    current_user: CurrentUser = Depends(get_current_user),
    cv_svc: CVService = Depends(get_cv_service),
) -> DataResponse:
    try:
        result = cv_svc.submit_to_coach(
            cv_id=cv_id,
            coach_id=body.coach_id,
            requester_id=current_user.user_id,
            requester_role=current_user.role,
            requester_tier=current_user.tier,
        )
    except TierGateError as exc:
        raise HTTPException(status_code=status.HTTP_402_PAYMENT_REQUIRED, detail=str(exc))
    except PermissionDeniedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    except CVServiceError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    return DataResponse(data=result)


@router.post(
    "/{cv_id}/notes",
    response_model=DataResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add a coach note to a CV",
)
async def add_coach_note(
    cv_id: str,
    body: AddCoachNoteRequest,
    current_user: CurrentUser = Depends(get_current_user),
    cv_svc: CVService = Depends(get_cv_service),
) -> DataResponse:
    try:
        note = cv_svc.add_coach_note(
            cv_id=cv_id,
            note_text=body.note_text,
            coach_id=current_user.user_id,
            coach_role=current_user.role,
        )
    except PermissionDeniedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    except CVServiceError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    return DataResponse(data=note)


@router.get(
    "/{cv_id}/notes",
    response_model=DataResponse,
    summary="Retrieve all coach notes for a CV",
)
async def get_coach_notes(
    cv_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    cv_svc: CVService = Depends(get_cv_service),
) -> DataResponse:
    try:
        notes = cv_svc.get_coach_notes(
            cv_id=cv_id,
            requester_id=current_user.user_id,
            requester_role=current_user.role,
        )
    except PermissionDeniedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    except CVServiceError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    return DataResponse(data=notes)


@router.get(
    "/{cv_id}/history",
    response_model=DataResponse,
    summary="Retrieve version history for a CV",
)
async def get_version_history(
    cv_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    cv_svc: CVService = Depends(get_cv_service),
) -> DataResponse:
    try:
        history = cv_svc.get_version_history(
            cv_id=cv_id,
            requester_id=current_user.user_id,
            requester_role=current_user.role,
        )
    except PermissionDeniedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    except CVServiceError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    return DataResponse(data=history)
