"""
ATS Service — Production Grade
All ATS operations routed through this service.
UI must NOT import scoring_engine or call it directly.
Permission and tier gating enforced here.
Returns structured ATSScore DTO.
"""

from app.ats.scoring_engine import ATSEngine, ATSScore
from app.services.role_service import RoleService, PermissionDeniedError
from app.tier.tier_rules import require_feature, TierGateError


class ATSServiceError(Exception):
    """Raised on ATS service failures."""


class ATSService:
    """
    Orchestrates ATS scoring with full enforcement of:
      - Role-based access control (requires ats.basic permission)
      - Tier gating (requires ats_basic feature on tier)
      - Delegates scoring to ATSEngine internally
    UI must call analyse_cv() and must not access scoring_engine directly.
    """

    def __init__(self, role_service: RoleService | None = None):
        self._engine = ATSEngine()
        self._rs = role_service or RoleService()

    def analyse_cv(
        self,
        cv_dict: dict,
        job_description: str,
        tier: str,
        requester_role: str,
    ) -> ATSScore:
        """
        Scores a CV against a job description.

        Enforces:
          - Role: ats.basic permission
          - Tier: ats_basic feature gate

        Args:
            cv_dict:         CV data dictionary
            job_description: Raw job description text
            tier:            User's tier ('Free' | 'Premium' | 'Enterprise')
            requester_role:  Requesting user's role string

        Returns:
            ATSScore with full breakdown.

        Raises:
            PermissionDeniedError: if role lacks ats.basic permission
            TierGateError:         if tier does not include ats_basic
            ATSServiceError:       on invalid inputs
        """
        self._rs.require_permission(requester_role, "ats.basic")
        require_feature(tier, "ats_basic")

        if not cv_dict:
            raise ATSServiceError("CV data must not be empty.")
        if not job_description or not job_description.strip():
            raise ATSServiceError("Job description must not be empty.")

        return self._engine.score(cv_dict, job_description, tier)
