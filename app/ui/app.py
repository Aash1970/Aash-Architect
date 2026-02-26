"""
Main Streamlit Application Entry Point — UI Layer Only.
No business logic here. All logic delegated to service layer.
No Streamlit imports in any other module outside /ui.
No permission_matrix imports — all permission checks via RoleService.
"""

import streamlit as st

from app.ui.state import init_session_state, is_authenticated, get_role, get_language
from app.ui.state import get_user_id, get_tier, navigate_to, set_flash, clear_session
from app.ui.components import show_flash, tier_badge, role_badge
from app.i18n import t, get_supported_languages

# ── Service dependencies (injected at startup) ───────────────────────────────
from app.services.data_service import DataService
from app.services.auth_service import AuthService
from app.services.role_service import RoleService
from app.services.tier_service import TierService
from app.services.cv_service import CVService
from app.services.ats_service import ATSService
from app.admin.admin_service import AdminService
from app.lifecycle.versioning import VersioningService
from app.lifecycle.retention import RetentionService
from app.security.package_builder import PackageBuilder


def _build_services():
    """Constructs the service dependency graph. Called once per session."""
    ds = DataService()
    rs = RoleService()
    ts = TierService(ds)
    vs = VersioningService()
    pb = PackageBuilder()
    ret = RetentionService()
    cv_svc = CVService(ds, rs, ts, vs, pb)
    auth_svc = AuthService(ds)
    admin_svc = AdminService(ds, rs, ret)
    ats_svc = ATSService(cv_svc, ts)
    return ds, auth_svc, cv_svc, admin_svc, rs, ats_svc


def _apply_global_css() -> None:
    """Injects global CSS for consistent design system."""
    st.markdown("""
    <style>
    /* Core palette */
    .stApp { background-color: #F8FAFC !important; }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #0F172A !important;
        border-right: 2px solid #4F46E5 !important;
    }
    [data-testid="stSidebar"] * { color: #E2E8F0 !important; }

    /* Typography */
    html, body, [class*="css"] {
        font-family: 'Segoe UI', system-ui, -apple-system, sans-serif !important;
    }
    h1, h2, h3 { color: #1E293B !important; font-weight: 700; }

    /* Primary buttons */
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #4F46E5, #7C3AED) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
    }

    /* Form inputs */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea {
        border: 1px solid #CBD5E1 !important;
        border-radius: 6px !important;
        padding: 8px 12px !important;
    }
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: #4F46E5 !important;
        box-shadow: 0 0 0 2px rgba(79,70,229,0.2) !important;
    }

    /* Cards */
    .metric-card {
        background: white;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 20px;
    }

    /* Dividers */
    hr { border-color: #E2E8F0 !important; }
    </style>
    """, unsafe_allow_html=True)


def _render_sidebar(role: str, tier: str, name: str, lang: str, rs: RoleService) -> None:
    """Renders the navigation sidebar with role-based menu."""
    with st.sidebar:
        st.markdown(f"### {t('app_title', lang)}")
        st.markdown(f"*{t('app_subtitle', lang)}*")
        st.divider()

        st.markdown(f"**{name}**")
        col1, col2 = st.columns(2)
        with col1:
            role_badge(role)
        with col2:
            tier_badge(tier)
        st.divider()

        pages = [
            ("cv_list", t("my_cvs", lang), "📄", "cv.read_own"),
        ]

        if rs.check_permission(role, "ats.basic"):
            pages.append(("ats", t("nav_ats", lang), "🎯", "ats.basic"))

        if rs.check_permission(role, "cv.read_assigned"):
            pages.append(("coach", t("nav_coach", lang), "👨‍🏫", "cv.read_assigned"))

        if rs.check_permission(role, "admin.panel.access"):
            pages.append(("admin", t("nav_admin", lang), "⚙️", "admin.panel.access"))

        for page_id, label, icon, perm in pages:
            if rs.check_permission(role, perm):
                if st.button(
                    f"{icon} {label}",
                    key=f"nav_{page_id}",
                    use_container_width=True,
                ):
                    navigate_to(page_id)
                    st.rerun()

        st.divider()

        supported = get_supported_languages()
        lang_options = list(supported.keys())
        lang_labels = list(supported.values())
        current_idx = lang_options.index(lang) if lang in lang_options else 0
        selected_label = st.selectbox(
            t("select_language", lang),
            lang_labels,
            index=current_idx,
            key="sidebar_lang",
        )
        selected_code = lang_options[lang_labels.index(selected_label)]
        if selected_code != lang:
            st.session_state["language"] = selected_code
            st.rerun()

        st.divider()

        if st.button(f"🚪 {t('nav_logout', lang)}", use_container_width=True):
            clear_session()
            st.rerun()


