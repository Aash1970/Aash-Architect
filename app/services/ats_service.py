"""
ATS Service — Production Grade
Encapsulates all ATS scoring logic and tier enforcement.
UI MUST call this service. UI MUST NOT import scoring_engine.
No UI dependencies. No Streamlit imports.
"""

from __future__ import annotations

from typing import Dict, Any

from app.ats.scoring_engine import ATSEngine
from app.services.tier_service import TierService
from app.services.cv_service import CVService
from app.tier.tier_rules import TierGateError


class ATSServiceError(Exception):
    """Raised on ATS service operation failures."""


class ATSService:
    """
    Service layer for ATS analysis.

    Encapsulates:
      - Tier gate enforcement (via TierService)
      - CV retrieval (via CVService)
      - Scoring (via ATSEngine)

    UI receives only plain dicts from this service.
    No scoring engine types leak into the UI layer.
    """

    def __init__(
        self,
        cv_service: CVService,
        tier_service: TierService,
    ):
        self._cv_service = cv_service
        self._tier_service = tier_service
        self._engine = ATSEngine()

    def analyse_cv(
        self,
        cv_id: str,
        job_description: str,
        requester_id: str,
        requester_role: str,
        requester_tier: str,
    ) -> Dict[str, Any]:
        """
        Analyses a CV against a job description.

        Enforces:
          - Tier: ats_basic required (Premium or Enterprise)
          - Role: via CVService.get_cv() (raises PermissionDeniedError on failure)

        Args:
            cv_id:           CV identifier to analyse
            job_description: Raw job description text
            requester_id:    User performing the request
            requester_role:  Role of the requester
            requester_tier:  Tier of the requester

        Returns:
            ATSScore serialised as plain dict with keys:
              overall_score, keyword_match_rate, completeness_score,
              format_score, matched_keywords, missing_keywords,
              recommendations, tier_used, advanced_analytics

        Raises:
            ATSServiceError:         If job description is too short
            TierGateError:           If tier does not allow ATS usage
            PermissionDeniedError:   If requester cannot access the CV
            CVServiceError:          If CV is not found
        """
        if not job_description or len(job_description.strip()) < 20:
            raise ATSServiceError("Job description must be at least 20 characters.")

        # Enforce tier gate — raises TierGateError if not allowed
        self._tier_service.assert_can_use_ats_basic(requester_tier)

        # Fetch CV — enforces role-based access internally
        cv = self._cv_service.get_cv(
            cv_id=cv_id,
            requester_id=requester_id,
            requester_role=requester_role,
        )

        # Run scoring engine
        score = self._engine.score(
            cv_dict=cv,
            job_description=job_description,
            tier=requester_tier,
        )

        return score.to_dict()

    def get_tier_info(self, tier: str) -> Dict[str, Any]:
        """
        Returns tier capability summary.

        Args:
            tier: User's tier string

        Returns:
            Dict with tier feature flags and limits
        """
        return self._tier_service.get_limits_summary(tier)
