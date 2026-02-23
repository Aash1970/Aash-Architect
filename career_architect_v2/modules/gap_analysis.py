from __future__ import annotations
import re
import streamlit as st
from datetime import datetime
from db.cv_store import load_cv

GAP_THRESHOLD_DAYS = 91  # > 3 months constitutes a significant gap

GAP_CATEGORIES = [
    "Career Development",
    "Health & Wellbeing",
    "Family & Care",
    "Bereavement",
    "Redundancy / Restructure",
    "Travel / Sabbatical",
    "Other",
]

_EMPATHY_TEMPLATES: dict[str, dict] = {
    "Career Development": {
        "narrative": (
            "During this period I made a deliberate investment in my professional development. "
            "I focused on building skills that directly strengthen my ability to add value in "
            "roles like this one, and emerged with renewed clarity and capability."
        ),
        "linkedin": (
            "Career break — strategic professional development and skills investment."
        ),
        "aash_says": (
            "Intentional growth is never a gap — it's an upgrade. Owning this period confidently "
            "signals self-awareness and ambition."
        ),
    },
    "Health & Wellbeing": {
        "narrative": (
            "I took time away from work to prioritise my health. I addressed the situation "
            "fully and returned with sustained energy, stronger resilience, and a refreshed "
            "commitment to delivering excellent work."
        ),
        "linkedin": "Career break — personal health and recovery.",
        "aash_says": (
            "Your health is your most important professional asset. Returning from a health "
            "challenge shows real strength — frame it that way."
        ),
    },
    "Family & Care": {
        "narrative": (
            "I stepped back from full-time employment to provide care for a family member. "
            "This experience sharpened my capacity for empathy, logistics management, and "
            "decision-making under pressure — skills I now bring directly to my work."
        ),
        "linkedin": "Career break — full-time family care responsibilities.",
        "aash_says": (
            "Caregiving is unpaid leadership. The skills you built — coordination, patience, "
            "advocating for others — are genuinely transferable. Don't undersell them."
        ),
    },
    "Bereavement": {
        "narrative": (
            "I took time to grieve and stabilise following a significant personal loss. "
            "I am now fully re-engaged and bring with me a depth of perspective that "
            "makes me a more considered and empathetic colleague."
        ),
        "linkedin": "Career break — personal bereavement and recovery period.",
        "aash_says": (
            "You don't owe anyone a full explanation. A brief, dignified statement is enough. "
            "Returning to work after loss is a quiet act of courage."
        ),
    },
    "Redundancy / Restructure": {
        "narrative": (
            "My role was made redundant as part of a company-wide restructure. I used the "
            "transition period productively — reflecting on my direction, upskilling, and "
            "pursuing roles where my expertise creates the most value."
        ),
        "linkedin": "Career break — following company restructure; active job search and development.",
        "aash_says": (
            "Redundancy happens to the best people at the best companies. Be direct, be "
            "confident, and focus on what you did during the gap — not how it started."
        ),
    },
    "Travel / Sabbatical": {
        "narrative": (
            "I took an intentional career break to travel and broaden my perspective. "
            "This period gave me cross-cultural insight, adaptability, and a sharper sense "
            "of the kind of work and environment where I thrive."
        ),
        "linkedin": "Career break — international travel and personal development sabbatical.",
        "aash_says": (
            "The world is the best classroom. Speak confidently about what you observed, "
            "learned, or built during this time."
        ),
    },
    "Other": {
        "narrative": (
            "I took a career break to address personal circumstances. I approached this period "
            "intentionally, ensuring I returned professionally current and personally ready "
            "to contribute fully."
        ),
        "linkedin": "Career break — personal circumstances.",
        "aash_says": (
            "You don't need to over-explain. A calm, confident framing is far more compelling "
            "than an anxious apology. You made a decision — own it."
        ),
    },
}


# ── Date parsing ──────────────────────────────────────────────

