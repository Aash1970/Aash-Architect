"""
Coach Review Page — Streamlit UI only.
For Coach role: view assigned users' CVs and add notes.
No business logic here. All operations via cv_service.
No permission_matrix imports — all checks via role_service.
"""

import streamlit as st
from typing import List, Dict, Any

from app.i18n import t
from app.ui.state import get_language, get_role, get_user_id, set_flash
from app.ui.components import show_flash, section_header


def render_coach_page(cv_service, data_service, role_service) -> None:
    """Renders the coach review panel."""
    lang = get_language()
    role = get_role()
    user_id = get_user_id()

    show_flash()
    section_header(t("nav_coach", lang))

    # Get assigned users
    try:
        coach_profile = data_service.get_user(user_id)
    except Exception as exc:
        st.error(str(exc))
        return

    assigned_ids = coach_profile.get("assigned_user_ids", []) if coach_profile else []

    if not assigned_ids:
        st.info(t("coach_no_assigned_users", lang))
        return

    st.markdown(f"**{t('coach_assigned_users', lang)}: {len(assigned_ids)}**")

    selected_user_id = st.selectbox(
        t("coach_select_user", lang),
        assigned_ids,
        key="coach_user_selector",
    )

    if not selected_user_id:
        return

    # Get user's CVs
    try:
        cvs = cv_service.list_cvs(
            requester_id=user_id,
            requester_role=role,
            target_user_id=selected_user_id,
        )
    except Exception as exc:
        st.error(str(exc))
        return

    if not cvs:
        st.info(t("coach_no_cvs", lang))
        return

    cv_options = {
        f"{c.get('title', 'My CV')} (v{c.get('version', 1)})": c["cv_id"]
        for c in cvs
    }
    selected_cv_label = st.selectbox(
        t("coach_select_cv", lang),
        list(cv_options.keys()),
        key="coach_cv_selector",
    )
    selected_cv_id = cv_options.get(selected_cv_label)

    if not selected_cv_id:
        return

    # Load full CV
    try:
        cv = cv_service.get_cv(
            cv_id=selected_cv_id,
            requester_id=user_id,
            requester_role=role,
        )
    except Exception as exc:
        st.error(str(exc))
        return

    _render_cv_summary(cv, lang)

    st.markdown("---")
    st.markdown(f"### {t('coach_notes', lang)}")

    # Existing notes
    try:
        notes = cv_service.get_coach_notes(
            cv_id=selected_cv_id,
            requester_id=user_id,
            requester_role=role,
        )
        if notes:
            for note in notes:
                with st.expander(
                    f"Note — {note.get('created_at', '')[:10]}",
                    expanded=True,
                ):
                    st.write(note.get("note_text", ""))
    except Exception as exc:
        st.error(str(exc))

    # Add new note — display conditional on permission (service will also enforce)
    if role_service.check_permission(role, "cv.comment_assigned"):
        with st.form("add_note_form"):
            note_text = st.text_area(
                t("coach_add_note_label", lang),
                height=120,
                placeholder=t("coach_add_note_placeholder", lang),
                key="coach_note_text",
            )
            submitted = st.form_submit_button(t("coach_btn_add_note", lang), type="primary")

        if submitted:
            if not note_text or len(note_text.strip()) < 5:
                st.error(t("coach_note_min_length", lang))
            else:
                try:
                    cv_service.add_coach_note(
                        cv_id=selected_cv_id,
                        note_text=note_text.strip(),
                        coach_id=user_id,
                        coach_role=role,
                    )
                    set_flash(t("coach_note_added", lang), "success")
                    st.rerun()
                except Exception as exc:
                    st.error(str(exc))


def _render_cv_summary(cv: Dict[str, Any], lang: str) -> None:
    """Renders a read-only CV summary for the coach."""
    pi = cv.get("personal_info", {})
    st.markdown(f"### {pi.get('full_name', '?')}")

    col1, col2 = st.columns(2)
    with col1:
        st.write(f"**{t('coach_label_email', lang)}:** {pi.get('email', '')}")
        st.write(f"**{t('coach_label_location', lang)}:** {pi.get('location', '')}")
    with col2:
        st.write(f"**{t('coach_label_mobile', lang)}:** {pi.get('mobile', '')}")
        if pi.get("linkedin"):
            st.write(f"**{t('coach_label_linkedin', lang)}:** {pi['linkedin']}")

    if pi.get("summary"):
        st.markdown(f"*{pi['summary']}*")

    work = cv.get("work_experience", [])
    if work:
        st.markdown(
            f"**{t('section_work_experience', lang)}** "
            f"({len(work)} {t('label_entries', lang)})"
        )
        for w in work[:3]:
            st.write(f"• {w.get('position', '')} at {w.get('company', '')}")

    skills = cv.get("skills", [])
    if skills:
        st.markdown(
            f"**{t('section_skills', lang)}:** "
            + ", ".join(s.get("name", "") for s in skills[:10])
        )
