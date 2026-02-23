from __future__ import annotations
import re
import streamlit as st
from db.cv_store import load_cv
from db.client import get_client
from modules.ats_level1 import _cv_to_text, _extract_keywords, _score_colour, _render_score_bar

# ── Action verbs list ─────────────────────────────────────────
ACTION_VERBS = [
    "achieved","accelerated","built","championed","consolidated","coordinated",
    "created","cultivated","delivered","designed","developed","directed",
    "drove","established","exceeded","executed","expanded","generated",
    "grew","implemented","improved","increased","initiated","innovated",
    "launched","led","managed","mentored","negotiated","optimised","organised",
    "orchestrated","pioneered","produced","reduced","resolved","secured",
    "spearheaded","streamlined","strengthened","transformed","trained",
    "upgraded","utilised","validated","won",
]

# ── Industry skill terms (broad coverage) ────────────────────
_TECH_TERMS = {
    "python","java","javascript","typescript","react","node","sql","aws",
    "azure","gcp","docker","kubernetes","api","rest","graphql","git","ci/cd",
    "agile","scrum","machine learning","data","analytics","excel","powerbi",
    "tableau","salesforce","jira","confluence","linux","cloud","devops",
}


def _tokenize(text: str) -> set[str]:
    tokens = re.findall(r"[a-z][a-z0-9+#.\-]*", text.lower())
    stopwords = {
        "a","an","the","and","or","but","in","on","at","to","for","of","with",
        "by","from","is","are","was","were","be","been","have","has","had",
        "do","does","did","will","would","could","should","may","might","this",
        "that","these","those","i","we","you","he","she","they","it","not","no",
    }
    return {t for t in tokens if t not in stopwords and len(t) > 2}


def _extract_skill_terms(text: str) -> set[str]:
    found: set[str] = set()
    # Multi-word skill phrases
    for term in _TECH_TERMS:
        if term in text:
            found.add(term)
    return found


def _experience_text(cv: dict) -> str:
    parts: list[str] = []
    for exp in cv.get("experience", []):
        parts += [exp.get("description", "")] + exp.get("achievements", [])
    return " ".join(parts)


# ── Scoring engine ────────────────────────────────────────────

def score_cv_l2(cv: dict, job_description: str, job_title: str = "") -> dict:
    cv_text    = _cv_to_text(cv).lower()
    exp_text   = _experience_text(cv).lower()
    jd_lower   = job_description.lower()

    cv_tokens  = _tokenize(cv_text)
    jd_tokens  = _tokenize(jd_lower)

    # 1. Semantic overlap (Jaccard similarity on meaningful tokens)
    union      = cv_tokens | jd_tokens
    overlap    = cv_tokens & jd_tokens
    semantic   = (len(overlap) / len(union) * 100) if union else 0.0

    # 2. Action verb presence in experience
    verbs_found = [v for v in ACTION_VERBS if v in exp_text]
    verb_score  = min(len(verbs_found) / 8, 1.0) * 100

    # 3. Quantification score (numbers / % in experience)
    quantities  = re.findall(
        r"\b\d+(?:\.\d+)?(?:\s*%|k|m|bn|million|billion|percent|people|clients|users|years?)?\b",
        exp_text,
    )
    quant_score = min(len(quantities) / 5, 1.0) * 100

    # 4. Skills gap
    cv_skills   = {s.lower() for s in cv.get("skills", [])}
    jd_skills   = _extract_skill_terms(jd_lower)
    missing     = jd_skills - cv_skills
    gap_score   = max(0.0, 100.0 - len(missing) * 10)

    # 5. CV length / format
    word_count  = len(cv_text.split())
    if 300 <= word_count <= 900:
        format_score = 100.0
    else:
        format_score = max(0.0, 100.0 - abs(word_count - 600) * 0.15)

    # 6. Profile summary quality
    summary     = cv.get("profile_summary", "")
    sw_count    = len(summary.split())
    summary_sc  = 100.0 if 50 <= sw_count <= 120 else max(0.0, 100.0 - abs(sw_count - 85) * 1.5)

    total = (
        semantic     * 0.30 +
        verb_score   * 0.20 +
        quant_score  * 0.15 +
        gap_score    * 0.15 +
        format_score * 0.10 +
        summary_sc   * 0.10
    )

    # Recommendations
    recs: list[str] = []
    if semantic < 50:
        recs.append("Increase vocabulary overlap with the job description — mirror their exact terminology.")
    if verb_score < 50:
        recs.append("Add strong action verbs to your experience (e.g. delivered, led, optimised).")
    if quant_score < 40:
        recs.append("Quantify achievements — use numbers, percentages, or team sizes.")
    if missing:
        recs.append(f"Add missing skills to your Skills section: {', '.join(sorted(missing)[:6])}.")
    if word_count < 300:
        recs.append("Your CV is short — expand descriptions to 300–900 words for best results.")
    if word_count > 900:
        recs.append("Your CV is lengthy — aim for under 900 words; prioritise relevance.")
    if sw_count < 50:
        recs.append("Your profile summary is too brief — aim for 50–120 words.")

    return {
        "total":            round(total, 1),
        "semantic_match":   round(semantic, 1),
        "action_verb_score":round(verb_score, 1),
        "quantification":   round(quant_score, 1),
        "skills_gap_score": round(gap_score, 1),
        "format_score":     round(format_score, 1),
        "summary_score":    round(summary_sc, 1),
        "missing_skills":   sorted(missing),
        "verbs_found":      verbs_found,
        "verbs_missing":    [v for v in ACTION_VERBS[:20] if v not in verbs_found],
        "word_count":       word_count,
        "quantities_found": len(quantities),
        "recommendations":  recs,
    }


