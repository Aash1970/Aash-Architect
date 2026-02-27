"""
/drafts router — CV builder autosave.

POST   /drafts/{cv_id}    Save or update an autosave draft for a CV
GET    /drafts/{cv_id}    Load the current autosave draft
DELETE /drafts/{cv_id}    Discard the draft after a successful publish
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.drafts.draft_service import DraftError, DraftService
from backend.api.deps import CurrentUser, get_current_user, get_draft_service
from backend.api.schemas.common import DataResponse, MessageResponse
from backend.api.schemas.drafts import DraftResponse, DraftSaveRequest

router = APIRouter()


@router.post(
    "/{cv_id}",
    response_model=DraftResponse,
    summary="Save or update an autosave draft for a CV",
)
async def save_draft(
    cv_id: str,
    body: DraftSaveRequest,
    current_user: CurrentUser = Depends(get_current_user),
    draft_svc: DraftService = Depends(get_draft_service),
) -> DraftResponse:
    try:
        draft = draft_svc.save_draft(
            user_id=current_user.user_id,
            draft_data=body.data,
            cv_id=cv_id,
        )
    except DraftError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    return DraftResponse.from_dict(draft)


@router.get(
    "/{cv_id}",
    response_model=DataResponse,
    summary="Load the current autosave draft for a CV",
)
async def load_draft(
    cv_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    draft_svc: DraftService = Depends(get_draft_service),
) -> DataResponse:
    draft = draft_svc.load_draft(user_id=current_user.user_id, cv_id=cv_id)
    return DataResponse(data=draft)


@router.delete(
    "/{cv_id}",
    response_model=MessageResponse,
    summary="Discard the autosave draft for a CV",
)
async def discard_draft(
    cv_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    draft_svc: DraftService = Depends(get_draft_service),
) -> MessageResponse:
    draft_svc.discard_draft(user_id=current_user.user_id, cv_id=cv_id)
    return MessageResponse(message=f"Draft for CV {cv_id} discarded.")
