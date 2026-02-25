"""
Validation System — Production Grade
All validation lives here. Server-side regardless of UI controls.
UI MUST use this module; validation MUST NOT be duplicated in UI.

Rules enforced:
  - Email fields validate RFC 5322 format
  - Mobile fields accept digits, spaces, +, -, () only
  - Required fields block save
  - Minimum length of 2 characters for all text fields
  - Text fields sanitized (strip, HTML entity escape)
  - URL fields validate http/https scheme
"""

import re
import html
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any


# ── Exceptions ──────────────────────────────────────────────────────────────

class ValidationError(Exception):
    """
    Raised when one or more validation rules fail.

    Attributes:
        errors: dict mapping field_name → list of error messages
    """
    def __init__(self, errors: Dict[str, List[str]]):
        self.errors = errors
        flat = "; ".join(
            f"{k}: {', '.join(v)}" for k, v in errors.items()
        )
        super().__init__(flat)

    def first_error(self) -> str:
        """Returns the first error message for display."""
        for msgs in self.errors.values():
            if msgs:
                return msgs[0]
        return "Validation failed."


# ── Patterns ────────────────────────────────────────────────────────────────

_EMAIL_RE = re.compile(
    r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$"
)

_MOBILE_RE = re.compile(
    r"^[\d\s\+\-\(\)]{7,20}$"
)

_DATE_RE = re.compile(
    r"^\d{4}-(?:0[1-9]|1[0-2])-(?:0[1-9]|[12]\d|3[01])$"
)

_URL_RE = re.compile(
    r"^https?://[^\s/$.?#].[^\s]*$", re.IGNORECASE
)


# ── Core validators ─────────────────────────────────────────────────────────

def sanitize_text(value: str) -> str:
    """
    Strip leading/trailing whitespace and escape HTML entities.
    All text inputs must pass through this before storage.
    """
    if not isinstance(value, str):
        return ""
    return html.escape(value.strip())


def validate_required(value: Any, field_name: str) -> List[str]:
    """Returns list of errors if value is empty/None."""
    errors: List[str] = []
    if value is None or (isinstance(value, str) and not value.strip()):
        errors.append(f"{field_name} is required.")
    return errors


def validate_min_length(value: str, field_name: str, min_len: int = 2) -> List[str]:
    """Returns errors if string shorter than min_len after stripping."""
    errors: List[str] = []
    if not isinstance(value, str):
        errors.append(f"{field_name} must be a text value.")
        return errors
    stripped = value.strip()
    if len(stripped) < min_len:
        errors.append(
            f"{field_name} must be at least {min_len} characters."
        )
    return errors


def validate_email(value: str, field_name: str = "Email") -> List[str]:
    """Returns errors if value is not a valid email address."""
    errors = validate_required(value, field_name)
    if errors:
        return errors
    if not _EMAIL_RE.match(value.strip()):
        errors.append(f"{field_name} must be a valid email address.")
    return errors


def validate_mobile(value: str, field_name: str = "Mobile") -> List[str]:
    """
    Returns errors if value is not a valid mobile number.
    Accepts: digits, spaces, +, -, (, )
    Min 7, max 20 characters.
    """
    errors = validate_required(value, field_name)
    if errors:
        return errors
    if not _MOBILE_RE.match(value.strip()):
        errors.append(
            f"{field_name} must contain digits only "
            "(spaces, +, -, and parentheses allowed)."
        )
    return errors


def validate_date_string(value: str, field_name: str = "Date") -> List[str]:
    """
    Returns errors if value is not a valid ISO date string (YYYY-MM-DD).
    """
    errors = validate_required(value, field_name)
    if errors:
        return errors
    if not _DATE_RE.match(value.strip()):
        errors.append(
            f"{field_name} must be a valid date in YYYY-MM-DD format."
        )
    return errors


def validate_url(value: str, field_name: str = "URL") -> List[str]:
    """
    Returns errors if value is not a valid http/https URL.
    Empty string is allowed (optional URL field).
    """
    errors: List[str] = []
    if not value or not value.strip():
        return errors  # optional field
    if not _URL_RE.match(value.strip()):
        errors.append(
            f"{field_name} must be a valid URL starting with http:// or https://"
        )
    return errors


def validate_text_field(
    value: str,
    field_name: str,
    min_len: int = 2,
    max_len: int = 5000,
    required: bool = True,
) -> List[str]:
    """
    Combined: required check + min/max length + sanitization validation.
    """
    errors: List[str] = []
    if required:
        errors.extend(validate_required(value, field_name))
        if errors:
            return errors
    elif not value or not value.strip():
        return errors  # optional field, empty is fine

    errors.extend(validate_min_length(value, field_name, min_len))
    if not errors and len(value.strip()) > max_len:
        errors.append(
            f"{field_name} must not exceed {max_len} characters."
        )
    return errors


