"""
CV Data Models — Production Grade
All models are pure Python dataclasses, independent of UI framework.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import date, datetime


@dataclass
class PersonalInfo:
    full_name: str
    email: str
    mobile: str
    location: str
    linkedin: Optional[str] = None
    website: Optional[str] = None
    summary: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "full_name": self.full_name,
            "email": self.email,
            "mobile": self.mobile,
            "location": self.location,
            "linkedin": self.linkedin,
            "website": self.website,
            "summary": self.summary,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PersonalInfo":
        return cls(
            full_name=data.get("full_name", ""),
            email=data.get("email", ""),
            mobile=data.get("mobile", ""),
            location=data.get("location", ""),
            linkedin=data.get("linkedin"),
            website=data.get("website"),
            summary=data.get("summary"),
        )


@dataclass
class WorkExperience:
    company: str
    position: str
    start_date: str  # ISO date string YYYY-MM-DD
    description: str
    end_date: Optional[str] = None
    is_current: bool = False
    achievements: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "company": self.company,
            "position": self.position,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "is_current": self.is_current,
            "description": self.description,
            "achievements": self.achievements,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WorkExperience":
        return cls(
            company=data.get("company", ""),
            position=data.get("position", ""),
            start_date=data.get("start_date", ""),
            end_date=data.get("end_date"),
            is_current=data.get("is_current", False),
            description=data.get("description", ""),
            achievements=data.get("achievements", []),
        )


@dataclass
class Education:
    institution: str
    degree: str
    field_of_study: str
    start_date: str  # ISO date string YYYY-MM-DD
    end_date: Optional[str] = None
    is_current: bool = False
    grade: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "institution": self.institution,
            "degree": self.degree,
            "field_of_study": self.field_of_study,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "is_current": self.is_current,
            "grade": self.grade,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Education":
        return cls(
            institution=data.get("institution", ""),
            degree=data.get("degree", ""),
            field_of_study=data.get("field_of_study", ""),
            start_date=data.get("start_date", ""),
            end_date=data.get("end_date"),
            is_current=data.get("is_current", False),
            grade=data.get("grade"),
        )


@dataclass
class Skill:
    name: str
    level: str  # Beginner | Intermediate | Advanced | Expert
    category: Optional[str] = None

    VALID_LEVELS = {"Beginner", "Intermediate", "Advanced", "Expert"}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "level": self.level,
            "category": self.category,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Skill":
        return cls(
            name=data.get("name", ""),
            level=data.get("level", "Beginner"),
            category=data.get("category"),
        )


@dataclass
class Language:
    name: str
    proficiency: str  # A1 | A2 | B1 | B2 | C1 | C2 | Native

    VALID_PROFICIENCY = {"A1", "A2", "B1", "B2", "C1", "C2", "Native"}

    def to_dict(self) -> Dict[str, Any]:
        return {"name": self.name, "proficiency": self.proficiency}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Language":
        return cls(
            name=data.get("name", ""),
            proficiency=data.get("proficiency", "B1"),
        )


@dataclass
class Certification:
    name: str
    issuer: str
    issue_date: str  # ISO date string YYYY-MM-DD
    credential_id: Optional[str] = None
    expiry_date: Optional[str] = None
    url: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "issuer": self.issuer,
            "issue_date": self.issue_date,
            "credential_id": self.credential_id,
            "expiry_date": self.expiry_date,
            "url": self.url,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Certification":
        return cls(
            name=data.get("name", ""),
            issuer=data.get("issuer", ""),
            issue_date=data.get("issue_date", ""),
            credential_id=data.get("credential_id"),
            expiry_date=data.get("expiry_date"),
            url=data.get("url"),
        )


@dataclass
class CVSummary:
    """Lightweight summary for listing/browsing CVs."""
    cv_id: str
    user_id: str
    title: str
    version: int
    created_at: str
    updated_at: str
    is_deleted: bool
    tier: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "cv_id": self.cv_id,
            "user_id": self.user_id,
            "title": self.title,
            "version": self.version,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "is_deleted": self.is_deleted,
            "tier": self.tier,
        }


@dataclass
class CVModel:
    """
    Full CV model. This is the canonical data structure for a CV.
    All services operate on this model or its dict representation.
    No Streamlit dependencies. Portable to FastAPI / any backend.
    """
    user_id: str
    personal_info: PersonalInfo
    version: int = 1
    cv_id: Optional[str] = None
    title: str = "My CV"
    tier: str = "Free"
    is_deleted: bool = False
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    work_experience: List[WorkExperience] = field(default_factory=list)
    education: List[Education] = field(default_factory=list)
    skills: List[Skill] = field(default_factory=list)
    languages: List[Language] = field(default_factory=list)
    certifications: List[Certification] = field(default_factory=list)
    coach_notes: Optional[str] = None
    assigned_coach_id: Optional[str] = None
    ats_score: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "cv_id": self.cv_id,
            "user_id": self.user_id,
            "title": self.title,
            "version": self.version,
            "tier": self.tier,
            "is_deleted": self.is_deleted,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "personal_info": self.personal_info.to_dict(),
            "work_experience": [w.to_dict() for w in self.work_experience],
            "education": [e.to_dict() for e in self.education],
            "skills": [s.to_dict() for s in self.skills],
            "languages": [l.to_dict() for l in self.languages],
            "certifications": [c.to_dict() for c in self.certifications],
            "coach_notes": self.coach_notes,
            "assigned_coach_id": self.assigned_coach_id,
            "ats_score": self.ats_score,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CVModel":
        return cls(
            cv_id=data.get("cv_id"),
            user_id=data.get("user_id", ""),
            title=data.get("title", "My CV"),
            version=data.get("version", 1),
            tier=data.get("tier", "Free"),
            is_deleted=data.get("is_deleted", False),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
            personal_info=PersonalInfo.from_dict(
                data.get("personal_info", {})
            ),
            work_experience=[
                WorkExperience.from_dict(w)
                for w in data.get("work_experience", [])
            ],
            education=[
                Education.from_dict(e)
                for e in data.get("education", [])
            ],
            skills=[
                Skill.from_dict(s) for s in data.get("skills", [])
            ],
            languages=[
                Language.from_dict(l) for l in data.get("languages", [])
            ],
            certifications=[
                Certification.from_dict(c)
                for c in data.get("certifications", [])
            ],
            coach_notes=data.get("coach_notes"),
            assigned_coach_id=data.get("assigned_coach_id"),
            ats_score=data.get("ats_score"),
        )

    def is_complete(self) -> bool:
        """Returns True if CV has minimum required data."""
        pi = self.personal_info
        return bool(
            pi.full_name and len(pi.full_name) > 1
            and pi.email and len(pi.email) > 3
            and pi.mobile and len(pi.mobile) > 5
            and pi.location and len(pi.location) > 1
        )

    def get_text_content(self) -> str:
        """Returns all CV text content for ATS analysis."""
        parts = [
            self.personal_info.full_name,
            self.personal_info.summary or "",
        ]
        for w in self.work_experience:
            parts.extend([w.position, w.company, w.description])
            parts.extend(w.achievements)
        for e in self.education:
            parts.extend([e.degree, e.field_of_study, e.institution])
        for s in self.skills:
            parts.append(s.name)
        for c in self.certifications:
            parts.extend([c.name, c.issuer])
        return " ".join(filter(None, parts)).lower()
