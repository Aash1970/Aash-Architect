"""
Coach Review Page — Streamlit UI only.
For Coach role: view assigned users' CVs and add notes.
No business logic here. All operations via cv_service.
"""

import streamlit as st
from typing import List, Dict, Any

from app.i18n import t
from app.ui.state import get_language, get_role, get_user_id, set_flash
from app.ui.components import show_flash, section_header
from app.roles.permission_matrix import has_permission


def render_coach_page(cv_service, data_service) -> None:
    """Renders the coach review panel."""
    lang = get_language()
    role = get_role()
    user_id = get_user_id()

    show_flash()
    section_header(t("nav_coach", lang))

    if not has_permission(role, "cv.read_assigned"):
        st.error(t("msg_permission_denied", lang))
        return

    # Get assigned users
    coach_profile = data_service.get_user(user_id)
    assigned_ids = coach_profile.get("assigned_user_ids", []) if coach_profile else []

    if not assigned_ids:
        st.info("No users are currently assigned to you.")
        return

    st.markdown(f"**{t('coach_assigned_users', lang)}: {len(assigned_ids)}**")

    selected_user_id = st.selectbox(
        "Select User",
        assigned_ids,
        key="coach_user_selector",
    )

    if not selected_user_id:
        return

    # Get user's CVs
    cvs = cv_service.list_cvs(
        requester_id=user_id,
        requester_role=role,
        target_user_id=selected_user_id,
    )

    if not cvs:
        st.info("This user has no CVs yet.")
        return

    cv_options = {
        f"{c.get('title', 'My CV')} (v{c.get('version', 1)})": c["cv_id"]
        for c in cvs
    }
    selected_cv_label = st.selectbox(
        "Select CV",
        list(cv_options.keys()),
        key="coach_cv_selector",
    )
    selected_cv_id = cv_options.get(selected_cv_label)

    if not selected_cv_id:
        return

    # Load full CV
    cv = cv_service.get_cv(
        cv_id=selected_cv_id,
        requester_id=user_id,
        requester_role=role,
    )

    _render_cv_summary(cv, lang)

    st.markdown("---")
    st.markdown(f"### {t('coach_notes', lang)}")

    # Existing notes
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

    # Add new note
    if has_permission(role, "cv.comment_assigned"):
        with st.form("add_note_form"):
            note_text = st.text_area(
                "Add a note",
                height=120,
                placeholder="Provide feedback for the candidate...",
                key="coach_note_text",
            )
            submitted = st.form_submit_button("Add Note", type="primary")

        if submitted:
            if not note_text or len(note_text.strip()) < 5:
                st.error("Note must be at least 5 characters.")
            else:
                try:
                    cv_service.add_coach_note(
                        cv_id=selected_cv_id,
                        note_text=note_text.strip(),
                        coach_id=user_id,
                        coach_role=role,
                    )
                    set_flash("Note added successfully.", "success")
                    st.rerun()
                except Exception as exc:
                    st.error(str(exc))


def _render_cv_summary(cv: Dict[str, Any], lang: str) -> None:
    """Renders a read-only CV summary for the coach."""
    pi = cv.get("personal_info", {})
    st.markdown(f"### {pi.get('full_name', 'Unknown')}")

    col1, col2 = st.columns(2)
    with col1:
        st.write(f"**Email:** {pi.get('email', '')}")
        st.write(f"**Location:** {pi.get('location', '')}")
    with col2:
        st.write(f"**Mobile:** {pi.get('mobile', '')}")
        if pi.get("linkedin"):
            st.write(f"**LinkedIn:** {pi['linkedin']}")

    if pi.get("summary"):
        st.markdown(f"*{pi['summary']}*")

    work = cv.get("work_experience", [])
    if work:
        st.markdown(f"**Experience** ({len(work)} entries)")
        for w in work[:3]:
            st.write(f"• {w.get('position', '')} at {w.get('company', '')}")

    skills = cv.get("skills", [])
    if skills:
        st.markdown(f"**Skills:** " + ", ".join(s.get("name", "") for s in skills[:10]))
