from __future__ import annotations
import streamlit as st
from db.cv_store import save_cv, load_cv, EMPTY_CV
import copy


# ── Helpers ───────────────────────────────────────────────────

def _blank_experience() -> dict:
    return {
        "company":      "",
        "role":         "",
        "start_date":   "",
        "end_date":     "",
        "current":      False,
        "description":  "",
        "achievements": [],
    }


def _blank_education() -> dict:
    return {
        "institution":  "",
        "qualification": "",
        "subject":      "",
        "grade":        "",
        "start_year":   "",
        "end_year":     "",
    }


def _blank_cert() -> dict:
    return {"name": "", "issuer": "", "year": ""}


def _ensure_cv_state(user_id: str) -> None:
    """Load CV from DB into session state if not already loaded."""
    if "cv_data" not in st.session_state or st.session_state.get("cv_owner") != user_id:
        cv, msg = load_cv(user_id)
        st.session_state.cv_data   = cv if cv else copy.deepcopy(EMPTY_CV)
        st.session_state.cv_owner  = user_id
        st.session_state.cv_loaded_msg = msg


# ── Section renderers ─────────────────────────────────────────

def _render_personal(cv: dict) -> None:
    st.subheader("Personal Details")
    p = cv.setdefault("personal", {})
    col1, col2 = st.columns(2)
    with col1:
        p["full_name"] = st.text_input("Full Name",     value=p.get("full_name", ""), key="cv_full_name")
        p["phone"]     = st.text_input("Phone",         value=p.get("phone",     ""), key="cv_phone")
        p["linkedin"]  = st.text_input("LinkedIn URL",  value=p.get("linkedin",  ""), key="cv_linkedin")
    with col2:
        p["email"]    = st.text_input("Email",          value=p.get("email",    ""), key="cv_email")
        p["location"] = st.text_input("Location",       value=p.get("location", ""), key="cv_location")
        p["website"]  = st.text_input("Website / Portfolio", value=p.get("website", ""), key="cv_website")


def _render_profile(cv: dict) -> None:
    st.subheader("Professional Profile Summary")
    cv["profile_summary"] = st.text_area(
        "Write 3–5 sentences summarising your career, skills, and goals.",
        value=cv.get("profile_summary", ""),
        height=140,
        key="cv_profile",
    )
    words = len(cv["profile_summary"].split())
    colour = "#22c55e" if 50 <= words <= 120 else "#f59e0b"
    st.markdown(f'<p style="color:{colour};font-size:0.8em;">{words} words (ideal: 50–120)</p>',
                unsafe_allow_html=True)


def _render_skills(cv: dict) -> None:
    st.subheader("Skills")
    raw = st.text_area(
        "Enter skills separated by commas.",
        value=", ".join(cv.get("skills", [])),
        height=90,
        key="cv_skills",
    )
    cv["skills"] = [s.strip() for s in raw.split(",") if s.strip()]
    st.caption(f"{len(cv['skills'])} skills listed.")


def _render_experience(cv: dict) -> None:
    st.subheader("Work Experience")
    experiences = cv.setdefault("experience", [])

    if st.button("+ Add Position", key="cv_add_exp"):
        experiences.append(_blank_experience())

    for idx, exp in enumerate(experiences):
        with st.expander(
            f"{exp.get('role','Role') or 'Role'} @ {exp.get('company','Company') or 'Company'}",
            expanded=(idx == len(experiences) - 1),
        ):
            col1, col2 = st.columns(2)
            with col1:
                exp["company"]    = st.text_input("Company",    value=exp.get("company",   ""), key=f"exp_co_{idx}")
                exp["start_date"] = st.text_input("Start Date (MM/YYYY)", value=exp.get("start_date",""), key=f"exp_sd_{idx}")
            with col2:
                exp["role"]       = st.text_input("Job Title",  value=exp.get("role",      ""), key=f"exp_ro_{idx}")
                exp["current"]    = st.checkbox("Current Role", value=exp.get("current", False), key=f"exp_cur_{idx}")
                if not exp["current"]:
                    exp["end_date"] = st.text_input("End Date (MM/YYYY)", value=exp.get("end_date",""), key=f"exp_ed_{idx}")
                else:
                    exp["end_date"] = ""

            exp["description"] = st.text_area(
                "Role description & responsibilities",
                value=exp.get("description", ""),
                height=110,
                key=f"exp_desc_{idx}",
            )
            raw_ach = st.text_area(
                "Key achievements (one per line)",
                value="\n".join(exp.get("achievements", [])),
                height=80,
                key=f"exp_ach_{idx}",
            )
            exp["achievements"] = [a.strip() for a in raw_ach.splitlines() if a.strip()]

            if st.button("Remove", key=f"exp_del_{idx}"):
                experiences.pop(idx)
                st.rerun()


