"""
Login / Registration Page — Streamlit UI only.
Calls AuthService for all auth operations.
No business logic here. All user-visible strings via t().
"""

import streamlit as st

from app.i18n import t, get_supported_languages
from app.ui.state import (
    get_language, set_authenticated_user, navigate_to,
    set_flash, is_authenticated
)
from app.ui.components import show_flash


def render_login_page(auth_service) -> None:
    """
    Renders the login/registration page.
    auth_service: AuthService instance passed from main app.
    """
    lang = get_language()

    _render_language_selector(lang)

    st.markdown(
        f"""
        <div style="text-align:center; padding:40px 0 20px 0;">
            <h1 style="color:#1E293B; font-size:2.5rem; font-weight:700;">
                {t("app_title", lang)}
            </h1>
            <p style="color:#64748B; font-size:1.1rem;">
                {t("app_subtitle", lang)}
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    show_flash()

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        tab_login, tab_register = st.tabs([
            t("btn_login", lang), t("btn_register", lang)
        ])

        with tab_login:
            _render_login_form(auth_service, lang)

        with tab_register:
            _render_register_form(auth_service, lang)


def _render_language_selector(lang: str) -> None:
    """Language selector in the top-right corner."""
    supported = get_supported_languages()
    col1, col2 = st.columns([6, 1])
    with col2:
        options = list(supported.keys())
        labels = list(supported.values())
        current_idx = options.index(lang) if lang in options else 0
        selected_label = st.selectbox(
            t("select_language", lang),
            labels,
            index=current_idx,
            key="lang_selector_login",
            label_visibility="collapsed",
        )
        selected_code = options[labels.index(selected_label)]
        if selected_code != lang:
            st.session_state["language"] = selected_code
            st.rerun()


def _render_login_form(auth_service, lang: str) -> None:
    """Login form with email and password."""
    with st.form("login_form"):
        email = st.text_input(
            t("label_email", lang),
            placeholder="your@email.com",
            key="login_email",
        )
        password = st.text_input(
            t("label_password", lang),
            type="password",
            key="login_password",
        )
        submitted = st.form_submit_button(
            t("btn_login", lang), use_container_width=True, type="primary"
        )

    if submitted:
        if not email or not password:
            st.error(t("err_required", lang))
            return

        try:
            user = auth_service.login(email.strip(), password)
            set_authenticated_user(
                user_id=user.user_id,
                email=user.email,
                role=user.role,
                tier=user.tier,
                name=user.full_name,
                access_token=user.access_token or "",
                language=user.language,
            )
            navigate_to("cv_list")
            set_flash(t("msg_login_success", lang), "success")
            st.rerun()
        except Exception:
            st.error(t("msg_login_failed", lang))


def _render_register_form(auth_service, lang: str) -> None:
    """Registration form."""
    with st.form("register_form"):
        full_name = st.text_input(
            t("label_full_name", lang),
            placeholder="Jane Doe",
            key="reg_name",
        )
        email = st.text_input(
            t("label_email", lang),
            placeholder="your@email.com",
            key="reg_email",
        )
        password = st.text_input(
            t("label_password", lang),
            type="password",
            key="reg_password",
        )
        submitted = st.form_submit_button(
            t("btn_register", lang), use_container_width=True, type="primary"
        )

    if submitted:
        errors = []
        if not full_name or len(full_name.strip()) < 2:
            errors.append(f"{t('label_full_name', lang)}: {t('err_min_length', lang, min=2)}")
        if not email:
            errors.append(f"{t('label_email', lang)}: {t('err_required', lang)}")
        if not password or len(password) < 8:
            errors.append(
                f"{t('label_password', lang)}: {t('err_password_min_length', lang)}"
            )

        if errors:
            for e in errors:
                st.error(e)
            return

        try:
            auth_service.register(
                email=email.strip(),
                password=password,
                full_name=full_name.strip(),
            )
            set_flash(t("msg_register_success", lang), "success")
            st.rerun()
        except Exception as exc:
            st.error(str(exc))
