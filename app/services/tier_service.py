"""
Tier Service — Production Grade
All tier gate enforcement happens here.
UI MUST NOT enforce tier logic.
Services call this before performing tier-gated operations.
"""

from app.tier.tier_rules import (
    get_tier_limits, is_feature_allowed, check_cv_limit,
    check_export_limit, is_export_format_allowed,
    require_feature, TierGateError
)
from app.services.data_service import DataService


class TierService:
    """
    Service layer for tier-gating checks.
    Injects DataService for count-based checks.
    """

    def __init__(self, data_service: DataService):
        self._ds = data_service

    def assert_can_create_cv(self, user_id: str, tier: str) -> None:
        """
        Checks whether the user can create another CV under their tier.

        Raises:
            TierGateError if the CV count limit is reached.
        """
        limits = get_tier_limits(tier)
        if limits.max_cvs == -1:
            return  # Unlimited

        current_cvs = self._ds.list_cvs_for_user(user_id)
        if not check_cv_limit(tier, len(current_cvs)):
            raise TierGateError(
                feature="cv_creation",
                required_tier="Premium",
                current_tier=tier,
            )

    def assert_can_export(self, user_id: str, tier: str, fmt: str) -> None:
        """
        Checks whether the user can export in the given format.

        Raises:
            TierGateError if monthly export limit reached or format not allowed.
        """
        if not is_export_format_allowed(tier, fmt):
            raise TierGateError(
                feature=f"export_format:{fmt}",
                required_tier="Premium",
                current_tier=tier,
            )

        limits = get_tier_limits(tier)
        if limits.max_exports_per_month == -1:
            return  # Unlimited

        exports_this_month = self._ds.count_exports_this_month(user_id)
        if not check_export_limit(tier, exports_this_month):
            raise TierGateError(
                feature="export",
                required_tier="Premium",
                current_tier=tier,
            )

    def assert_can_use_ats_basic(self, tier: str) -> None:
        """Raises TierGateError if basic ATS not allowed for tier."""
        require_feature(tier, "ats_basic")

    def assert_can_use_ats_advanced(self, tier: str) -> None:
        """Raises TierGateError if advanced ATS not allowed for tier."""
        require_feature(tier, "ats_advanced")

    def assert_can_use_ats_analytics(self, tier: str) -> None:
        """Raises TierGateError if ATS analytics not allowed for tier."""
        require_feature(tier, "ats_analytics")

    def assert_can_submit_to_coach(self, tier: str) -> None:
        """Raises TierGateError if coach submission not allowed for tier."""
        require_feature(tier, "coach_submission")

    def get_limits_summary(self, tier: str) -> dict:
        """Returns a dict summary of tier limits for UI display."""
        limits = get_tier_limits(tier)
        return {
            "tier": tier,
            "max_cvs": limits.max_cvs if limits.max_cvs != -1 else "Unlimited",
            "ats_basic": limits.ats_basic,
            "ats_advanced": limits.ats_advanced,
            "ats_analytics": limits.ats_analytics,
            "coach_submission": limits.coach_submission,
            "max_exports_per_month": (
                limits.max_exports_per_month
                if limits.max_exports_per_month != -1
                else "Unlimited"
            ),
            "export_formats": list(limits.export_formats),
            "version_history_days": limits.version_history_days,
        }