def _parse_date(s: str) -> datetime | None:
    if not s:
        return None
    s = s.strip()
    for fmt in ("%m/%Y", "%Y-%m", "%Y-%m-%d", "%B %Y", "%b %Y", "%Y"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    return None


# ── Gap detection ─────────────────────────────────────────────

def detect_gaps(experience: list[dict]) -> list[dict]:
    """
    Detects employment gaps > GAP_THRESHOLD_DAYS between positions.
    Returns list of gap dicts with start, end, duration_days, duration_months.
    """
    periods: list[tuple[datetime, datetime]] = []

    for exp in experience:
        start = _parse_date(exp.get("start_date", ""))
        end   = datetime.now() if exp.get("current") else _parse_date(exp.get("end_date", ""))
        if start and end and end >= start:
            periods.append((start, end))

    if len(periods) < 2:
        return []

    periods.sort(key=lambda x: x[0])

    gaps: list[dict] = []
    for i in range(1, len(periods)):
        prev_end   = periods[i - 1][1]
        curr_start = periods[i][0]
        if curr_start > prev_end:
            gap_days = (curr_start - prev_end).days
            if gap_days > GAP_THRESHOLD_DAYS:
                gaps.append({
                    "start":          prev_end.strftime("%B %Y"),
                    "end":            curr_start.strftime("%B %Y"),
                    "duration_days":  gap_days,
                    "duration_months":gap_days // 30,
                })

    return gaps


# ── Main render ───────────────────────────────────────────────

def render_gap_analysis(user_id: str, flags: dict) -> None:
    st.header("Gap Analysis Engine")
    st.caption(
        "Detects employment gaps and generates professional, empathetic narratives "
        "for interviews and LinkedIn."
    )

    cv, msg = load_cv(user_id)
    if not cv:
        st.warning("No CV found. Please build and save your CV first.")
        return

    experience = cv.get("experience", [])
    if not experience:
        st.info("No work experience entries found in your CV. Add at least two positions to enable gap detection.")
        return

    gaps = detect_gaps(experience)

    if not gaps:
        st.success(
            "No significant employment gaps detected (threshold: 3 months). "
            "Your timeline appears continuous."
        )
        st.divider()

    else:
        st.markdown(
            f'<div style="background:#FEF3C7;border-left:4px solid #F59E0B;'
            f'padding:12px 16px;border-radius:4px;margin-bottom:16px;">'
            f'<strong>{len(gaps)} gap{"s" if len(gaps)>1 else ""} detected</strong>'
            f' — use the form below to generate professional narratives for each.</div>',
            unsafe_allow_html=True,
        )

        for idx, gap in enumerate(gaps):
            st.subheader(
                f"Gap {idx + 1}: {gap['start']} → {gap['end']} "
                f"({gap['duration_months']} months)"
            )

            category = st.selectbox(
                "How would you categorise this gap?",
                GAP_CATEGORIES,
                key=f"gap_cat_{idx}",
            )

            custom_detail = st.text_area(
                "Optional: add specific detail (e.g. qualification achieved, organisation cared for).",
                height=70,
                key=f"gap_detail_{idx}",
            )

            template = _EMPATHY_TEMPLATES[category]

            narrative = template["narrative"]
            if custom_detail.strip():
                narrative = narrative.rstrip(".") + f", specifically: {custom_detail.strip()}."

            col_n, col_l = st.columns(2)

            with col_n:
                st.markdown("**Interview Narrative**")
                st.markdown(
                    f'<div style="background:#F8FAFC;border:1px solid #E2E8F0;'
                    f'padding:12px;border-radius:6px;font-size:0.9em;line-height:1.6;">'
                    f'{narrative}</div>',
                    unsafe_allow_html=True,
                )
                if st.button("Copy Narrative", key=f"gap_copy_n_{idx}"):
                    st.code(narrative)

            with col_l:
                st.markdown("**LinkedIn Framing**")
                st.markdown(
                    f'<div style="background:#F8FAFC;border:1px solid #E2E8F0;'
                    f'padding:12px;border-radius:6px;font-size:0.9em;line-height:1.6;">'
                    f'{template["linkedin"]}</div>',
                    unsafe_allow_html=True,
                )

            st.markdown(
                f'<div style="background:#EEF2FF;border-left:4px solid #6366F1;'
                f'padding:10px 14px;border-radius:4px;margin-top:8px;font-size:0.88em;">'
                f'<strong>Aash Says:</strong> {template["aash_says"]}</div>',
                unsafe_allow_html=True,
            )

            if idx < len(gaps) - 1:
                st.divider()

    # General gap framing advice
    with st.expander("General Gap Framing Guidance"):
        st.markdown("""
**Core principles:**

1. **Be brief and confident.** A single well-framed sentence outperforms a paragraph of justification.
2. **Own the decision.** Even circumstances beyond your control can be framed as choices you navigated.
3. **Pivot to the present.** After naming the gap, immediately direct attention to what you gained or what you're bringing now.
4. **Never apologise.** Apologetic framing signals lack of confidence; confident framing signals self-awareness.
5. **Consistency matters.** Use the same framing on your CV, LinkedIn, and in interviews.
        """)
