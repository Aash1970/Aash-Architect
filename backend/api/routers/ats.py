"""
/ats router — ATS CV scoring.

POST  /ats/analyse        Score a CV against a job description
GET   /ats/tier-info      Return tier feature summary for the current user
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.services.ats_service import ATSService, ATSServiceError
from app.services.cv_service import CVServiceError
from app.services.role_service import PermissionDeniedError
from app.tier.tier_rules import TierGateError
from backend.api.deps import CurrentUser, get_ats_service, get_current_user
from backend.api.schemas.ats import ATSAnalyseRequest, ATSScoreResponse
from backend.api.schemas.common import DataResponse

router = APIRouter()


@router.post(
    "/analyse",
    response_model=ATSScoreResponse,
    summary="Score a CV against a job description",
)
async def analyse_cv(
    body: ATSAnalyseRequest,
    current_user: CurrentUser = Depends(get_current_user),
    ats_svc: ATSService = Depends(get_ats_service),
) -> ATSScoreResponse:
    try:
        score_dict = ats_svc.analyse_cv(
            cv_id=body.cv_id,
            job_description=body.job_description,
            requester_id=current_user.user_id,
            requester_role=current_user.role,
            requester_tier=current_user.tier,
        )
    except TierGateError as exc:
        raise HTTPException(status_code=status.HTTP_402_PAYMENT_REQUIRED, detail=str(exc))
    except PermissionDeniedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    except CVServiceError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except ATSServiceError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    return ATSScoreResponse.from_dict(score_dict)


@router.get(
    "/tier-info",
    response_model=DataResponse,
    summary="Return ATS feature availability for the current user's tier",
)
async def tier_info(
    current_user: CurrentUser = Depends(get_current_user),
    ats_svc: ATSService = Depends(get_ats_service),
) -> DataResponse:
    info = ats_svc.get_tier_info(current_user.tier)
    return DataResponse(data=info)
