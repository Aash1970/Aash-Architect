"""
User Data Models — Production Grade
Pure Python, no UI dependencies.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List


@dataclass
class UserProfile:
    """Extended profile stored alongside auth record."""
    user_id: str
    email: str
    full_name: str
    role: str  # User | Coach | Admin | SystemAdmin
    tier: str  # Free | Premium | Enterprise
    language: str = "en"
    is_active: bool = True
    is_deleted: bool = False
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    assigned_coach_id: Optional[str] = None  # for User role
    assigned_user_ids: List[str] = field(default_factory=list)  # for Coach role

    def to_dict(self) -> Dict[str, Any]:
        return {
            "user_id": self.user_id,
            "email": self.email,
            "full_name": self.full_name,
            "role": self.role,
            "tier": self.tier,
            "language": self.language,
            "is_active": self.is_active,
            "is_deleted": self.is_deleted,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "assigned_coach_id": self.assigned_coach_id,
            "assigned_user_ids": self.assigned_user_ids,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UserProfile":
        return cls(
            user_id=data.get("user_id", ""),
            email=data.get("email", ""),
            full_name=data.get("full_name", ""),
            role=data.get("role", "User"),
            tier=data.get("tier", "Free"),
            language=data.get("language", "en"),
            is_active=data.get("is_active", True),
            is_deleted=data.get("is_deleted", False),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
            assigned_coach_id=data.get("assigned_coach_id"),
            assigned_user_ids=data.get("assigned_user_ids", []),
        )


@dataclass
class UserModel:
    """
    Auth + Profile combined model for service layer operations.
    Never exposes passwords. Only carries session-safe data.
    """
    user_id: str
    email: str
    role: str
    tier: str
    full_name: str
    language: str = "en"
    is_active: bool = True
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None

    VALID_ROLES = {"User", "Coach", "Admin", "SystemAdmin"}
    VALID_TIERS = {"Free", "Premium", "Enterprise"}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "user_id": self.user_id,
            "email": self.email,
            "role": self.role,
            "tier": self.tier,
            "full_name": self.full_name,
            "language": self.language,
            "is_active": self.is_active,
        }

    @classmethod
    def from_profile(cls, profile: UserProfile, access_token: Optional[str] = None) -> "UserModel":
        return cls(
            user_id=profile.user_id,
            email=profile.email,
            role=profile.role,
            tier=profile.tier,
            full_name=profile.full_name,
            language=profile.language,
            is_active=profile.is_active,
            access_token=access_token,
        )