def _save_result(user_id: str, job_title: str, result: dict) -> None:
    try:
        get_client().table("ats_results").insert({
            "user_id":   user_id,
            "level":     2,
            "job_title": job_title,
            "score":     result["total"],
            "breakdown": result,
        }).execute()
    except Exception:
        pass


# ── Main render ───────────────────────────────────────────────

def render_ats_level2(user_id: str, flags: dict) -> None:
    st.header("ATS Scoring — Level 2: Advanced Analysis")
    st.caption("Semantic similarity, action verbs, quantification, skills gap and format quality.")

    cv, msg = load_cv(user_id)
    if not cv:
        st.warning("No CV found. Please build and save your CV first.")
        return

    with st.form("ats2_form"):
        job_title = st.text_input("Job Title", placeholder="e.g. Head of Operations")
        job_desc  = st.text_area(
            "Paste the full Job Description",
            height=220,
            placeholder="Paste the complete job posting here…",
        )
        submitted = st.form_submit_button("Deep Analyse", type="primary")

    if not submitted:
        return

    if not job_desc.strip():
        st.error("Please paste a job description.")
        return

    with st.spinner("Running deep analysis…"):
        result = score_cv_l2(cv, job_desc, job_title)

    _save_result(user_id, job_title, result)

    score  = result["total"]
    colour = _score_colour(score)

    st.markdown(
        f'<h2 style="color:{colour};text-align:center;margin-top:12px;">'
        f'Level 2 Score: {score} / 100</h2>',
        unsafe_allow_html=True,
    )

    if score >= 75:
        st.success("Excellent — your CV demonstrates strong alignment for this role.")
    elif score >= 50:
        st.warning("Good foundation — targeted improvements will significantly raise your score.")
    else:
        st.error("Needs work — follow the recommendations below to improve alignment.")

    st.divider()

    col_l, col_r = st.columns(2)
    with col_l:
        st.subheader("Dimension Scores")
        _render_score_bar("Semantic Match",   result["semantic_match"])
        _render_score_bar("Action Verbs",     result["action_verb_score"])
        _render_score_bar("Quantification",   result["quantification"])
        _render_score_bar("Skills Alignment", result["skills_gap_score"])
        _render_score_bar("Format & Length",  result["format_score"])
        _render_score_bar("Profile Summary",  result["summary_score"])

    with col_r:
        st.subheader("Key Stats")
        st.metric("Word Count",         result["word_count"],      delta="ideal 300–900")
        st.metric("Quantified Items",   result["quantities_found"], delta="aim for 5+")
        st.metric("Action Verbs Found", len(result["verbs_found"]), delta="aim for 8+")

    st.divider()

    if result["missing_skills"]:
        st.subheader("Skills Gap — Add These to Your CV")
        st.markdown(
            " ".join(
                f'<span style="background:#FEE2E2;color:#991B1B;padding:3px 9px;'
                f'border-radius:12px;font-size:0.85em;margin:2px;display:inline-block;">{s}</span>'
                for s in result["missing_skills"]
            ),
            unsafe_allow_html=True,
        )

    if result["verbs_found"]:
        st.subheader("Action Verbs Detected")
        st.markdown(
            " ".join(
                f'<span style="background:#DCFCE7;color:#166534;padding:3px 9px;'
                f'border-radius:12px;font-size:0.85em;margin:2px;display:inline-block;">{v}</span>'
                for v in result["verbs_found"]
            ),
            unsafe_allow_html=True,
        )

    if result["recommendations"]:
        st.divider()
        st.subheader("Personalised Recommendations")
        for i, rec in enumerate(result["recommendations"], 1):
            st.markdown(
                f'<div style="background:#EEF2FF;border-left:4px solid #6366F1;'
                f'padding:10px 14px;margin-bottom:8px;border-radius:4px;">'
                f'<strong>{i}.</strong> {rec}</div>',
                unsafe_allow_html=True,
            )