def _render_education(cv: dict) -> None:
    st.subheader("Education")
    education = cv.setdefault("education", [])

    if st.button("+ Add Qualification", key="cv_add_edu"):
        education.append(_blank_education())

    for idx, edu in enumerate(education):
        with st.expander(
            f"{edu.get('qualification','Qualification') or 'Qualification'} — {edu.get('institution','Institution') or 'Institution'}",
            expanded=(idx == len(education) - 1),
        ):
            col1, col2 = st.columns(2)
            with col1:
                edu["institution"]   = st.text_input("Institution",   value=edu.get("institution",  ""), key=f"edu_inst_{idx}")
                edu["subject"]       = st.text_input("Subject / Field", value=edu.get("subject",     ""), key=f"edu_subj_{idx}")
                edu["start_year"]    = st.text_input("Start Year",    value=edu.get("start_year",  ""), key=f"edu_sy_{idx}")
            with col2:
                edu["qualification"] = st.text_input("Qualification", value=edu.get("qualification",""), key=f"edu_qual_{idx}")
                edu["grade"]         = st.text_input("Grade / Class", value=edu.get("grade",       ""), key=f"edu_grade_{idx}")
                edu["end_year"]      = st.text_input("End Year",      value=edu.get("end_year",    ""), key=f"edu_ey_{idx}")
            if st.button("Remove", key=f"edu_del_{idx}"):
                education.pop(idx)
                st.rerun()


def _render_certs(cv: dict) -> None:
    st.subheader("Certifications")
    certs = cv.setdefault("certifications", [])

    if st.button("+ Add Certification", key="cv_add_cert"):
        certs.append(_blank_cert())

    for idx, cert in enumerate(certs):
        col1, col2, col3, col4 = st.columns([3, 3, 1, 1])
        with col1:
            cert["name"]   = st.text_input("Certification", value=cert.get("name",  ""), key=f"cert_n_{idx}")
        with col2:
            cert["issuer"] = st.text_input("Issuer",        value=cert.get("issuer",""), key=f"cert_i_{idx}")
        with col3:
            cert["year"]   = st.text_input("Year",          value=cert.get("year",  ""), key=f"cert_y_{idx}")
        with col4:
            st.write("")
            if st.button("✕", key=f"cert_del_{idx}"):
                certs.pop(idx)
                st.rerun()


def _render_languages(cv: dict) -> None:
    st.subheader("Languages")
    raw = st.text_area(
        "Languages (comma-separated, e.g. English (Native), French (B2))",
        value=", ".join(cv.get("languages", [])),
        height=70,
        key="cv_langs",
    )
    cv["languages"] = [l.strip() for l in raw.split(",") if l.strip()]


# ── Main render ───────────────────────────────────────────────

def render_cv_builder(user_id: str, flags: dict) -> None:
    st.header("CV Builder")
    _ensure_cv_state(user_id)
    cv = st.session_state.cv_data

    load_msg = st.session_state.get("cv_loaded_msg", "")
    if "version" in load_msg.lower() or "no cv" in load_msg.lower():
        st.caption(load_msg)

    tab_personal, tab_profile, tab_skills, tab_exp, tab_edu, tab_certs, tab_lang = st.tabs([
        "Personal", "Profile", "Skills", "Experience", "Education", "Certifications", "Languages"
    ])

    with tab_personal:
        _render_personal(cv)
    with tab_profile:
        _render_profile(cv)
    with tab_skills:
        _render_skills(cv)
    with tab_exp:
        _render_experience(cv)
    with tab_edu:
        _render_education(cv)
    with tab_certs:
        _render_certs(cv)
    with tab_lang:
        _render_languages(cv)

    st.divider()
    col_save, col_msg = st.columns([1, 3])
    with col_save:
        if st.button("Save CV", type="primary", key="cv_save_btn"):
            ok, msg = save_cv(user_id, cv)
            if ok:
                st.session_state.cv_loaded_msg = msg
                st.success(msg)
            else:
                st.error(msg)
