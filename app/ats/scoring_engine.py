"""
ATS Scoring Engine — Production Grade
Independent module. NO Streamlit imports. NO UI dependencies.
Accepts CV JSON and job description text.
Returns structured score object.
Integrates with tier system for feature gating.

Scoring algorithm:
  - Keyword extraction from job description (NLP-lite, no external deps)
  - Keyword matching against CV full text
  - Section completeness scoring
  - Format quality heuristics
  - Weighted composite score
"""

from __future__ import annotations

import re
import math
from dataclasses import dataclass, field
from typing import Dict, List, Set, Tuple, Any, Optional


# ── Stop words (English, minimal set for keyword extraction) ─────────────────
_STOP_WORDS: Set[str] = {
    "a", "an", "the", "and", "or", "but", "in", "on", "at", "to",
    "for", "of", "with", "by", "from", "as", "is", "was", "are",
    "were", "be", "been", "being", "have", "has", "had", "do", "does",
    "did", "will", "would", "could", "should", "may", "might", "must",
    "shall", "can", "need", "dare", "ought", "used", "this", "that",
    "these", "those", "i", "you", "he", "she", "it", "we", "they",
    "me", "him", "her", "us", "them", "my", "your", "his", "its",
    "our", "their", "what", "which", "who", "when", "where", "why",
    "how", "not", "no", "so", "if", "then", "than", "too", "very",
    "just", "also", "about", "more", "other", "such", "new", "old",
    "up", "out", "over", "into", "after", "before", "through", "both",
    "each", "few", "same", "than", "into", "through", "during",
    "including", "until", "against", "among", "throughout", "despite",
    "however", "therefore", "although", "because", "since", "while",
}

# Minimum keyword length for extraction
_MIN_KEYWORD_LEN = 3


@dataclass
class ATSRecommendation:
    """A single actionable recommendation from the ATS engine."""
    priority: str        # high | medium | low
    category: str        # keywords | format | completeness | section
    message: str
    impact_score: float  # estimated score improvement if applied (0-10)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "priority": self.priority,
            "category": self.category,
            "message": self.message,
            "impact_score": self.impact_score,
        }


@dataclass
class ATSScore:
    """
    Structured ATS score result returned by the engine.
    All fields are serialisable to JSON.
    """
    overall_score: float          # 0 – 100
    keyword_match_rate: float     # 0 – 100 (%)
    completeness_score: float     # 0 – 100
    format_score: float           # 0 – 100
    matched_keywords: List[str]
    missing_keywords: List[str]
    recommendations: List[ATSRecommendation]
    tier_used: str                # Free | Premium | Enterprise
    advanced_analytics: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "overall_score": round(self.overall_score, 1),
            "grade": self.grade,
            "keyword_match_rate": round(self.keyword_match_rate, 1),
            "completeness_score": round(self.completeness_score, 1),
            "format_score": round(self.format_score, 1),
            "matched_keywords": self.matched_keywords,
            "missing_keywords": self.missing_keywords,
            "recommendations": [r.to_dict() for r in self.recommendations],
            "tier_used": self.tier_used,
            "advanced_analytics": self.advanced_analytics,
        }

    @property
    def grade(self) -> str:
        """Letter grade equivalent of the overall score."""
        s = self.overall_score
        if s >= 85:
            return "A"
        if s >= 70:
            return "B"
        if s >= 55:
            return "C"
        if s >= 40:
            return "D"
        return "F"


