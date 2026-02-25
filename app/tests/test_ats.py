"""
Test Suite: ATS Scoring Engine
Covers app/ats/scoring_engine.py
"""

import pytest
from app.ats.scoring_engine import (
    ATSEngine, ATSScore, ATSRecommendation, score_cv_against_job
)

# ── Fixtures ──────────────────────────────────────────────────────────────────

SAMPLE_CV = {
    "cv_id": "cv-test-001",
    "user_id": "user-001",
    "title": "Senior Python Developer CV",
    "personal_info": {
        "full_name": "Jane Doe",
        "email": "jane@example.com",
        "mobile": "+44 7700 123456",
        "location": "London, UK",
        "linkedin": "https://linkedin.com/in/janedoe",
        "summary": (
            "Senior Python developer with 8 years of experience building "
            "scalable microservices and RESTful APIs using FastAPI and Django. "
            "Strong background in DevOps, Docker, Kubernetes, and AWS."
        ),
    },
    "work_experience": [
        {
            "company": "TechCorp Ltd",
            "position": "Senior Software Engineer",
            "start_date": "2020-01-01",
            "end_date": "2024-01-01",
            "is_current": False,
            "description": (
                "Developed Python microservices using FastAPI and PostgreSQL. "
                "Led team of 5 engineers. Implemented CI/CD pipelines with GitHub Actions."
            ),
            "achievements": [
                "Reduced API response time by 40%",
                "Mentored 3 junior developers",
            ],
        },
        {
            "company": "StartupXYZ",
            "position": "Python Developer",
            "start_date": "2017-06-01",
            "end_date": "2020-01-01",
            "is_current": False,
            "description": "Built Django REST APIs. Managed AWS infrastructure.",
            "achievements": [],
        },
    ],
    "education": [
        {
            "institution": "University of London",
            "degree": "BSc Computer Science",
            "field_of_study": "Computer Science",
            "start_date": "2013-09-01",
            "end_date": "2017-06-30",
            "is_current": False,
        }
    ],
    "skills": [
        {"name": "Python", "level": "Expert"},
        {"name": "FastAPI", "level": "Expert"},
        {"name": "Django", "level": "Advanced"},
        {"name": "PostgreSQL", "level": "Advanced"},
        {"name": "Docker", "level": "Advanced"},
        {"name": "AWS", "level": "Intermediate"},
        {"name": "Kubernetes", "level": "Intermediate"},
        {"name": "GitHub Actions", "level": "Intermediate"},
    ],
    "languages": [
        {"name": "English", "proficiency": "Native"},
        {"name": "French", "proficiency": "B2"},
    ],
    "certifications": [
        {
            "name": "AWS Solutions Architect Associate",
            "issuer": "Amazon Web Services",
            "issue_date": "2022-03-15",
        }
    ],
}

SAMPLE_JD = """
We are looking for a Senior Python Developer to join our engineering team.

Requirements:
- 5+ years of Python development experience
- Strong experience with FastAPI or Django
- PostgreSQL and database design
- Docker and Kubernetes for containerization
- AWS cloud infrastructure experience
- CI/CD pipeline experience
- Experience leading small teams
- Strong problem-solving skills
- REST API design and development
- Microservices architecture experience
"""

MINIMAL_JD = "Software developer with Python experience needed."


# ── ATSEngine ────────────────────────────────────────────────────────────────

