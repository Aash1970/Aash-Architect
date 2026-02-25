"""
Test Suite: Tier System
Covers app/tier/tier_rules.py and app/services/tier_service.py
"""

import pytest
from app.tier.tier_rules import (
    get_tier_limits, is_feature_allowed, check_cv_limit,
    check_export_limit, is_export_format_allowed,
    require_feature, TierGateError, TIER_RULES, VALID_TIERS
)
from app.services.tier_service import TierService
from app.services.data_service import DataService


# ── Tier Limits ───────────────────────────────────────────────────────────────

class TestTierLimits:
    def test_free_tier_has_cv_limit(self):
        limits = get_tier_limits("Free")
        assert limits.max_cvs == 2

    def test_premium_tier_has_unlimited_cvs(self):
        limits = get_tier_limits("Premium")
        assert limits.max_cvs == -1

    def test_enterprise_tier_has_unlimited_cvs(self):
        limits = get_tier_limits("Enterprise")
        assert limits.max_cvs == -1

    def test_free_tier_no_ats(self):
        limits = get_tier_limits("Free")
        assert limits.ats_basic is False
        assert limits.ats_advanced is False

    def test_premium_tier_has_basic_ats(self):
        limits = get_tier_limits("Premium")
        assert limits.ats_basic is True

    def test_premium_tier_has_advanced_ats(self):
        limits = get_tier_limits("Premium")
        assert limits.ats_advanced is True

    def test_enterprise_tier_has_all_ats(self):
        limits = get_tier_limits("Enterprise")
        assert limits.ats_basic is True
        assert limits.ats_advanced is True
        assert limits.ats_analytics is True

    def test_free_tier_no_coach_submission(self):
        limits = get_tier_limits("Free")
        assert limits.coach_submission is False

    def test_premium_tier_coach_submission(self):
        limits = get_tier_limits("Premium")
        assert limits.coach_submission is True

    def test_free_tier_limited_exports(self):
        limits = get_tier_limits("Free")
        assert limits.max_exports_per_month == 3

    def test_premium_tier_unlimited_exports(self):
        limits = get_tier_limits("Premium")
        assert limits.max_exports_per_month == -1

    def test_unknown_tier_falls_back_to_free(self):
        limits = get_tier_limits("GoldTier")
        free_limits = get_tier_limits("Free")
        assert limits.max_cvs == free_limits.max_cvs

    def test_all_tiers_defined(self):
        for tier in VALID_TIERS:
            assert tier in TIER_RULES


# ── is_feature_allowed ────────────────────────────────────────────────────────

class TestIsFeatureAllowed:
    def test_ats_basic_not_allowed_free(self):
        assert is_feature_allowed("Free", "ats_basic") is False

    def test_ats_basic_allowed_premium(self):
        assert is_feature_allowed("Premium", "ats_basic") is True

    def test_ats_analytics_only_enterprise(self):
        assert is_feature_allowed("Free", "ats_analytics") is False
        assert is_feature_allowed("Premium", "ats_analytics") is False
        assert is_feature_allowed("Enterprise", "ats_analytics") is True

    def test_coach_submission_premium(self):
        assert is_feature_allowed("Premium", "coach_submission") is True

    def test_coach_submission_free(self):
        assert is_feature_allowed("Free", "coach_submission") is False

    def test_unknown_feature_returns_false(self):
        assert is_feature_allowed("Enterprise", "magic_feature") is False


# ── check_cv_limit ────────────────────────────────────────────────────────────

class TestCheckCvLimit:
    def test_free_tier_can_create_first_cv(self):
        assert check_cv_limit("Free", current_cv_count=0) is True

    def test_free_tier_can_create_second_cv(self):
        assert check_cv_limit("Free", current_cv_count=1) is True

    def test_free_tier_cannot_create_third_cv(self):
        assert check_cv_limit("Free", current_cv_count=2) is False

    def test_premium_unlimited(self):
        assert check_cv_limit("Premium", current_cv_count=999) is True

    def test_enterprise_unlimited(self):
        assert check_cv_limit("Enterprise", current_cv_count=999) is True