class ATSEngine:
    """
    Applicant Tracking System scoring engine.

    Usage:
        engine = ATSEngine()
        score = engine.score(cv_dict, job_description, tier="Premium")
        print(score.overall_score)
    """

    # Section weights for completeness scoring
    _SECTION_WEIGHTS: Dict[str, float] = {
        "personal_info": 0.25,
        "work_experience": 0.30,
        "education": 0.20,
        "skills": 0.15,
        "languages": 0.05,
        "certifications": 0.05,
    }

    # ATS scoring weights
    _SCORE_WEIGHTS: Dict[str, float] = {
        "keyword_match": 0.55,
        "completeness": 0.30,
        "format": 0.15,
    }

    def score(
        self,
        cv_dict: Dict[str, Any],
        job_description: str,
        tier: str = "Free",
    ) -> ATSScore:
        """
        Score a CV against a job description.

        Args:
            cv_dict:         CV as a dictionary (from CVModel.to_dict())
            job_description: Raw job description text
            tier:            User's tier ('Free' | 'Premium' | 'Enterprise')

        Returns:
            ATSScore with full breakdown.
        """
        if not job_description or not job_description.strip():
            raise ValueError("Job description must not be empty.")
        if not cv_dict:
            raise ValueError("CV data must not be empty.")

        # Extract keywords from job description
        jd_keywords = self._extract_keywords(job_description)

        # Extract full text from CV
        cv_text = self._extract_cv_text(cv_dict)
        cv_words = set(self._tokenize(cv_text))

        # Keyword matching
        matched, missing = self._match_keywords(jd_keywords, cv_words)
        keyword_match_rate = (
            (len(matched) / len(jd_keywords) * 100)
            if jd_keywords else 0.0
        )

        # Section completeness
        completeness_score = self._score_completeness(cv_dict)

        # Format quality
        format_score = self._score_format(cv_dict)

        # Composite score
        overall_score = (
            keyword_match_rate * self._SCORE_WEIGHTS["keyword_match"]
            + completeness_score * self._SCORE_WEIGHTS["completeness"]
            + format_score * self._SCORE_WEIGHTS["format"]
        )

        # Recommendations
        recommendations = self._generate_recommendations(
            cv_dict, matched, missing, completeness_score, format_score
        )

        # Advanced analytics (Enterprise only)
        advanced_analytics = None
        if tier == "Enterprise":
            advanced_analytics = self._advanced_analytics(
                cv_dict, jd_keywords, matched, missing, job_description
            )

        return ATSScore(
            overall_score=min(overall_score, 100.0),
            keyword_match_rate=keyword_match_rate,
            completeness_score=completeness_score,
            format_score=format_score,
            matched_keywords=sorted(matched),
            missing_keywords=sorted(missing),
            recommendations=sorted(
                recommendations, key=lambda r: r.impact_score, reverse=True
            ),
            tier_used=tier,
            advanced_analytics=advanced_analytics,
        )

    # ── Private helpers ──────────────────────────────────────────────────────

    def _tokenize(self, text: str) -> List[str]:
        """Tokenise text to lowercase alphabetic tokens."""
        tokens = re.findall(r"[a-zA-Z]+", text.lower())
        return tokens

    def _extract_keywords(self, text: str) -> Set[str]:
        """
        Extracts meaningful keywords from text.
        Filters stop words and short tokens.
        Also extracts common bigrams (2-word phrases).
        """
        tokens = self._tokenize(text)
        keywords: Set[str] = set()

        for token in tokens:
            if len(token) >= _MIN_KEYWORD_LEN and token not in _STOP_WORDS:
                keywords.add(token)

        # Extract bigrams for multi-word technical terms
        words = [t for t in tokens if t not in _STOP_WORDS and len(t) >= 2]
        for i in range(len(words) - 1):
            bigram = f"{words[i]} {words[i+1]}"
            if len(bigram) > 5:
                keywords.add(bigram)

        return keywords

    def _extract_cv_text(self, cv_dict: Dict[str, Any]) -> str:
        """Extracts all searchable text from a CV dictionary."""
        parts: List[str] = []

        # Personal info
        pi = cv_dict.get("personal_info", {})
        parts.extend([
            pi.get("full_name", ""),
            pi.get("summary", "") or "",
        ])

        # Work experience
        for w in cv_dict.get("work_experience", []):
            parts.extend([
                w.get("position", ""),
                w.get("company", ""),
                w.get("description", ""),
            ])
            parts.extend(w.get("achievements", []))

        # Education
        for e in cv_dict.get("education", []):
            parts.extend([
                e.get("degree", ""),
                e.get("field_of_study", ""),
                e.get("institution", ""),
            ])

        # Skills
        for s in cv_dict.get("skills", []):
            parts.append(s.get("name", ""))

        # Certifications
        for c in cv_dict.get("certifications", []):
            parts.extend([c.get("name", ""), c.get("issuer", "")])

        return " ".join(filter(None, parts)).lower()

    def _match_keywords(
        self, jd_keywords: Set[str], cv_words: Set[str]
    ) -> Tuple[List[str], List[str]]:
        """
        Match JD keywords against CV word set.
        Handles both single words and bigrams.
        """
        cv_text_full = " ".join(cv_words)
        matched: List[str] = []
        missing: List[str] = []

        for kw in jd_keywords:
            if " " in kw:
                # Bigram — check if phrase appears in full text
                if kw in cv_text_full:
                    matched.append(kw)
                else:
                    missing.append(kw)
            else:
                if kw in cv_words:
                    matched.append(kw)
                else:
                    missing.append(kw)

        # Return top 30 of each to keep result manageable
        return matched[:30], missing[:30]

    def _score_completeness(self, cv_dict: Dict[str, Any]) -> float:
        """
        Scores CV section completeness.
        Returns 0–100.
        """
        total = 0.0

        # Personal info
        pi = cv_dict.get("personal_info", {})
        pi_fields = ["full_name", "email", "mobile", "location", "summary"]
        pi_filled = sum(1 for f in pi_fields if pi.get(f))
        pi_score = (pi_filled / len(pi_fields)) * 100
        total += pi_score * self._SECTION_WEIGHTS["personal_info"]

        # Work experience
        work = cv_dict.get("work_experience", [])
        work_score = min(len(work) * 33.3, 100.0)
        total += work_score * self._SECTION_WEIGHTS["work_experience"]

        # Education
        edu = cv_dict.get("education", [])
        edu_score = min(len(edu) * 50.0, 100.0)
        total += edu_score * self._SECTION_WEIGHTS["education"]

        # Skills
        skills = cv_dict.get("skills", [])
        skills_score = min(len(skills) * 20.0, 100.0)
        total += skills_score * self._SECTION_WEIGHTS["skills"]

        # Languages
        langs = cv_dict.get("languages", [])
        langs_score = min(len(langs) * 50.0, 100.0)
        total += langs_score * self._SECTION_WEIGHTS["languages"]

        # Certifications
        certs = cv_dict.get("certifications", [])
        certs_score = min(len(certs) * 33.3, 100.0)
        total += certs_score * self._SECTION_WEIGHTS["certifications"]

        return round(total, 1)

    def _score_format(self, cv_dict: Dict[str, Any]) -> float:
        """
        Heuristic format quality score.
        Returns 0–100.
        """
        score = 0.0

        # Has LinkedIn
        pi = cv_dict.get("personal_info", {})
        if pi.get("linkedin"):
            score += 10

        # Summary exists and is substantial
        summary = pi.get("summary", "") or ""
        if len(summary) >= 100:
            score += 20
        elif len(summary) >= 50:
            score += 10

        # Work experience has descriptions
        work = cv_dict.get("work_experience", [])
        if work:
            described = sum(1 for w in work if len(w.get("description", "")) > 50)
            score += (described / len(work)) * 30

        # Work experience has achievements
        with_achievements = sum(
            1 for w in work if len(w.get("achievements", [])) > 0
        )
        if work:
            score += (with_achievements / len(work)) * 20

        # Skills have levels
        skills = cv_dict.get("skills", [])
        if skills:
            with_levels = sum(1 for s in skills if s.get("level"))
            score += (with_levels / len(skills)) * 20

        return min(round(score, 1), 100.0)

    def _generate_recommendations(
        self,
        cv_dict: Dict[str, Any],
        matched: List[str],
        missing: List[str],
        completeness_score: float,
        format_score: float,
    ) -> List[ATSRecommendation]:
        """Generates actionable recommendations based on scoring."""
        recs: List[ATSRecommendation] = []
        pi = cv_dict.get("personal_info", {})

        # Keyword gaps
        if len(missing) > 10:
            recs.append(ATSRecommendation(
                priority="high",
                category="keywords",
                message=(
                    f"Your CV is missing {len(missing)} important keywords from the "
                    "job description. Add these to your skills, experience, or summary: "
                    + ", ".join(missing[:8]) + ("..." if len(missing) > 8 else ".")
                ),
                impact_score=8.5,
            ))
        elif len(missing) > 5:
            recs.append(ATSRecommendation(
                priority="medium",
                category="keywords",
                message=(
                    f"Consider adding these {len(missing)} missing keywords: "
                    + ", ".join(missing[:5]) + "."
                ),
                impact_score=5.0,
            ))

        # Professional summary
        summary = pi.get("summary", "") or ""
        if not summary:
            recs.append(ATSRecommendation(
                priority="high",
                category="completeness",
                message=(
                    "Add a Professional Summary. ATS systems heavily weight this section. "
                    "Aim for 3–5 sentences including your top skills and career goals."
                ),
                impact_score=7.0,
            ))
        elif len(summary) < 100:
            recs.append(ATSRecommendation(
                priority="medium",
                category="completeness",
                message=(
                    "Expand your Professional Summary. It's currently too short. "
                    "Aim for at least 100 characters incorporating job-relevant keywords."
                ),
                impact_score=4.0,
            ))

        # Work experience descriptions
        work = cv_dict.get("work_experience", [])
        if not work:
            recs.append(ATSRecommendation(
                priority="high",
                category="completeness",
                message="Add work experience entries. This is the most heavily weighted CV section.",
                impact_score=9.0,
            ))
        else:
            short_descs = [
                w for w in work if len(w.get("description", "")) < 50
            ]
            if short_descs:
                recs.append(ATSRecommendation(
                    priority="medium",
                    category="format",
                    message=(
                        f"{len(short_descs)} work experience entries have short descriptions. "
                        "Expand each to at least 2–3 sentences with measurable achievements."
                    ),
                    impact_score=5.5,
                ))

        # Skills count
        skills = cv_dict.get("skills", [])
        if len(skills) < 5:
            recs.append(ATSRecommendation(
                priority="medium",
                category="keywords",
                message=(
                    "Add more skills — you currently have fewer than 5. "
                    "ATS systems scan skills sections for keyword matches. "
                    "Aim for 8–15 relevant skills."
                ),
                impact_score=4.5,
            ))

        # LinkedIn profile
        if not pi.get("linkedin"):
            recs.append(ATSRecommendation(
                priority="low",
                category="format",
                message=(
                    "Add your LinkedIn profile URL. Many recruiters verify profiles, "
                    "and it signals a complete professional presence."
                ),
                impact_score=2.0,
            ))

        # Certifications
        if not cv_dict.get("certifications"):
            recs.append(ATSRecommendation(
                priority="low",
                category="completeness",
                message=(
                    "Add any relevant certifications. Certifications validate skills "
                    "and improve keyword coverage."
                ),
                impact_score=2.5,
            ))

        # Achievements
        no_achievements = [w for w in work if not w.get("achievements")]
        if no_achievements and work:
            recs.append(ATSRecommendation(
                priority="medium",
                category="format",
                message=(
                    "Add quantifiable achievements to your work experience. "
                    "Use numbers and metrics (e.g. 'Increased sales by 25%')."
                ),
                impact_score=4.0,
            ))

        return recs

    def _advanced_analytics(
        self,
        cv_dict: Dict[str, Any],
        jd_keywords: Set[str],
        matched: List[str],
        missing: List[str],
        job_description: str,
    ) -> Dict[str, Any]:
        """
        Enterprise-tier advanced analytics.
        Returns detailed breakdown for reporting dashboards.
        """
        work = cv_dict.get("work_experience", [])
        skills = cv_dict.get("skills", [])

        # Seniority signal from JD
        senior_terms = {"senior", "lead", "principal", "head", "director", "manager", "vp"}
        jd_seniority = any(t in job_description.lower() for t in senior_terms)

        # Experience years estimate
        total_months = 0
        for w in work:
            start = w.get("start_date", "")
            end = w.get("end_date", "")
            if start and len(start) == 10:
                try:
                    sy, sm = int(start[:4]), int(start[5:7])
                    if end and len(end) == 10:
                        ey, em = int(end[:4]), int(end[5:7])
                    else:
                        import datetime
                        now = datetime.date.today()
                        ey, em = now.year, now.month
                    total_months += (ey - sy) * 12 + (em - sm)
                except (ValueError, IndexError):
                    pass

        experience_years = round(total_months / 12, 1)

        # Skill category breakdown
        skill_categories: Dict[str, List[str]] = {}
        for s in skills:
            cat = s.get("category") or "Other"
            skill_categories.setdefault(cat, []).append(s.get("name", ""))

        # Keyword density
        cv_text = self._extract_cv_text(cv_dict)
        cv_word_count = len(cv_text.split())
        keyword_density = (
            (len(matched) / cv_word_count * 100) if cv_word_count > 0 else 0
        )

        return {
            "experience_years": experience_years,
            "jd_requires_seniority": jd_seniority,
            "total_jd_keywords": len(jd_keywords),
            "keyword_density_pct": round(keyword_density, 2),
            "cv_word_count": cv_word_count,
            "skill_categories": skill_categories,
            "match_breakdown": {
                "matched_count": len(matched),
                "missing_count": len(missing),
                "total_jd_keywords": len(jd_keywords),
            },
            "section_scores": {
                "has_summary": bool((cv_dict.get("personal_info") or {}).get("summary")),
                "work_entries": len(work),
                "education_entries": len(cv_dict.get("education", [])),
                "skills_count": len(skills),
                "certifications_count": len(cv_dict.get("certifications", [])),
            },
        }


def score_cv_against_job(
    cv_dict: Dict[str, Any],
    job_description: str,
    tier: str = "Free",
) -> ATSScore:
    """
    Convenience function. Instantiates ATSEngine and scores.

    Args:
        cv_dict:         CV dictionary
        job_description: Job description text
        tier:            User tier

    Returns:
        ATSScore
    """
    engine = ATSEngine()
    return engine.score(cv_dict, job_description, tier)
