"""Pydantic schemas for /cv routes."""
from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


# ── Sub-schemas mirroring app/models/cv_model.py dataclasses ─────────────────

class PersonalInfoSchema(BaseModel):
    full_name: str = Field(min_length=2, max_length=120)
    email: str
    mobile: str
    location: str
    linkedin: Optional[str] = None
    website: Optional[str] = None
    summary: Optional[str] = None


class WorkExperienceSchema(BaseModel):
    company: str = Field(min_length=2)
    position: str = Field(min_length=2)
    start_date: str  # YYYY-MM-DD
    description: str = Field(min_length=10)
    end_date: Optional[str] = None
    is_current: bool = False
    achievements: List[str] = []


class EducationSchema(BaseModel):
    institution: str = Field(min_length=2)
    degree: str = Field(min_length=2)
    field_of_study: str = Field(min_length=2)
    start_date: str  # YYYY-MM-DD
    end_date: Optional[str] = None
    is_current: bool = False
    grade: Optional[str] = None


class SkillSchema(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    level: Literal["Beginner", "Intermediate", "Advanced", "Expert"]
    category: Optional[str] = None


class LanguageSchema(BaseModel):
    name: str = Field(min_length=2, max_length=60)
    proficiency: Literal["A1", "A2", "B1", "B2", "C1", "C2", "Native"]


class CertificationSchema(BaseModel):
    name: str = Field(min_length=2)
    issuer: str = Field(min_length=2)
    issue_date: str  # YYYY-MM-DD
    credential_id: Optional[str] = None
    expiry_date: Optional[str] = None
    url: Optional[str] = None


class CoachNoteSchema(BaseModel):
    cv_id: str
    note_id: str
    note_text: str
    coach_id: str
    created_at: str


# ── Request bodies ────────────────────────────────────────────────────────────

class CVCreateRequest(BaseModel):
    title: str = Field(default="My CV", min_length=1, max_length=120)
    personal_info: PersonalInfoSchema
    work_experience: List[WorkExperienceSchema] = []
    education: List[EducationSchema] = []
    skills: List[SkillSchema] = []
    languages: List[LanguageSchema] = []
    certifications: List[CertificationSchema] = []


class CVUpdateRequest(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=120)
    personal_info: Optional[PersonalInfoSchema] = None
    work_experience: Optional[List[WorkExperienceSchema]] = None
    education: Optional[List[EducationSchema]] = None
    skills: Optional[List[SkillSchema]] = None
    languages: Optional[List[LanguageSchema]] = None
    certifications: Optional[List[CertificationSchema]] = None


class AddCoachNoteRequest(BaseModel):
    note_text: str = Field(min_length=10, max_length=2000)


class SubmitToCoachRequest(BaseModel):
    coach_id: str = ""


class ExportRequest(BaseModel):
    format: Literal["pdf", "docx", "json", "xml"] = "pdf"


# ── Response ──────────────────────────────────────────────────────────────────

class CVResponse(BaseModel):
    cv_id: str
    user_id: str
    title: str
    version: int
    tier: str
    is_deleted: bool
    created_at: Optional[str]
    updated_at: Optional[str]
    personal_info: Dict[str, Any]
    work_experience: List[Dict[str, Any]] = []
    education: List[Dict[str, Any]] = []
    skills: List[Dict[str, Any]] = []
    languages: List[Dict[str, Any]] = []
    certifications: List[Dict[str, Any]] = []
    assigned_coach_id: Optional[str] = None
    ats_score: Optional[Dict[str, Any]] = None

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "CVResponse":
        return cls(
            cv_id=d["cv_id"],
            user_id=d["user_id"],
            title=d.get("title", "My CV"),
            version=d.get("version", 1),
            tier=d.get("tier", "Free"),
            is_deleted=d.get("is_deleted", False),
            created_at=d.get("created_at"),
            updated_at=d.get("updated_at"),
            personal_info=d.get("personal_info", {}),
            work_experience=d.get("work_experience", []),
            education=d.get("education", []),
            skills=d.get("skills", []),
            languages=d.get("languages", []),
            certifications=d.get("certifications", []),
            assigned_coach_id=d.get("assigned_coach_id"),
            ats_score=d.get("ats_score"),
        )
