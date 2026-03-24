"""
Admin Panel Page — Streamlit UI only.
Admin and SystemAdmin functionality.
All operations delegated to AdminService.
All permission checks delegated to RoleService — no has_permission imports here.
Menu visibility driven by role_service.check_permission().
"""

import streamlit as st
from typing import Dict, Any

from app.i18n import t
from app.ui.state import get_language, get_role, get_user_id, set_flash
from app.ui.components import show_flash, section_header, role_badge, tier_badge


def render_admin_page(admin_service, role_service) -> None:
    """Renders the admin panel. Services enforce access; UI only renders."""
    lang = get_language()
    role = get_role()
    user_id = get_user_id()

    show_flash()
    section_header(t("nav_admin", lang))

    # Sub-navigation based on role — display decisions only, enforcement in service
    admin_tabs = [t("admin_users", lang), t("admin_metrics", lang)]
    if role_service.check_permission(role, "admin.coach.manage"):
        admin_tabs.append(t("admin_coaches", lang))
    if role_service.check_permission(role, "admin.export.reports"):
        admin_tabs.append(t("admin_reports", lang))
    if role_service.check_permission(role, "sysadmin.panel.access"):
        admin_tabs.append("⚙ " + t("nav_sysadmin", lang))

    selected_tab = st.selectbox(t("admin_section", lang), admin_tabs, key="admin_tab")

    st.markdown("---")

    if selected_tab == t("admin_users", lang):
        _render_user_management(admin_service, role_service, role, lang)
    elif selected_tab == t("admin_metrics", lang):
        _render_metrics(admin_service, role, lang)
    elif selected_tab == t("admin_coaches", lang):
        _render_coach_management(admin_service, role, lang)
    elif selected_tab == t("admin_reports", lang):
        _render_reports(admin_service, role, lang)
    elif "sysadmin" in selected_tab.lower() or "⚙" in selected_tab:
        _render_sysadmin_panel(admin_service, role_service, role, user_id, lang)


def _render_user_management(admin_service, role_service, role: str, lang: str) -> None:
    """User list + actions."""
    st.markdown(f"### {t('admin_users', lang)}")

    try:
        users = admin_service.list_users(requester_role=role)
    except Exception as exc:
        st.error(str(exc))
        return

    if not users:
        st.info(t("admin_no_users", lang))
        return

    # Filters
    all_label = t("admin_all", lang)
    col1, col2 = st.columns(2)
    with col1:
        role_filter = st.selectbox(
            t("admin_filter_role", lang),
            [all_label, "User", "Coach", "Admin", "SystemAdmin"],
            key="admin_role_filter",
        )
    with col2:
        tier_filter = st.selectbox(
            t("admin_filter_tier", lang),
            [all_label, "Free", "Premium", "Enterprise"],
            key="admin_tier_filter",
        )

    filtered = users
    if role_filter != all_label:
        filtered = [u for u in filtered if u.get("role") == role_filter]
    if tier_filter != all_label:
        filtered = [u for u in filtered if u.get("tier") == tier_filter]

    st.markdown(f"**{t('admin_user_count', lang, count=len(filtered))}**")

    for user in filtered:
        with st.expander(
            f"{user.get('full_name', '?')} ({user.get('email', '')})",
            expanded=False,
        ):
            col1, col2, col3 = st.columns(3)
            with col1:
                role_badge(user.get("role", "User"))
            with col2:
                tier_badge(user.get("tier", "Free"))
            with col3:
                is_active = user.get("is_active", True)
                status_key = "admin_status_active" if is_active else "admin_status_inactive"
                st.write(f"{t('admin_status_label', lang)}: {t(status_key, lang)}")

            if role_service.check_permission(role, "user.change_role"):
                new_role = st.selectbox(
                    t("admin_change_role", lang),
                    ["User", "Coach", "Admin"],
                    index=["User", "Coach", "Admin"].index(
                        user.get("role", "User")
                    ) if user.get("role") in ["User", "Coach", "Admin"] else 0,
                    key=f"role_{user['user_id']}",
                )
                if st.button(
                    t("admin_update_role", lang), key=f"upd_role_{user['user_id']}"
                ):
                    try:
                        admin_service.update_user(
                            user_id=user["user_id"],
                            updates={"role": new_role},
                            requester_role=role,
                        )
                        set_flash(f"{t('admin_role_updated', lang)}: {user.get('email', '')}", "success")
                        st.rerun()
                    except Exception as exc:
                        st.error(str(exc))

            if role_service.check_permission(role, "user.change_tier"):
                new_tier = st.selectbox(
                    t("admin_change_tier", lang),
                    ["Free", "Premium", "Enterprise"],
                    index=["Free", "Premium", "Enterprise"].index(
                        user.get("tier", "Free")
                    ),
                    key=f"tier_{user['user_id']}",
                )
                if st.button(
                    t("admin_update_tier", lang), key=f"upd_tier_{user['user_id']}"
                ):
                    try:
                        admin_service.update_user(
                            user_id=user["user_id"],
                            updates={"tier": new_tier},
                            requester_role=role,
                        )
                        set_flash(f"{t('admin_tier_updated', lang)}: {user.get('email', '')}", "success")
                        st.rerun()
                    except Exception as exc:
                        st.error(str(exc))

            if role_service.check_permission(role, "user.deactivate") and user.get("is_active", True):
                if st.button(
                    t("admin_deactivate", lang), key=f"deact_{user['user_id']}", type="secondary"
                ):
                    try:
                        admin_service.deactivate_user(user["user_id"], role)
                        set_flash(t("admin_user_deactivated", lang), "warning")
                        st.rerun()
                    except Exception as exc:
                        st.error(str(exc))