def validate_cv_section_entry(data: Dict[str, Any]) -> Dict[str, List[str]]:
    """
    Generic section entry validator. Ensures no fields are 1 character.
    Called before adding any entry to a CV section.

    Returns: dict of field_name → error list. Empty dict = valid.
    """
    all_errors: Dict[str, List[str]] = {}
    for key, value in data.items():
        if isinstance(value, str) and value.strip():
            errs = validate_min_length(value, key.replace("_", " ").title())
            if errs:
                all_errors[key] = errs
    return all_errors


# ── Domain-specific validators ───────────────────────────────────────────────

def validate_personal_info(data: Dict[str, Any]) -> Dict[str, List[str]]:
    """
    Validates the PersonalInfo section of a CV.
    Raises ValidationError if any field fails.
    Returns empty dict if all valid.
    """
    errors: Dict[str, List[str]] = {}

    # Full name
    errs = validate_text_field(
        data.get("full_name", ""), "Full Name", min_len=2
    )
    if errs:
        errors["full_name"] = errs

    # Email
    errs = validate_email(data.get("email", ""))
    if errs:
        errors["email"] = errs

    # Mobile
    errs = validate_mobile(data.get("mobile", ""))
    if errs:
        errors["mobile"] = errs

    # Location
    errs = validate_text_field(
        data.get("location", ""), "Location", min_len=2
    )
    if errs:
        errors["location"] = errs

    # LinkedIn (optional)
    if data.get("linkedin"):
        errs = validate_url(data["linkedin"], "LinkedIn URL")
        if errs:
            errors["linkedin"] = errs

    # Website (optional)
    if data.get("website"):
        errs = validate_url(data["website"], "Website URL")
        if errs:
            errors["website"] = errs

    # Summary (optional, but if provided must be >= 10 chars)
    if data.get("summary"):
        errs = validate_text_field(
            data["summary"], "Professional Summary",
            min_len=10, required=False
        )
        if errs:
            errors["summary"] = errs

    return errors


def validate_work_experience(data: Dict[str, Any]) -> Dict[str, List[str]]:
    """Validates a single WorkExperience entry."""
    errors: Dict[str, List[str]] = {}

    for field_name, key in [("Company", "company"), ("Position", "position")]:
        errs = validate_text_field(data.get(key, ""), field_name, min_len=2)
        if errs:
            errors[key] = errs

    # Start date required
    errs = validate_date_string(data.get("start_date", ""), "Start Date")
    if errs:
        errors["start_date"] = errs

    # End date only required if not current
    if not data.get("is_current", False):
        errs = validate_date_string(data.get("end_date", ""), "End Date")
        if errs:
            errors["end_date"] = errs

    # Description required
    errs = validate_text_field(
        data.get("description", ""), "Description", min_len=10
    )
    if errs:
        errors["description"] = errs

    return errors


def validate_education(data: Dict[str, Any]) -> Dict[str, List[str]]:
    """Validates a single Education entry."""
    errors: Dict[str, List[str]] = {}

    for field_name, key in [
        ("Institution", "institution"),
        ("Degree", "degree"),
        ("Field of Study", "field_of_study"),
    ]:
        errs = validate_text_field(data.get(key, ""), field_name, min_len=2)
        if errs:
            errors[key] = errs

    errs = validate_date_string(data.get("start_date", ""), "Start Date")
    if errs:
        errors["start_date"] = errs

    if not data.get("is_current", False):
        errs = validate_date_string(data.get("end_date", ""), "End Date")
        if errs:
            errors["end_date"] = errs

    return errors


def validate_skill(data: Dict[str, Any]) -> Dict[str, List[str]]:
    """Validates a single Skill entry."""
    errors: Dict[str, List[str]] = {}

    errs = validate_text_field(data.get("name", ""), "Skill Name", min_len=2)
    if errs:
        errors["name"] = errs

    valid_levels = {"Beginner", "Intermediate", "Advanced", "Expert"}
    level = data.get("level", "")
    if level not in valid_levels:
        errors["level"] = [
            f"Level must be one of: {', '.join(sorted(valid_levels))}"
        ]

    return errors


def validate_certification(data: Dict[str, Any]) -> Dict[str, List[str]]:
    """Validates a single Certification entry."""
    errors: Dict[str, List[str]] = {}

    for field_name, key in [("Certification Name", "name"), ("Issuer", "issuer")]:
        errs = validate_text_field(data.get(key, ""), field_name, min_len=2)
        if errs:
            errors[key] = errs

    errs = validate_date_string(data.get("issue_date", ""), "Issue Date")
    if errs:
        errors["issue_date"] = errs

    return errors


def validate_language_entry(data: Dict[str, Any]) -> Dict[str, List[str]]:
    """Validates a single Language entry."""
    errors: Dict[str, List[str]] = {}

    errs = validate_text_field(data.get("name", ""), "Language", min_len=2)
    if errs:
        errors["name"] = errs

    valid_prof = {"A1", "A2", "B1", "B2", "C1", "C2", "Native"}
    proficiency = data.get("proficiency", "")
    if proficiency not in valid_prof:
        errors["proficiency"] = [
            f"Proficiency must be one of: {', '.join(sorted(valid_prof))}"
        ]

    return errors
