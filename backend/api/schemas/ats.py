"""Pydantic schemas for /ats routes."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ATSAnalyseRequest(BaseModel):
    cv_id: str
    job_description: str = Field(min_length=20, max_length=10_000)


class ATSRecommendationSchema(BaseModel):
    priority: str
    category: str
    message: str
    impact_score: float


class ATSScoreResponse(BaseModel):
    overall_score: float
    keyword_match_rate: float
    completeness_score: float
    format_score: float
    grade: str
    matched_keywords: List[str]
    missing_keywords: List[str]
    recommendations: List[ATSRecommendationSchema]
    tier_used: str
    advanced_analytics: Optional[Dict[str, Any]] = None

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "ATSScoreResponse":
        recs = [
            ATSRecommendationSchema(**r)
            for r in d.get("recommendations", [])
        ]
        return cls(
            overall_score=d["overall_score"],
            keyword_match_rate=d["keyword_match_rate"],
            completeness_score=d["completeness_score"],
            format_score=d["format_score"],
            grade=d["grade"],
            matched_keywords=d.get("matched_keywords", []),
            missing_keywords=d.get("missing_keywords", []),
            recommendations=recs,
            tier_used=d["tier_used"],
            advanced_analytics=d.get("advanced_analytics"),
        )
