"""
Test Suite: Validation System
Covers all validators in app/validation/validators.py
"""

import pytest
from app.validation.validators import (
    validate_email, validate_mobile, validate_date_string,
    validate_min_length, validate_required, validate_text_field,
    validate_url, validate_personal_info, validate_work_experience,
    validate_education, validate_skill, sanitize_text,
    validate_certification, validate_language_entry, ValidationError,
)


# ── sanitize_text ────────────────────────────────────────────────────────────

class TestSanitizeText:
    def test_strips_whitespace(self):
        assert sanitize_text("  hello  ") == "hello"

    def test_escapes_html(self):
        result = sanitize_text('<script>alert("xss")</script>')
        assert "<script>" not in result
        assert "&lt;" in result

    def test_handles_non_string(self):
        assert sanitize_text(None) == ""  # type: ignore
        assert sanitize_text(123) == ""   # type: ignore

    def test_empty_string(self):
        assert sanitize_text("") == ""


# ── validate_required ────────────────────────────────────────────────────────

class TestValidateRequired:
    def test_passes_non_empty(self):
        assert validate_required("hello", "Field") == []

    def test_fails_empty_string(self):
        errors = validate_required("", "Field")
        assert len(errors) == 1
        assert "required" in errors[0].lower()

    def test_fails_whitespace_only(self):
        errors = validate_required("   ", "Field")
        assert len(errors) == 1

    def test_fails_none(self):
        errors = validate_required(None, "Field")
        assert len(errors) == 1


# ── validate_min_length ──────────────────────────────────────────────────────

class TestValidateMinLength:
    def test_passes_exact_min(self):
        assert validate_min_length("ab", "Field", min_len=2) == []

    def test_passes_above_min(self):
        assert validate_min_length("hello world", "Field", min_len=2) == []

    def test_fails_below_min(self):
        errors = validate_min_length("a", "Field", min_len=2)
        assert len(errors) == 1
        assert "2" in errors[0]

    def test_single_char_fails_default_min(self):
        # Architecture spec: No record may save with 1 character input
        errors = validate_min_length("X", "Name", min_len=2)
        assert len(errors) > 0

    def test_non_string_fails(self):
        errors = validate_min_length(123, "Field")  # type: ignore
        assert len(errors) > 0


# ── validate_email ───────────────────────────────────────────────────────────

class TestValidateEmail:
    def test_valid_emails(self):
        valid = [
            "user@example.com",
            "user.name+tag@example.co.uk",
            "user123@test.org",
        ]
        for email in valid:
            assert validate_email(email) == [], f"Should pass: {email}"

    def test_invalid_emails(self):
        invalid = [
            "notanemail",
            "@nodomain.com",
            "missing@.com",
            "double@@domain.com",
            "",
            "   ",
        ]
        for email in invalid:
            assert len(validate_email(email)) > 0, f"Should fail: {email}"

    def test_custom_field_name(self):
        errors = validate_email("bad", "Work Email")
        assert "Work Email" in errors[0]


# ── validate_mobile ──────────────────────────────────────────────────────────

class TestValidateMobile:
    def test_valid_mobiles(self):
        valid = [
            "+44 7700 123456",
            "07700123456",
            "+1 (555) 000-1234",
            "0044 7700 123456",
        ]
        for mobile in valid:
            assert validate_mobile(mobile) == [], f"Should pass: {mobile}"

    def test_invalid_mobiles(self):
        invalid = [
            "",
            "abc",
            "phone number here",
            "123",  # too short (< 7 digits)
        ]
        for mobile in invalid:
            assert len(validate_mobile(mobile)) > 0, f"Should fail: {mobile}"

    def test_alpha_only_fails(self):
        errors = validate_mobile("ABCDEFGH")
        assert len(errors) > 0


# ── validate_date_string ─────────────────────────────────────────────────────

class TestValidateDateString:
    def test_valid_dates(self):
        valid = ["2024-01-15", "2000-12-31", "1990-06-01"]
        for d in valid:
            assert validate_date_string(d) == [], f"Should pass: {d}"

    def test_invalid_dates(self):
        invalid = [
            "15/01/2024",     # wrong format
            "2024-13-01",     # invalid month
            "2024-01-32",     # invalid day
            "January 2024",   # text format
            "",
            "2024-1-1",       # not zero-padded
        ]
        for d in invalid:
            assert len(validate_date_string(d)) > 0, f"Should fail: {d}"


# ── validate_url ─────────────────────────────────────────────────────────────

class TestValidateUrl:
    def test_valid_urls(self):
        valid = [
            "https://example.com",
            "http://test.org/path?q=1",
            "https://linkedin.com/in/user",
        ]
        for url in valid:
            assert validate_url(url) == [], f"Should pass: {url}"

    def test_optional_empty_passes(self):
        assert validate_url("") == []
        assert validate_url(None) == []  # type: ignore

    def test_invalid_schemes_fail(self):
        invalid = ["ftp://example.com", "example.com", "just text"]
        for url in invalid:
            assert len(validate_url(url)) > 0, f"Should fail: {url}"