def _render_cv_list_page(cv_service, lang: str, rs: RoleService) -> None:
    """CV list page — shows user's CVs with export and edit actions."""
    from app.ui.components import section_header
    from app.tier.tier_rules import get_tier_limits

    section_header(t("my_cvs", lang))
    show_flash()

    user_id = get_user_id()
    role = get_role()
    tier = get_tier()

    cvs = cv_service.list_cvs(requester_id=user_id, requester_role=role)
    active_cvs = [c for c in cvs if not c.get("is_deleted")]

    col_new, col_count = st.columns([1, 3])
    with col_new:
        if st.button(f"+ {t('create_new_cv', lang)}", type="primary"):
            navigate_to("cv_builder_new")
            st.rerun()

    with col_count:
        limits = get_tier_limits(tier)
        max_cv = limits.max_cvs
        count_display = (
            f"{len(active_cvs)}/{max_cv}"
            if max_cv != -1
            else f"{len(active_cvs)} / {t('unlimited', lang)}"
        )
        st.info(f"{t('label_cvs', lang)}: {count_display}")

    if not active_cvs:
        st.info(t("no_cvs_found", lang))
        return

    for cv in active_cvs:
        pi = cv.get("personal_info", {})
        cv_title = cv.get("title", t("cv_title_default", lang))
        with st.container():
            st.markdown(
                f"""
                <div style="background:white; border:1px solid #E2E8F0;
                            border-radius:12px; padding:16px; margin:8px 0;">
                    <strong>{cv_title}</strong>
                    &nbsp;•&nbsp; v{cv.get('version', 1)}
                    &nbsp;•&nbsp; {pi.get('full_name', '')}
                </div>
                """,
                unsafe_allow_html=True,
            )
            col1, col2, col3, col4 = st.columns(4)
            cv_id = cv["cv_id"]

            with col1:
                if st.button(f"✏️ {t('btn_edit', lang)}", key=f"edit_{cv_id}"):
                    navigate_to("cv_builder_edit", cv_id=cv_id)
                    st.rerun()
            with col2:
                if st.button(f"📦 {t('btn_export', lang)}", key=f"export_{cv_id}"):
                    _handle_export(cv_service, cv_id, lang, tier)
            with col3:
                if st.button(f"👨‍🏫 {t('btn_coach_short', lang)}", key=f"coach_{cv_id}"):
                    try:
                        cv_service.submit_to_coach(
                            cv_id=cv_id,
                            coach_id="",
                            requester_id=user_id,
                            requester_role=role,
                            requester_tier=tier,
                        )
                        set_flash(t("msg_coach_submitted", lang), "success")
                        st.rerun()
                    except Exception as exc:
                        st.error(str(exc))
            with col4:
                if st.button(
                    f"🗑️ {t('btn_delete', lang)}", key=f"del_{cv_id}", type="secondary"
                ):
                    try:
                        cv_service.delete_cv(
                            cv_id=cv_id,
                            requester_id=user_id,
                            requester_role=role,
                        )
                        set_flash(t("msg_deleted", lang), "success")
                        st.rerun()
                    except Exception as exc:
                        st.error(str(exc))


def _handle_export(cv_service, cv_id: str, lang: str, tier: str) -> None:
    """Handles CV export."""
    user_id = get_user_id()
    role = get_role()
    try:
        archive_bytes = cv_service.export_cv(
            cv_id=cv_id,
            requester_id=user_id,
            requester_role=role,
            requester_tier=tier,
            export_format="pdf",
        )
        st.download_button(
            label=f"⬇️ {t('btn_download_package', lang)}",
            data=archive_bytes,
            file_name=f"cv_export_{cv_id[:8]}.zip",
            mime="application/zip",
            key=f"dl_{cv_id}",
        )
        set_flash(t("msg_exported", lang), "success")
    except Exception as exc:
        st.error(str(exc))


def main() -> None:
    """Main application entry point."""
    st.set_page_config(
        page_title="Career Architect Pro",
        page_icon="📄",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    _apply_global_css()
    init_session_state()

    ds, auth_svc, cv_svc, admin_svc, rs, ats_svc = _build_services()

    lang = get_language()

    if not is_authenticated():
        from app.ui.pages.login_page import render_login_page
        render_login_page(auth_svc)
        return

    role = get_role()
    tier = get_tier()
    name = st.session_state.get("user_name", "")

    _render_sidebar(role, tier, name, lang, rs)

    current_page = st.session_state.get("current_page", "cv_list")

    if current_page == "cv_list":
        _render_cv_list_page(cv_svc, lang, rs)

    elif current_page == "cv_builder_new":
        from app.ui.pages.cv_builder import render_cv_builder
        render_cv_builder(cv_svc, cv_dict=None)

    elif current_page == "cv_builder_edit":
        from app.ui.pages.cv_builder import render_cv_builder
        cv_id = st.session_state.get("selected_cv_id")
        user_id = get_user_id()
        if cv_id:
            cv = cv_svc.get_cv(
                cv_id=cv_id,
                requester_id=user_id,
                requester_role=role,
            )
            render_cv_builder(cv_svc, cv_dict=cv)

    elif current_page == "ats":
        from app.ui.pages.ats_page import render_ats_page
        user_id = get_user_id()
        cvs = cv_svc.list_cvs(requester_id=user_id, requester_role=role)
        render_ats_page(ats_svc, cvs)

    elif current_page == "coach":
        from app.ui.pages.coach_page import render_coach_page
        render_coach_page(cv_svc, ds)

    elif current_page == "admin":
        from app.ui.pages.admin_page import render_admin_page
        render_admin_page(admin_svc)

    else:
        _render_cv_list_page(cv_svc, lang, rs)


if __name__ == "__main__":
    main()