# ── check_export_limit ────────────────────────────────────────────────────────

class TestCheckExportLimit:
    def test_free_within_limit(self):
        assert check_export_limit("Free", 2) is True

    def test_free_at_limit(self):
        assert check_export_limit("Free", 3) is False

    def test_free_over_limit(self):
        assert check_export_limit("Free", 10) is False

    def test_premium_unlimited(self):
        assert check_export_limit("Premium", 10000) is True


# ── is_export_format_allowed ──────────────────────────────────────────────────

class TestIsExportFormatAllowed:
    def test_free_allows_pdf(self):
        assert is_export_format_allowed("Free", "pdf") is True

    def test_free_disallows_docx(self):
        assert is_export_format_allowed("Free", "docx") is False

    def test_premium_allows_pdf_docx_json(self):
        for fmt in ["pdf", "docx", "json"]:
            assert is_export_format_allowed("Premium", fmt) is True

    def test_enterprise_allows_xml(self):
        assert is_export_format_allowed("Enterprise", "xml") is True

    def test_case_insensitive(self):
        assert is_export_format_allowed("Free", "PDF") is True


# ── require_feature ───────────────────────────────────────────────────────────

class TestRequireFeature:
    def test_passes_for_allowed_feature(self):
        require_feature("Premium", "ats_basic")  # should not raise

    def test_raises_for_disallowed_feature(self):
        with pytest.raises(TierGateError) as exc_info:
            require_feature("Free", "ats_basic")
        assert exc_info.value.feature == "ats_basic"
        assert exc_info.value.current_tier == "Free"

    def test_tier_gate_error_has_required_tier(self):
        with pytest.raises(TierGateError) as exc_info:
            require_feature("Free", "coach_submission")
        assert exc_info.value.required_tier in ("Premium", "Enterprise")


# ── TierService integration ───────────────────────────────────────────────────

class TestTierService:
    def setup_method(self):
        self.ds = DataService()
        self.svc = TierService(self.ds)
        # Seed some CVs for the user in the data service
        for i in range(2):
            self.ds.create_cv({
                "cv_id": f"cv-test-{i}",
                "user_id": "user-free-01",
                "title": f"CV {i}",
                "is_deleted": False,
                "version": 1,
            })

    def test_free_user_at_limit_cannot_create(self):
        with pytest.raises(TierGateError):
            self.svc.assert_can_create_cv("user-free-01", "Free")

    def test_premium_user_can_always_create(self):
        # Premium is unlimited — should not raise regardless of count
        self.svc.assert_can_create_cv("user-free-01", "Premium")

    def test_assert_can_export_disallowed_format_raises(self):
        with pytest.raises(TierGateError):
            self.svc.assert_can_export("user-free-01", "Free", "xml")

    def test_assert_can_use_ats_basic_free_raises(self):
        with pytest.raises(TierGateError):
            self.svc.assert_can_use_ats_basic("Free")

    def test_assert_can_use_ats_basic_premium_passes(self):
        self.svc.assert_can_use_ats_basic("Premium")

    def test_assert_can_use_ats_analytics_enterprise_only(self):
        with pytest.raises(TierGateError):
            self.svc.assert_can_use_ats_analytics("Premium")
        self.svc.assert_can_use_ats_analytics("Enterprise")

    def test_assert_can_submit_to_coach_free_raises(self):
        with pytest.raises(TierGateError):
            self.svc.assert_can_submit_to_coach("Free")

    def test_get_limits_summary_returns_dict(self):
        summary = self.svc.get_limits_summary("Premium")
        assert summary["tier"] == "Premium"
        assert summary["ats_basic"] is True
        assert summary["max_cvs"] == "Unlimited"
