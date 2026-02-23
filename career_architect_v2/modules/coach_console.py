from __future__ import annotations
import streamlit as st
from db.client import get_client
from db.cv_store import load_cv_for_coach


# ── DB helpers ────────────────────────────────────────────────

def _get_assigned_users(coach_id: str) -> list[dict]:
    """
    Returns users assigned to this coach via coach_assignments.
    Falls back to showing all users from user_roles for coaches
    without explicit assignments (graceful degradation).
    """
    try:
        result = (
            get_client()
            .table("coach_assignments")
            .select("user_id")
            .eq("coach_id", coach_id)
            .execute()
        )
        if not result.data:
            return []

        user_ids = [r["user_id"] for r in result.data]

        roles = (
            get_client()
            .table("user_roles")
            .select("user_id, email, role, created_at")
            .in_("user_id", user_ids)
            .execute()
        )
        return roles.data or []
    except Exception:
        return []


def _get_user_reflections(user_id: str, limit: int = 10) -> list[dict]:
    try:
        result = (
            get_client()
            .table("reflections")
            .select("entry_date, mood, content, goals")
            .eq("user_id", user_id)
            .order("entry_date", desc=True)
            .limit(limit)
            .execute()
        )
        return result.data or []
    except Exception:
        return []


def _get_user_ats_results(user_id: str) -> list[dict]:
    try:
        result = (
            get_client()
            .table("ats_results")
            .select("level, job_title, score, created_at")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .limit(5)
            .execute()
        )
        return result.data or []
    except Exception:
        return []


# ── Main render ───────────────────────────────────────────────

def render_coach_console(user_id: str, role: str, flags: dict) -> None:
    st.header("Coach Console")
    st.caption(
        "View the progress, CVs, and reflections of users assigned to you."
    )

    assigned = _get_assigned_users(user_id)

    if not assigned:
        st.info(
            "No users are currently assigned to you. "
            "Contact an Admin to have users linked to your coaching profile."
        )
        return

    st.markdown(f"**{len(assigned)} user{'s' if len(assigned) != 1 else ''} assigned to you.**")

    selected_email = st.selectbox(
        "Select a user to review",
        options=[u.get("email") or u.get("user_id") for u in assigned],
        key="coach_user_select",
    )

    selected = next(
        (u for u in assigned if u.get("email") == selected_email or u.get("user_id") == selected_email),
        None,
    )
    if not selected:
        return

    target_id = selected["user_id"]
    st.divider()

    tab_overview, tab_cv, tab_reflect, tab_ats = st.tabs(
        ["Overview", "CV", "Reflections", "ATS Results"]
    )

    with tab_overview:
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"**Email:** {selected.get('email','—')}")
            st.markdown(f"**Role:** {selected.get('role','—')}")
        with col2:
            joined = selected.get("created_at", "")[:10] if selected.get("created_at") else "—"
            st.markdown(f"**Joined:** {joined}")

        reflections = _get_user_reflections(target_id, limit=5)
        ats_results = _get_user_ats_results(target_id)

        st.divider()
        col_r, col_a = st.columns(2)
        with col_r:
            st.metric("Reflections (recent)", len(reflections))
        with col_a:
            st.metric("ATS Scans (recent)", len(ats_results))
            if ats_results:
                avg = sum(r["score"] for r in ats_results) / len(ats_results)
                st.metric("Avg ATS Score", f"{avg:.1f}")

    with tab_cv:
        cv, msg = load_cv_for_coach(target_id, user_id)
        if not cv:
            st.info(f"No CV saved yet for this user. ({msg})")
        else:
            st.caption(msg)
            p = cv.get("personal", {})
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"**Name:** {p.get('full_name','—')}")
                st.markdown(f"**Location:** {p.get('location','—')}")
            with col2:
                st.markdown(f"**Email:** {p.get('email','—')}")
                st.markdown(f"**Phone:** {p.get('phone','—')}")

            st.subheader("Profile Summary")
            summary = cv.get("profile_summary", "")
            st.markdown(
                f'<div style="background:#F8FAFC;border:1px solid #E2E8F0;'
                f'padding:12px;border-radius:6px;">'
                f'{summary if summary else "<em>No summary written.</em>"}</div>',
                unsafe_allow_html=True,
            )

            skills = cv.get("skills", [])
            if skills:
                st.subheader("Skills")
                st.markdown(
                    " ".join(
                        f'<span style="background:#EEF2FF;color:#4F46E5;padding:2px 8px;'
                        f'border-radius:12px;font-size:0.8em;margin:2px;display:inline-block;">{s}</span>'
                        for s in skills
                    ),
                    unsafe_allow_html=True,
                )

            experience = cv.get("experience", [])
            if experience:
                st.subheader("Experience")
                for exp in experience:
                    status = "Present" if exp.get("current") else exp.get("end_date", "")
                    st.markdown(
                        f"**{exp.get('role','—')}** at {exp.get('company','—')} "
                        f"({exp.get('start_date','—')} – {status})"
                    )

    with tab_reflect:
        reflections = _get_user_reflections(target_id, limit=10)
        if not reflections:
            st.info("No reflections recorded yet.")
        else:
            mood_colours = {
                "Excellent":"#22c55e","Good":"#84cc16","Neutral":"#94a3b8",
                "Difficult":"#f59e0b","Challenging":"#ef4444",
            }
            for r in reflections:
                colour = mood_colours.get(r.get("mood","Neutral"), "#94a3b8")
                with st.expander(f"{r.get('entry_date','—')}  ·  {r.get('mood','—')}", expanded=False):
                    st.markdown(
                        f'<div style="border-left:4px solid {colour};padding:8px 12px;">'
                        f'{r.get("content","")}</div>',
                        unsafe_allow_html=True,
                    )
                    if r.get("goals"):
                        st.markdown(f"**Goals:** {r['goals']}")

    with tab_ats:
        ats_results = _get_user_ats_results(target_id)
        if not ats_results:
            st.info("No ATS scans recorded yet.")
        else:
            for r in ats_results:
                score = r.get("score", 0)
                colour = "#22c55e" if score >= 75 else "#f59e0b" if score >= 50 else "#ef4444"
                st.markdown(
                    f'<div style="background:#F8FAFC;border:1px solid #E2E8F0;'
                    f'padding:10px 14px;border-radius:6px;margin-bottom:8px;display:flex;'
                    f'justify-content:space-between;">'
                    f'<span>Level {r.get("level")} — {r.get("job_title","Untitled")}</span>'
                    f'<span style="color:{colour};font-weight:700;">{score:.1f}/100</span>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
