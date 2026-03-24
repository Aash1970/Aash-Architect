"""
CV Builder Page — Streamlit UI only.
Handles CV creation and editing.
All business logic delegated to CVService.
Validation uses app.validation.validators (called via service).
UI uses proper input types: st.date_input, email text_input, numeric mobile.
"""

import streamlit as st
from datetime import date, datetime
from typing import Dict, Any, List, Optional

from app.i18n import t
from app.ui.state import (
    get_language, get_user_id, get_role, get_tier,
    set_flash, navigate_to
)
from app.ui.components import (
    show_flash, show_validation_errors, section_header,
    tier_badge, upgrade_prompt
)
from app.validation.validators import (
    validate_personal_info, validate_work_experience,
    validate_education, validate_skill, validate_certification,
    validate_language_entry, sanitize_text
)


def render_cv_builder(cv_service, cv_dict: Optional[Dict[str, Any]] = None) -> None:
    """
    Renders the CV builder/editor form.

    Args:
        cv_service: CVService instance
        cv_dict:    Existing CV dict for editing, or None for new CV
    """
    lang = get_language()
    is_edit = cv_dict is not None

    show_flash()

    title_key = "edit_cv" if is_edit else "create_new_cv"
    st.markdown(f"### {t(title_key, lang)}")

    if is_edit:
        col1, col2, col3 = st.columns([3, 1, 1])
        with col2:
            st.markdown(f"v{cv_dict.get('version', 1)}")
        with col3:
            tier_badge(cv_dict.get("tier", "Free"))

    # ── Tabs for each CV section ─────────────────────────────────────────────
    tab_personal, tab_work, tab_edu, tab_skills, tab_langs, tab_certs = st.tabs([
        t("section_personal_info", lang),
        t("section_work_experience", lang),
        t("section_education", lang),
        t("section_skills", lang),
        t("section_languages", lang),
        t("section_certifications", lang),
    ])

    with tab_personal:
        _render_personal_info_section(cv_dict, lang)

    with tab_work:
        _render_work_experience_section(cv_dict, lang)

    with tab_edu:
        _render_education_section(cv_dict, lang)

    with tab_skills:
        _render_skills_section(cv_dict, lang)

    with tab_langs:
        _render_languages_section(cv_dict, lang)

    with tab_certs:
        _render_certifications_section(cv_dict, lang)

    st.divider()

    # ── Save / Cancel buttons ────────────────────────────────────────────────
    col_save, col_cancel = st.columns([1, 1])
    with col_save:
        if st.button(
            t("btn_save", lang), type="primary", use_container_width=True,
            key="cv_save_btn"
        ):
            _handle_save(cv_service, cv_dict, lang)

    with col_cancel:
        if st.button(
            t("btn_cancel", lang), use_container_width=True, key="cv_cancel_btn"
        ):
            navigate_to("cv_list")
            st.rerun()


def _render_personal_info_section(cv_dict: Optional[Dict], lang: str) -> None:
    """Personal information section with proper input types."""
    pi = cv_dict.get("personal_info", {}) if cv_dict else {}

    section_header(t("section_personal_info", lang), divider=False)

    col1, col2 = st.columns(2)
    with col1:
        full_name = st.text_input(
            t("label_full_name", lang) + " *",
            value=pi.get("full_name", ""),
            key="pi_full_name",
            max_chars=100,
        )
        email = st.text_input(
            t("label_email", lang) + " *",
            value=pi.get("email", ""),
            key="pi_email",
            placeholder="name@example.com",
        )
        mobile = st.text_input(
            t("label_mobile", lang) + " *",
            value=pi.get("mobile", ""),
            key="pi_mobile",
            placeholder="+44 7700 000000",
            help=t("placeholder_mobile_help", lang),
        )

    with col2:
        location = st.text_input(
            t("label_location", lang) + " *",
            value=pi.get("location", ""),
            key="pi_location",
        )
        linkedin = st.text_input(
            t("label_linkedin", lang),
            value=pi.get("linkedin", "") or "",
            key="pi_linkedin",
            placeholder="https://linkedin.com/in/yourprofile",
        )
        website = st.text_input(
            t("label_website", lang),
            value=pi.get("website", "") or "",
            key="pi_website",
            placeholder="https://yourwebsite.com",
        )

    summary = st.text_area(
        t("label_summary", lang),
        value=pi.get("summary", "") or "",
        key="pi_summary",
        height=120,
        placeholder=t("placeholder_summary", lang),
        max_chars=1000,
    )

    st.session_state["_cv_personal_info"] = {
        "full_name": sanitize_text(full_name),
        "email": sanitize_text(email),
        "mobile": sanitize_text(mobile),
        "location": sanitize_text(location),
        "linkedin": sanitize_text(linkedin) or None,
        "website": sanitize_text(website) or None,
        "summary": sanitize_text(summary) or None,
    }