class TestATSEngine:
    def setup_method(self):
        self.engine = ATSEngine()

    def test_score_returns_ats_score_object(self):
        result = self.engine.score(SAMPLE_CV, SAMPLE_JD, tier="Premium")
        assert isinstance(result, ATSScore)

    def test_overall_score_in_range(self):
        result = self.engine.score(SAMPLE_CV, SAMPLE_JD, tier="Premium")
        assert 0 <= result.overall_score <= 100

    def test_keyword_match_rate_in_range(self):
        result = self.engine.score(SAMPLE_CV, SAMPLE_JD, tier="Premium")
        assert 0 <= result.keyword_match_rate <= 100

    def test_completeness_score_in_range(self):
        result = self.engine.score(SAMPLE_CV, SAMPLE_JD, tier="Premium")
        assert 0 <= result.completeness_score <= 100

    def test_format_score_in_range(self):
        result = self.engine.score(SAMPLE_CV, SAMPLE_JD, tier="Premium")
        assert 0 <= result.format_score <= 100

    def test_matched_keywords_are_list(self):
        result = self.engine.score(SAMPLE_CV, SAMPLE_JD)
        assert isinstance(result.matched_keywords, list)

    def test_missing_keywords_are_list(self):
        result = self.engine.score(SAMPLE_CV, SAMPLE_JD)
        assert isinstance(result.missing_keywords, list)

    def test_well_matched_cv_scores_higher(self):
        """CV matching job description well should score > minimal CV."""
        good_score = self.engine.score(SAMPLE_CV, SAMPLE_JD, tier="Premium")
        empty_cv = {
            "personal_info": {"full_name": "John", "email": "j@j.com"},
            "work_experience": [],
            "education": [],
            "skills": [],
            "languages": [],
            "certifications": [],
        }
        poor_score = self.engine.score(empty_cv, SAMPLE_JD, tier="Premium")
        assert good_score.overall_score > poor_score.overall_score

    def test_python_keyword_matched_in_sample_cv(self):
        result = self.engine.score(SAMPLE_CV, SAMPLE_JD, tier="Premium")
        assert "python" in result.matched_keywords

    def test_empty_job_description_raises(self):
        with pytest.raises(ValueError, match="not be empty"):
            self.engine.score(SAMPLE_CV, "", tier="Premium")

    def test_whitespace_job_description_raises(self):
        with pytest.raises(ValueError):
            self.engine.score(SAMPLE_CV, "   ", tier="Premium")

    def test_empty_cv_raises(self):
        with pytest.raises(ValueError, match="not be empty"):
            self.engine.score({}, SAMPLE_JD, tier="Premium")

    def test_recommendations_are_list(self):
        result = self.engine.score(SAMPLE_CV, SAMPLE_JD)
        assert isinstance(result.recommendations, list)

    def test_recommendations_have_priority(self):
        result = self.engine.score(SAMPLE_CV, SAMPLE_JD)
        for rec in result.recommendations:
            assert rec.priority in ("high", "medium", "low")

    def test_recommendations_have_impact_score(self):
        result = self.engine.score(SAMPLE_CV, SAMPLE_JD)
        for rec in result.recommendations:
            assert isinstance(rec.impact_score, (int, float))
            assert rec.impact_score >= 0

    def test_tier_recorded_in_result(self):
        result = self.engine.score(SAMPLE_CV, SAMPLE_JD, tier="Enterprise")
        assert result.tier_used == "Enterprise"

    def test_free_tier_no_advanced_analytics(self):
        result = self.engine.score(SAMPLE_CV, SAMPLE_JD, tier="Free")
        assert result.advanced_analytics is None

    def test_enterprise_tier_has_advanced_analytics(self):
        result = self.engine.score(SAMPLE_CV, SAMPLE_JD, tier="Enterprise")
        assert result.advanced_analytics is not None

    def test_advanced_analytics_has_required_keys(self):
        result = self.engine.score(SAMPLE_CV, SAMPLE_JD, tier="Enterprise")
        aa = result.advanced_analytics
        required_keys = [
            "experience_years", "cv_word_count",
            "keyword_density_pct", "match_breakdown"
        ]
        for key in required_keys:
            assert key in aa, f"Missing key: {key}"

    def test_recommendations_sorted_by_impact(self):
        """Recommendations should be sorted highest impact first."""
        result = self.engine.score(SAMPLE_CV, SAMPLE_JD)
        if len(result.recommendations) > 1:
            for i in range(len(result.recommendations) - 1):
                assert (
                    result.recommendations[i].impact_score
                    >= result.recommendations[i + 1].impact_score
                )


# ── ATSScore ──────────────────────────────────────────────────────────────────

class TestATSScore:
    def _make_score(self, overall: float) -> ATSScore:
        return ATSScore(
            overall_score=overall,
            keyword_match_rate=overall,
            completeness_score=overall,
            format_score=overall,
            matched_keywords=[],
            missing_keywords=[],
            recommendations=[],
            tier_used="Premium",
        )

    def test_grade_a(self):
        assert self._make_score(90).grade == "A"

    def test_grade_b(self):
        assert self._make_score(75).grade == "B"

    def test_grade_c(self):
        assert self._make_score(60).grade == "C"

    def test_grade_d(self):
        assert self._make_score(45).grade == "D"

    def test_grade_f(self):
        assert self._make_score(30).grade == "F"

    def test_to_dict_has_all_keys(self):
        score = self._make_score(75)
        d = score.to_dict()
        required = [
            "overall_score", "keyword_match_rate", "completeness_score",
            "format_score", "matched_keywords", "missing_keywords",
            "recommendations", "tier_used"
        ]
        for key in required:
            assert key in d, f"Missing key: {key}"

    def test_to_dict_scores_rounded(self):
        score = ATSScore(
            overall_score=75.12345,
            keyword_match_rate=60.99999,
            completeness_score=80.555,
            format_score=70.0,
            matched_keywords=[],
            missing_keywords=[],
            recommendations=[],
            tier_used="Free",
        )
        d = score.to_dict()
        # Should be rounded to 1 decimal
        assert d["overall_score"] == 75.1
        assert d["keyword_match_rate"] == 61.0


# ── Convenience function ───────────────────────────────────────────────────────

class TestScoreCvAgainstJob:
    def test_returns_ats_score(self):
        result = score_cv_against_job(SAMPLE_CV, SAMPLE_JD, tier="Premium")
        assert isinstance(result, ATSScore)

    def test_default_tier_is_free(self):
        result = score_cv_against_job(SAMPLE_CV, MINIMAL_JD)
        assert result.tier_used == "Free"
