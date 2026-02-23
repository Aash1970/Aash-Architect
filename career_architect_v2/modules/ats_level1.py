from __future__ import annotations
import re
import streamlit as st
from db.cv_store import load_cv
from db.client import get_client

# ── Stopwords (lightweight, no NLTK dependency) ───────────────
_STOPWORDS = {
    "a","an","the","and","or","but","in","on","at","to","for","of","with",
    "by","from","is","are","was","were","be","been","being","have","has",
    "had","do","does","did","will","would","could","should","may","might",
    "shall","can","need","dare","ought","used","this","that","these","those",
    "i","me","my","we","our","you","your","he","him","his","she","her","they",
    "them","their","it","its","who","which","what","how","when","where","why",
    "not","no","nor","so","yet","both","either","neither","as","if","then",
    "than","too","very","just","also","more","most","other","some","such",
    "any","all","each","every","few","many","much","own","same","than","very",
}


# ── Text helpers ──────────────────────────────────────────────

def _cv_to_text(cv: dict) -> str:
    parts: list[str] = []
    p = cv.get("personal", {})
    parts += [p.get("full_name", ""), p.get("location", ""), p.get("linkedin", "")]
    parts.append(cv.get("profile_summary", ""))
    parts += cv.get("skills", [])
    for exp in cv.get("experience", []):
        parts += [exp.get("company", ""), exp.get("role", ""),
                  exp.get("description", "")] + exp.get("achievements", [])
    for edu in cv.get("education", []):
        parts += [edu.get("institution", ""), edu.get("qualification", ""),
                  edu.get("subject", "")]
    for cert in cv.get("certifications", []):
        parts.append(cert.get("name", ""))
    parts += cv.get("languages", [])
    return " ".join(str(s) for s in parts if s)


def _extract_keywords(text: str) -> list[str]:
    tokens = re.findall(r"[a-z][a-z0-9+#.\-]*", text.lower())
    return [t for t in tokens if t not in _STOPWORDS and len(t) > 2]


# ── Scoring engine ────────────────────────────────────────────

def score_cv_l1(cv: dict, job_description: str, job_title: str = "") -> dict:
    cv_text  = _cv_to_text(cv).lower()
    jd_kws   = list(dict.fromkeys(_extract_keywords(job_description)))  # preserve order, unique

    if not jd_kws:
        return {"error": "Job description produced no usable keywords."}

    matched  = [kw for kw in jd_kws if kw in cv_text]
    kw_score = len(matched) / len(jd_kws) * 100

    # Section completeness
    sections = {
        "Personal Details": bool(cv.get("personal", {}).get("full_name")),
        "Profile Summary":  bool(cv.get("profile_summary", "").strip()),
        "Skills":           len(cv.get("skills", [])) > 0,
        "Experience":       len(cv.get("experience", [])) > 0,
        "Education":        len(cv.get("education", [])) > 0,
    }
    section_score = sum(sections.values()) / len(sections) * 100

    # Contact completeness
    p = cv.get("personal", {})
    contact_fields = {"Full Name": "full_name", "Email": "email",
                      "Phone": "phone", "Location": "location"}
    contact_status = {k: bool(p.get(v)) for k, v in contact_fields.items()}
    contact_score  = sum(contact_status.values()) / len(contact_status) * 100

    # Skills breadth
    skills_count = len(cv.get("skills", []))
    skills_score = min(skills_count / 15, 1.0) * 100

    total = (
        kw_score      * 0.40 +
        section_score * 0.30 +
        contact_score * 0.15 +
        skills_score  * 0.15
    )

    return {
        "total":               round(total, 1),
        "keyword_coverage":    round(kw_score, 1),
        "section_completeness":round(section_score, 1),
        "contact_completeness":round(contact_score, 1),
        "skills_score":        round(skills_score, 1),
        "matched_keywords":    matched,
        "missing_keywords":    [kw for kw in jd_kws if kw not in cv_text][:20],
        "total_jd_keywords":   len(jd_kws),
        "sections_status":     sections,
        "contact_status":      contact_status,
        "skills_count":        skills_count,
    }


