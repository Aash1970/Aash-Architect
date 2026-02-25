"""
Tier Rules — Production Grade
All tier-gating logic lives here.
UI MUST NOT enforce tier limits.
Services MUST call these functions before performing gated operations.

Tiers:
  Free       — Limited functionality
  Premium    — Full user features
  Enterprise — Full platform features including admin analytics
"""

from dataclasses import dataclass
from typing import Dict, Set, Optional

VALID_TIERS: Set[str] = {"Free", "Premium", "Enterprise"}


@dataclass(frozen=True)
class TierLimits:
    """Immutable limits definition for a tier."""
    max_cvs: int                    # -1 = unlimited
    ats_basic: bool
    ats_advanced: bool
    ats_analytics: bool
    coach_submission: bool
    max_exports_per_month: int      # -1 = unlimited
    export_formats: Set[str]
    version_history_days: int       # days of version history retained
    priority_support: bool


# ── Tier definitions ────────────────────────────────────────────────────────
TIER_RULES: Dict[str, TierLimits] = {
    "Free": TierLimits(
        max_cvs=2,
        ats_basic=False,
        ats_advanced=False,
        ats_analytics=False,
        coach_submission=False,
        max_exports_per_month=3,
        export_formats={"pdf"},
        version_history_days=7,
        priority_support=False,
    ),
    "Premium": TierLimits(
        max_cvs=-1,
        ats_basic=True,
        ats_advanced=True,
        ats_analytics=False,
        coach_submission=True,
        max_exports_per_month=-1,
        export_formats={"pdf", "docx", "json"},
        version_history_days=90,
        priority_support=True,
    ),
    "Enterprise": TierLimits(
        max_cvs=-1,
        ats_basic=True,
        ats_advanced=True,
        ats_analytics=True,
        coach_submission=True,
        max_exports_per_month=-1,
        export_formats={"pdf", "docx", "json", "xml"},
        version_history_days=365,
        priority_support=True,
    ),
}


def get_tier_limits(tier: str) -> TierLimits:
    """
    Returns the TierLimits for a given tier string.
    Falls back to Free tier for unknown tier values.
    """
    return TIER_RULES.get(tier, TIER_RULES["Free"])


def is_feature_allowed(tier: str, feature: str) -> bool:
    """
    Returns True if the feature is permitted on the given tier.

    Supported feature keys:
        ats_basic | ats_advanced | ats_analytics |
        coach_submission | priority_support
    """
    limits = get_tier_limits(tier)
    feature_map = {
        "ats_basic": limits.ats_basic,
        "ats_advanced": limits.ats_advanced,
        "ats_analytics": limits.ats_analytics,
        "coach_submission": limits.coach_submission,
        "priority_support": limits.priority_support,
    }
    return feature_map.get(feature, False)


def check_cv_limit(tier: str, current_cv_count: int) -> bool:
    """
    Returns True if the user can create another CV under their tier.
    Returns False if they have reached the tier limit.
    """
    limits = get_tier_limits(tier)
    if limits.max_cvs == -1:
        return True
    return current_cv_count < limits.max_cvs


def check_export_limit(tier: str, exports_this_month: int) -> bool:
    """
    Returns True if another export is allowed under the tier.
    """
    limits = get_tier_limits(tier)
    if limits.max_exports_per_month == -1:
        return True
    return exports_this_month < limits.max_exports_per_month


def is_export_format_allowed(tier: str, fmt: str) -> bool:
    """
    Returns True if the requested export format is allowed for the tier.
    """
    limits = get_tier_limits(tier)
    return fmt.lower() in limits.export_formats


class TierGateError(Exception):
    """
    Raised by services when a tier-gated operation is attempted
    by a user whose tier does not permit it.

    Attributes:
        feature:        The blocked feature key
        required_tier:  The minimum tier that unlocks this feature
        current_tier:   The user's current tier
    """
    def __init__(self, feature: str, required_tier: str, current_tier: str):
        self.feature = feature
        self.required_tier = required_tier
        self.current_tier = current_tier
        super().__init__(
            f"Feature '{feature}' requires '{required_tier}' tier. "
            f"Current tier: '{current_tier}'."
        )


def require_feature(tier: str, feature: str) -> None:
    """
    Asserts that a tier-gated feature is available.
    Raises TierGateError if not allowed.

    Usage in service layer:
        require_feature(user.tier, "ats_advanced")
    """
    if not is_feature_allowed(tier, feature):
        tier_unlock = _feature_minimum_tier(feature)
        raise TierGateError(
            feature=feature,
            required_tier=tier_unlock,
            current_tier=tier,
        )


def _feature_minimum_tier(feature: str) -> str:
    """Returns the lowest tier that unlocks a given feature."""
    for tier_name in ["Free", "Premium", "Enterprise"]:
        limits = TIER_RULES[tier_name]
        feature_map = {
            "ats_basic": limits.ats_basic,
            "ats_advanced": limits.ats_advanced,
            "ats_analytics": limits.ats_analytics,
            "coach_submission": limits.coach_submission,
            "priority_support": limits.priority_support,
        }
        if feature_map.get(feature, False):
            return tier_name
    return "Enterprise"