# ── validate_personal_info ───────────────────────────────────────────────────

class TestValidatePersonalInfo:
    VALID_PI = {
        "full_name": "Jane Doe",
        "email": "jane@example.com",
        "mobile": "+44 7700 000000",
        "location": "London, UK",
    }

    def test_valid_personal_info(self):
        errors = validate_personal_info(self.VALID_PI)
        assert errors == {}

    def test_missing_required_fields(self):
        for field in ["full_name", "email", "mobile", "location"]:
            data = {**self.VALID_PI, field: ""}
            errors = validate_personal_info(data)
            assert field in errors, f"Should fail for missing {field}"

    def test_one_char_name_fails(self):
        data = {**self.VALID_PI, "full_name": "J"}
        errors = validate_personal_info(data)
        assert "full_name" in errors

    def test_invalid_email_format(self):
        data = {**self.VALID_PI, "email": "not-an-email"}
        errors = validate_personal_info(data)
        assert "email" in errors

    def test_invalid_mobile_format(self):
        data = {**self.VALID_PI, "mobile": "abc"}
        errors = validate_personal_info(data)
        assert "mobile" in errors

    def test_optional_summary_short_fails(self):
        data = {**self.VALID_PI, "summary": "Hi"}
        errors = validate_personal_info(data)
        assert "summary" in errors

    def test_optional_summary_none_passes(self):
        data = {**self.VALID_PI, "summary": None}
        errors = validate_personal_info(data)
        assert errors == {}

    def test_invalid_linkedin_url(self):
        data = {**self.VALID_PI, "linkedin": "not-a-url"}
        errors = validate_personal_info(data)
        assert "linkedin" in errors


# ── validate_work_experience ──────────────────────────────────────────────────

class TestValidateWorkExperience:
    VALID_WORK = {
        "company": "Acme Corp",
        "position": "Software Engineer",
        "start_date": "2020-01-01",
        "end_date": "2023-06-30",
        "is_current": False,
        "description": "Developed and maintained Python microservices.",
    }

    def test_valid_work_entry(self):
        assert validate_work_experience(self.VALID_WORK) == {}

    def test_missing_company(self):
        data = {**self.VALID_WORK, "company": ""}
        assert "company" in validate_work_experience(data)

    def test_missing_position(self):
        data = {**self.VALID_WORK, "position": ""}
        assert "position" in validate_work_experience(data)

    def test_invalid_start_date(self):
        data = {**self.VALID_WORK, "start_date": "invalid"}
        assert "start_date" in validate_work_experience(data)

    def test_missing_end_date_when_not_current(self):
        data = {**self.VALID_WORK, "end_date": "", "is_current": False}
        assert "end_date" in validate_work_experience(data)

    def test_no_end_date_needed_when_current(self):
        data = {**self.VALID_WORK, "end_date": None, "is_current": True}
        errors = validate_work_experience(data)
        assert "end_date" not in errors

    def test_short_description_fails(self):
        data = {**self.VALID_WORK, "description": "Hi"}
        assert "description" in validate_work_experience(data)


# ── validate_education ────────────────────────────────────────────────────────

class TestValidateEducation:
    VALID_EDU = {
        "institution": "University of London",
        "degree": "Bachelor of Science",
        "field_of_study": "Computer Science",
        "start_date": "2015-09-01",
        "end_date": "2019-06-30",
        "is_current": False,
    }

    def test_valid_education(self):
        assert validate_education(self.VALID_EDU) == {}

    def test_missing_institution(self):
        data = {**self.VALID_EDU, "institution": ""}
        assert "institution" in validate_education(data)

    def test_single_char_degree_fails(self):
        data = {**self.VALID_EDU, "degree": "B"}
        assert "degree" in validate_education(data)


# ── validate_skill ────────────────────────────────────────────────────────────

class TestValidateSkill:
    def test_valid_skill(self):
        assert validate_skill({"name": "Python", "level": "Expert"}) == {}

    def test_missing_name(self):
        assert "name" in validate_skill({"name": "", "level": "Beginner"})

    def test_single_char_name_fails(self):
        assert "name" in validate_skill({"name": "C", "level": "Advanced"})

    def test_invalid_level(self):
        assert "level" in validate_skill({"name": "Python", "level": "Pro"})

    def test_all_valid_levels(self):
        for level in ["Beginner", "Intermediate", "Advanced", "Expert"]:
            assert validate_skill({"name": "Skill", "level": level}) == {}


# ── ValidationError exception ────────────────────────────────────────────────

class TestValidationError:
    def test_exception_contains_errors(self):
        exc = ValidationError({"email": ["Invalid format"], "name": ["Too short"]})
        assert "email" in exc.errors
        assert "name" in exc.errors

    def test_first_error_returns_string(self):
        exc = ValidationError({"field": ["Error message"]})
        assert exc.first_error() == "Error message"

    def test_str_representation(self):
        exc = ValidationError({"email": ["bad"]})
        assert "email" in str(exc)