def _render_work_experience_section(cv_dict: Optional[Dict], lang: str) -> None:
    """Work experience section with add/remove functionality."""
    work_list = cv_dict.get("work_experience", []) if cv_dict else []

    section_header(t("section_work_experience", lang), divider=False)

    if work_list:
        for i, entry in enumerate(work_list):
            end_display = (
                t("label_present", lang)
                if entry.get("is_current")
                else entry.get("end_date", "")
            )
            with st.expander(
                f"{entry.get('position', 'Role')} @ {entry.get('company', 'Company')}",
                expanded=False,
            ):
                st.write(
                    f"**{t('label_dates', lang)}:** {entry.get('start_date', '')} — "
                    f"{end_display}"
                )
                st.write(entry.get("description", ""))

    st.markdown("---")
    st.markdown(f"**{t('btn_add', lang)} {t('section_work_experience', lang)}**")

    with st.form("add_work_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            company = st.text_input(t("label_company", lang) + " *", key="w_company")
            position = st.text_input(t("label_position", lang) + " *", key="w_position")
        with col2:
            start_date = st.date_input(
                t("label_start_date", lang) + " *",
                key="w_start_date",
                value=date(2020, 1, 1),
            )
            is_current = st.checkbox(t("label_is_current", lang), key="w_is_current")
            end_date = None
            if not is_current:
                end_date = st.date_input(
                    t("label_end_date", lang) + " *",
                    key="w_end_date",
                    value=date.today(),
                )

        description = st.text_area(
            t("label_description", lang) + " *",
            key="w_description",
            placeholder=t("placeholder_description", lang),
            height=100,
        )
        achievements_raw = st.text_area(
            t("label_achievements", lang),
            key="w_achievements",
            placeholder=t("placeholder_achievements", lang),
            height=80,
        )

        add_submitted = st.form_submit_button(
            f"+ {t('btn_add', lang)}", type="primary"
        )

    if add_submitted:
        entry_data = {
            "company": sanitize_text(company),
            "position": sanitize_text(position),
            "start_date": start_date.isoformat() if start_date else "",
            "end_date": end_date.isoformat() if end_date else None,
            "is_current": is_current,
            "description": sanitize_text(description),
            "achievements": [
                sanitize_text(a)
                for a in achievements_raw.split("\n")
                if a.strip()
            ],
        }
        errors = validate_work_experience(entry_data)
        if errors:
            show_validation_errors(errors)
        else:
            if "_cv_work_experience" not in st.session_state:
                st.session_state["_cv_work_experience"] = list(work_list)
            st.session_state["_cv_work_experience"].append(entry_data)
            set_flash(t("work_entry_added", lang), "success")
            st.rerun()

    if "_cv_work_experience" not in st.session_state:
        st.session_state["_cv_work_experience"] = list(work_list)


def _render_education_section(cv_dict: Optional[Dict], lang: str) -> None:
    """Education section."""
    edu_list = cv_dict.get("education", []) if cv_dict else []

    section_header(t("section_education", lang), divider=False)

    if edu_list:
        for entry in edu_list:
            end_display = (
                t("label_present", lang)
                if entry.get("is_current")
                else entry.get("end_date", "")
            )
            with st.expander(
                f"{entry.get('degree', '')} — {entry.get('institution', '')}",
                expanded=False,
            ):
                st.write(f"**{t('label_field_of_study', lang)}:** {entry.get('field_of_study', '')}")
                st.write(
                    f"**{t('label_dates', lang)}:** {entry.get('start_date', '')} — "
                    f"{end_display}"
                )

    st.markdown("---")
    st.markdown(f"**{t('btn_add', lang)} {t('section_education', lang)}**")

    with st.form("add_edu_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            institution = st.text_input(t("label_institution", lang) + " *", key="e_inst")
            degree = st.text_input(t("label_degree", lang) + " *", key="e_degree")
            field = st.text_input(t("label_field_of_study", lang) + " *", key="e_field")
        with col2:
            start_date = st.date_input(
                t("label_start_date", lang) + " *",
                key="e_start",
                value=date(2015, 9, 1),
            )
            is_current = st.checkbox(t("label_is_current", lang), key="e_current")
            end_date = None
            if not is_current:
                end_date = st.date_input(
                    t("label_end_date", lang),
                    key="e_end",
                    value=date(2019, 6, 30),
                )
            grade = st.text_input(t("label_grade", lang), key="e_grade")

        add_submitted = st.form_submit_button(f"+ {t('btn_add', lang)}", type="primary")

    if add_submitted:
        entry_data = {
            "institution": sanitize_text(institution),
            "degree": sanitize_text(degree),
            "field_of_study": sanitize_text(field),
            "start_date": start_date.isoformat() if start_date else "",
            "end_date": end_date.isoformat() if end_date else None,
            "is_current": is_current,
            "grade": sanitize_text(grade) or None,
        }
        errors = validate_education(entry_data)
        if errors:
            show_validation_errors(errors)
        else:
            if "_cv_education" not in st.session_state:
                st.session_state["_cv_education"] = list(edu_list)
            st.session_state["_cv_education"].append(entry_data)
            set_flash(t("education_entry_added", lang), "success")
            st.rerun()

    if "_cv_education" not in st.session_state:
        st.session_state["_cv_education"] = list(edu_list)


def _render_skills_section(cv_dict: Optional[Dict], lang: str) -> None:
    """Skills section."""
    skills_list = cv_dict.get("skills", []) if cv_dict else []

    section_header(t("section_skills", lang), divider=False)

    if skills_list:
        cols = st.columns(4)
        for i, s in enumerate(skills_list):
            level = s.get("level", "Beginner")
            level_color = {
                "Expert": "#059669",
                "Advanced": "#7C3AED",
                "Intermediate": "#2563EB",
                "Beginner": "#6B7280",
            }.get(level, "#6B7280")
            level_display = t(f"skill_level_{level.lower()}", lang)
            with cols[i % 4]:
                st.markdown(
                    f'<div style="background:#F1F5F9; padding:8px 12px; '
                    f'border-radius:8px; margin:4px 0;">'
                    f'<strong>{s.get("name", "")}</strong><br/>'
                    f'<span style="color:{level_color}; font-size:12px;">'
                    f'{level_display}</span></div>',
                    unsafe_allow_html=True,
                )

    st.markdown("---")
    with st.form("add_skill_form", clear_on_submit=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            skill_name = st.text_input(t("label_skill_name", lang) + " *", key="sk_name")
        with col2:
            skill_level = st.selectbox(
                t("label_skill_level", lang),
                ["Beginner", "Intermediate", "Advanced", "Expert"],
                key="sk_level",
            )
        with col3:
            skill_cat = st.text_input(t("label_skill_category", lang), key="sk_cat")

        add_submitted = st.form_submit_button(f"+ {t('btn_add', lang)}", type="primary")

    if add_submitted:
        entry = {
            "name": sanitize_text(skill_name),
            "level": skill_level,
            "category": sanitize_text(skill_cat) or None,
        }
        errors = validate_skill(entry)
        if errors:
            show_validation_errors(errors)
        else:
            if "_cv_skills" not in st.session_state:
                st.session_state["_cv_skills"] = list(skills_list)
            st.session_state["_cv_skills"].append(entry)
            set_flash(t("skill_added", lang), "success")
            st.rerun()

    if "_cv_skills" not in st.session_state:
        st.session_state["_cv_skills"] = list(skills_list)


def _render_languages_section(cv_dict: Optional[Dict], lang: str) -> None:
    """Languages section."""
    langs_list = cv_dict.get("languages", []) if cv_dict else []

    section_header(t("section_languages", lang), divider=False)

    if langs_list:
        for entry in langs_list:
            st.write(f"**{entry.get('name', '')}** — {entry.get('proficiency', '')}")

    st.markdown("---")
    with st.form("add_lang_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            lang_name = st.text_input(t("label_language_name", lang) + " *", key="ln_name")
        with col2:
            proficiency = st.selectbox(
                t("label_proficiency", lang),
                ["A1", "A2", "B1", "B2", "C1", "C2", "Native"],
                index=4,
                key="ln_prof",
            )

        add_submitted = st.form_submit_button(f"+ {t('btn_add', lang)}", type="primary")

    if add_submitted:
        entry = {
            "name": sanitize_text(lang_name),
            "proficiency": proficiency,
        }
        errors = validate_language_entry(entry)
        if errors:
            show_validation_errors(errors)
        else:
            if "_cv_languages" not in st.session_state:
                st.session_state["_cv_languages"] = list(langs_list)
            st.session_state["_cv_languages"].append(entry)
            set_flash(t("language_added", lang), "success")
            st.rerun()

    if "_cv_languages" not in st.session_state:
        st.session_state["_cv_languages"] = list(langs_list)


def _render_certifications_section(cv_dict: Optional[Dict], lang: str) -> None:
    """Certifications section."""
    certs_list = cv_dict.get("certifications", []) if cv_dict else []

    section_header(t("section_certifications", lang), divider=False)

    if certs_list:
        for c in certs_list:
            st.write(f"**{c.get('name', '')}** — {c.get('issuer', '')} ({c.get('issue_date', '')})")

    st.markdown("---")
    with st.form("add_cert_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            cert_name = st.text_input(t("label_cert_name", lang) + " *", key="c_name")
            issuer = st.text_input(t("label_issuer", lang) + " *", key="c_issuer")
        with col2:
            issue_date = st.date_input(
                t("label_issue_date", lang) + " *",
                key="c_issue",
                value=date.today(),
            )
            expiry_date = st.date_input(
                t("label_expiry_date", lang),
                key="c_expiry",
                value=None,
            )
        credential_id = st.text_input(t("label_credential_id", lang), key="c_cred_id")
        cert_url = st.text_input(t("label_cert_url", lang), key="c_url")

        add_submitted = st.form_submit_button(f"+ {t('btn_add', lang)}", type="primary")

    if add_submitted:
        entry = {
            "name": sanitize_text(cert_name),
            "issuer": sanitize_text(issuer),
            "issue_date": issue_date.isoformat() if issue_date else "",
            "expiry_date": expiry_date.isoformat() if expiry_date else None,
            "credential_id": sanitize_text(credential_id) or None,
            "url": sanitize_text(cert_url) or None,
        }
        errors = validate_certification(entry)
        if errors:
            show_validation_errors(errors)
        else:
            if "_cv_certifications" not in st.session_state:
                st.session_state["_cv_certifications"] = list(certs_list)
            st.session_state["_cv_certifications"].append(entry)
            set_flash(t("certification_added", lang), "success")
            st.rerun()

    if "_cv_certifications" not in st.session_state:
        st.session_state["_cv_certifications"] = list(certs_list)


def _handle_save(cv_service, cv_dict: Optional[Dict], lang: str) -> None:
    """Collects all section data from session state and saves via cv_service."""
    from app.validation.validators import validate_personal_info, ValidationError

    user_id = get_user_id()
    role = get_role()
    tier = get_tier()

    pi = st.session_state.get("_cv_personal_info", {})

    errors = validate_personal_info(pi)
    if errors:
        show_validation_errors(errors)
        return

    cv_data = {
        "personal_info": pi,
        "work_experience": st.session_state.get("_cv_work_experience", []),
        "education": st.session_state.get("_cv_education", []),
        "skills": st.session_state.get("_cv_skills", []),
        "languages": st.session_state.get("_cv_languages", []),
        "certifications": st.session_state.get("_cv_certifications", []),
        "title": pi.get("full_name", "My CV") + "'s CV",
    }

    try:
        if cv_dict and cv_dict.get("cv_id"):
            cv_service.update_cv(
                cv_id=cv_dict["cv_id"],
                updates=cv_data,
                requester_id=user_id,
                requester_role=role,
            )
        else:
            cv_service.create_cv(
                cv_data=cv_data,
                requester_id=user_id,
                requester_role=role,
                requester_tier=tier,
            )

        for key in ["_cv_personal_info", "_cv_work_experience", "_cv_education",
                    "_cv_skills", "_cv_languages", "_cv_certifications"]:
            st.session_state.pop(key, None)

        set_flash(t("msg_saved", lang), "success")
        navigate_to("cv_list")
        st.rerun()

    except ValidationError as exc:
        show_validation_errors(exc.errors)
    except Exception as exc:
        st.error(str(exc))