def _save_result(user_id: str, job_title: str, result: dict) -> None:
    try:
        get_client().table("ats_results").insert({
            "user_id":   user_id,
            "level":     1,
            "job_title": job_title,
            "score":     result["total"],
            "breakdown": result,
        }).execute()
    except Exception:
        pass


# ── Score display ─────────────────────────────────────────────

def _score_colour(score: float) -> str:
    if score >= 75:
        return "#22c55e"
    if score >= 50:
        return "#f59e0b"
    return "#ef4444"


def _render_score_bar(label: str, score: float) -> None:
    colour = _score_colour(score)
    st.markdown(
        f"""
        <div style="margin-bottom:8px;">
          <div style="display:flex;justify-content:space-between;font-size:0.85em;">
            <span>{label}</span><span style="color:{colour};font-weight:700;">{score}%</span>
          </div>
          <div style="background:#E2E8F0;border-radius:4px;height:8px;">
            <div style="background:{colour};width:{score}%;height:8px;border-radius:4px;"></div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ── Main render ───────────────────────────────────────────────

def render_ats_level1(user_id: str, flags: dict) -> None:
    st.header("ATS Scoring — Level 1: Keyword Analysis")
    st.caption("Measures how well your CV's vocabulary matches the job description.")

    cv, msg = load_cv(user_id)
    if not cv:
        st.warning("No CV found. Please build and save your CV first.")
        return

    with st.form("ats1_form"):
        job_title = st.text_input("Job Title", placeholder="e.g. Senior Project Manager")
        job_desc  = st.text_area(
            "Paste the full Job Description",
            height=220,
            placeholder="Paste the complete job posting here…",
        )
        submitted = st.form_submit_button("Analyse CV", type="primary")

    if not submitted:
        return

    if not job_desc.strip():
        st.error("Please paste a job description.")
        return

    with st.spinner("Analysing…"):
        result = score_cv_l1(cv, job_desc, job_title)

    if "error" in result:
        st.error(result["error"])
        return

    _save_result(user_id, job_title, result)

    score = result["total"]
    colour = _score_colour(score)

    st.markdown(
        f'<h2 style="color:{colour};text-align:center;margin-top:12px;">'
        f'ATS Score: {score} / 100</h2>',
        unsafe_allow_html=True,
    )

    if score >= 75:
        st.success("Strong match — your CV is well-optimised for this role.")
    elif score >= 50:
        st.warning("Moderate match — consider adding missing keywords.")
    else:
        st.error("Low match — significant keyword gaps detected.")

    st.divider()

    col_l, col_r = st.columns(2)
    with col_l:
        st.subheader("Score Breakdown")
        _render_score_bar("Keyword Coverage",     result["keyword_coverage"])
        _render_score_bar("Section Completeness", result["section_completeness"])
        _render_score_bar("Contact Completeness", result["contact_completeness"])
        _render_score_bar("Skills Breadth",       result["skills_score"])

    with col_r:
        st.subheader("Section Status")
        for section, present in result["sections_status"].items():
            icon = "✅" if present else "❌"
            st.markdown(f"{icon} **{section}**")

        st.subheader("Contact Fields")
        for field, present in result["contact_status"].items():
            icon = "✅" if present else "❌"
            st.markdown(f"{icon} {field}")

    st.divider()

    col_m, col_mi = st.columns(2)
    with col_m:
        st.subheader(f"Matched Keywords ({len(result['matched_keywords'])} / {result['total_jd_keywords']})")
        if result["matched_keywords"]:
            st.markdown(
                " ".join(
                    f'<span style="background:#DCFCE7;color:#166534;padding:2px 7px;'
                    f'border-radius:12px;font-size:0.8em;margin:2px;display:inline-block;">{kw}</span>'
                    for kw in result["matched_keywords"]
                ),
                unsafe_allow_html=True,
            )
    with col_mi:
        st.subheader(f"Missing Keywords (top {len(result['missing_keywords'])})")
        if result["missing_keywords"]:
            st.markdown(
                " ".join(
                    f'<span style="background:#FEE2E2;color:#991B1B;padding:2px 7px;'
                    f'border-radius:12px;font-size:0.8em;margin:2px;display:inline-block;">{kw}</span>'
                    for kw in result["missing_keywords"]
                ),
                unsafe_allow_html=True,
            )
        else:
            st.success("No significant missing keywords.")