def _render_metrics(admin_service, role: str, lang: str) -> None:
    """Platform metrics dashboard."""
    st.markdown(f"### {t('admin_metrics', lang)}")

    try:
        metrics = admin_service.get_metrics(requester_role=role)
    except Exception as exc:
        st.error(str(exc))
        return

    col1, col2, col3 = st.columns(3)
    col1.metric(t("admin_total_users", lang), metrics.get("total_users", 0))
    col2.metric(t("admin_total_cvs", lang), metrics.get("total_cvs", 0))
    col3.metric(t("admin_total_exports", lang), metrics.get("total_exports", 0))

    col4, col5 = st.columns(2)
    with col4:
        st.markdown(f"**{t('admin_users_by_role', lang)}**")
        for r, count in (metrics.get("users_by_role") or {}).items():
            st.write(f"{r}: {count}")
    with col5:
        st.markdown(f"**{t('admin_users_by_tier', lang)}**")
        for tr, count in (metrics.get("users_by_tier") or {}).items():
            st.write(f"{tr}: {count}")


def _render_coach_management(admin_service, role: str, lang: str) -> None:
    """Coach assignment management."""
    st.markdown(f"### {t('admin_coaches', lang)}")

    try:
        coaches = admin_service.list_coaches(requester_role=role)
    except Exception as exc:
        st.error(str(exc))
        return

    if coaches:
        st.markdown(f"**{t('admin_coaches_available', lang, count=len(coaches))}**")
        for c in coaches:
            st.write(f"• {c.get('full_name', '?')} ({c.get('email', '')})")

    st.markdown("---")
    st.markdown(f"**{t('admin_assign_coach_title', lang)}**")

    col1, col2 = st.columns(2)
    with col1:
        user_id_input = st.text_input(t("admin_label_user_id", lang), key="assign_user_id")
    with col2:
        coach_id_input = st.text_input(t("admin_label_coach_id", lang), key="assign_coach_id")

    if st.button(t("admin_btn_assign_coach", lang), type="primary"):
        if user_id_input and coach_id_input:
            try:
                admin_service.assign_coach_to_user(
                    user_id=user_id_input,
                    coach_id=coach_id_input,
                    requester_role=role,
                )
                set_flash(t("admin_coach_assigned", lang), "success")
                st.rerun()
            except Exception as exc:
                st.error(str(exc))
        else:
            st.error(t("admin_err_assign_required", lang))


def _render_reports(admin_service, role: str, lang: str) -> None:
    """Export reports."""
    st.markdown(f"### {t('admin_reports', lang)}")

    if st.button(t("admin_btn_generate_report", lang), type="primary"):
        try:
            report = admin_service.export_user_report(requester_role=role)
            import json
            report_json = json.dumps(report, indent=2)
            st.download_button(
                label=t("admin_btn_download_report", lang),
                data=report_json,
                file_name="user_report.json",
                mime="application/json",
            )
            st.success(f"{t('admin_report_generated', lang)}: {len(report)}")
        except Exception as exc:
            st.error(str(exc))


def _render_sysadmin_panel(admin_service, role_service, role: str, user_id: str, lang: str) -> None:
    """SystemAdmin-only controls. Service enforces access."""
    st.markdown(f"### {t('admin_sysadmin_title', lang)}")

    # Retention policies
    if role_service.check_permission(role, "sysadmin.retention.override"):
        st.markdown(f"#### {t('admin_retention_policies', lang)}")
        try:
            policies = admin_service.list_retention_policies(requester_role=role)
            for p in policies:
                col1, col2, col3, col4 = st.columns(4)
                col1.write(f"**{p['tier']}**")
                col2.write(f"{t('admin_versions_days', lang)}: {p['cv_version_days']}d")
                col3.write(f"{t('admin_deleted_cvs_days', lang)}: {p['deleted_cv_days']}d")
                col4.write(f"{t('admin_exports_days', lang)}: {p['export_log_days']}d")
        except Exception as exc:
            st.error(str(exc))

    # Language control
    if role_service.check_permission(role, "sysadmin.language.control"):
        st.markdown(f"#### {t('admin_active_languages', lang)}")
        try:
            active = admin_service.get_active_languages()
            st.write(f"{t('admin_currently_active', lang)}: {', '.join(active)}")
            all_langs = ["en", "es", "fr", "de"]
            new_selection = st.multiselect(
                t("admin_set_active_languages", lang),
                all_langs,
                default=active,
                key="sysadmin_lang_select",
            )
            if st.button(t("admin_btn_update_languages", lang)):
                try:
                    updated = admin_service.set_active_languages(new_selection, role)
                    set_flash(f"{t('admin_active_languages', lang)}: {', '.join(updated)}", "success")
                    st.rerun()
                except Exception as exc:
                    st.error(str(exc))
        except Exception as exc:
            st.error(str(exc))
