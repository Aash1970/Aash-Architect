"""
Admin Panel Page — Streamlit UI only.
Admin and SystemAdmin functionality.
All operations delegated to AdminService.
Menu visibility controlled by role. No hardcoded permissions here.
"""

import streamlit as st
from typing import Dict, Any

from app.i18n import t
from app.ui.state import get_language, get_role, get_user_id, set_flash
from app.ui.components import show_flash, section_header, role_badge, tier_badge
from app.roles.permission_matrix import has_permission


def render_admin_page(admin_service) -> None:
    """Renders the admin panel. Only visible to Admin and SystemAdmin roles."""
    lang = get_language()
    role = get_role()
    user_id = get_user_id()

    show_flash()

    if not has_permission(role, "admin.panel.access"):
        st.error(t("msg_permission_denied", lang))
        return

    section_header(t("nav_admin", lang))

    # Sub-navigation based on role
    admin_tabs = [t("admin_users", lang), t("admin_metrics", lang)]
    if has_permission(role, "admin.coach.manage"):
        admin_tabs.append(t("admin_coaches", lang))
    if has_permission(role, "admin.export.reports"):
        admin_tabs.append(t("admin_reports", lang))
    if has_permission(role, "sysadmin.panel.access"):
        admin_tabs.append("⚙ " + t("nav_sysadmin", lang))

    selected_tab = st.selectbox("Section", admin_tabs, key="admin_tab")

    st.markdown("---")

    if selected_tab == t("admin_users", lang):
        _render_user_management(admin_service, role, lang)
    elif selected_tab == t("admin_metrics", lang):
        _render_metrics(admin_service, role, lang)
    elif selected_tab == t("admin_coaches", lang):
        _render_coach_management(admin_service, role, lang)
    elif selected_tab == t("admin_reports", lang):
        _render_reports(admin_service, role, lang)
    elif "sysadmin" in selected_tab.lower() or "⚙" in selected_tab:
        _render_sysadmin_panel(admin_service, role, user_id, lang)


def _render_user_management(admin_service, role: str, lang: str) -> None:
    """User list + actions."""
    st.markdown(f"### {t('admin_users', lang)}")

    users = admin_service.list_users(requester_role=role)
    if not users:
        st.info("No users found.")
        return

    # Filters
    col1, col2 = st.columns(2)
    with col1:
        role_filter = st.selectbox(
            "Filter by Role",
            ["All", "User", "Coach", "Admin", "SystemAdmin"],
            key="admin_role_filter",
        )
    with col2:
        tier_filter = st.selectbox(
            "Filter by Tier",
            ["All", "Free", "Premium", "Enterprise"],
            key="admin_tier_filter",
        )

    filtered = users
    if role_filter != "All":
        filtered = [u for u in filtered if u.get("role") == role_filter]
    if tier_filter != "All":
        filtered = [u for u in filtered if u.get("tier") == tier_filter]

    st.markdown(f"**{len(filtered)} user(s)**")

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
                status = "Active" if user.get("is_active", True) else "Inactive"
                st.write(f"Status: {status}")

            if has_permission(role, "user.change_role"):
                new_role = st.selectbox(
                    "Change Role",
                    ["User", "Coach", "Admin"],
                    index=["User", "Coach", "Admin"].index(
                        user.get("role", "User")
                    ) if user.get("role") in ["User", "Coach", "Admin"] else 0,
                    key=f"role_{user['user_id']}",
                )
                if st.button(
                    "Update Role", key=f"upd_role_{user['user_id']}"
                ):
                    try:
                        admin_service.update_user(
                            user_id=user["user_id"],
                            updates={"role": new_role},
                            requester_role=role,
                        )
                        set_flash(f"Role updated for {user.get('email', '')}", "success")
                        st.rerun()
                    except Exception as exc:
                        st.error(str(exc))

            if has_permission(role, "user.change_tier"):
                new_tier = st.selectbox(
                    "Change Tier",
                    ["Free", "Premium", "Enterprise"],
                    index=["Free", "Premium", "Enterprise"].index(
                        user.get("tier", "Free")
                    ),
                    key=f"tier_{user['user_id']}",
                )
                if st.button(
                    "Update Tier", key=f"upd_tier_{user['user_id']}"
                ):
                    try:
                        admin_service.update_user(
                            user_id=user["user_id"],
                            updates={"tier": new_tier},
                            requester_role=role,
                        )
                        set_flash(f"Tier updated for {user.get('email', '')}", "success")
                        st.rerun()
                    except Exception as exc:
                        st.error(str(exc))

            if has_permission(role, "user.deactivate") and user.get("is_active", True):
                if st.button(
                    "Deactivate", key=f"deact_{user['user_id']}", type="secondary"
                ):
                    admin_service.deactivate_user(user["user_id"], role)
                    set_flash(f"User deactivated.", "warning")
                    st.rerun()


def _render_metrics(admin_service, role: str, lang: str) -> None:
    """Platform metrics dashboard."""
    st.markdown(f"### {t('admin_metrics', lang)}")

    try:
        metrics = admin_service.get_metrics(requester_role=role)
    except Exception as exc:
        st.error(str(exc))
        return

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Users", metrics.get("total_users", 0))
    col2.metric("Total CVs", metrics.get("total_cvs", 0))
    col3.metric("Total Exports", metrics.get("total_exports", 0))

    col4, col5 = st.columns(2)
    with col4:
        st.markdown("**Users by Role**")
        for r, count in (metrics.get("users_by_role") or {}).items():
            st.write(f"{r}: {count}")
    with col5:
        st.markdown("**Users by Tier**")
        for tr, count in (metrics.get("users_by_tier") or {}).items():
            st.write(f"{tr}: {count}")


def _render_coach_management(admin_service, role: str, lang: str) -> None:
    """Coach assignment management."""
    st.markdown(f"### {t('admin_coaches', lang)}")

    coaches = admin_service.list_coaches(requester_role=role)
    if coaches:
        st.markdown(f"**{len(coaches)} coach(es) available**")
        for c in coaches:
            st.write(f"• {c.get('full_name', '?')} ({c.get('email', '')})")

    st.markdown("---")
    st.markdown("**Assign Coach to User**")

    col1, col2 = st.columns(2)
    with col1:
        user_id_input = st.text_input("User ID", key="assign_user_id")
    with col2:
        coach_id_input = st.text_input("Coach ID", key="assign_coach_id")

    if st.button("Assign Coach", type="primary"):
        if user_id_input and coach_id_input:
            try:
                admin_service.assign_coach_to_user(
                    user_id=user_id_input,
                    coach_id=coach_id_input,
                    requester_role=role,
                )
                set_flash("Coach assigned successfully.", "success")
                st.rerun()
            except Exception as exc:
                st.error(str(exc))
        else:
            st.error("Both User ID and Coach ID are required.")


def _render_reports(admin_service, role: str, lang: str) -> None:
    """Export reports."""
    st.markdown(f"### {t('admin_reports', lang)}")

    if st.button("Generate User Report", type="primary"):
        try:
            report = admin_service.export_user_report(requester_role=role)
            import json
            report_json = json.dumps(report, indent=2)
            st.download_button(
                label="Download Report (JSON)",
                data=report_json,
                file_name="user_report.json",
                mime="application/json",
            )
            st.success(f"Report generated: {len(report)} users.")
        except Exception as exc:
            st.error(str(exc))


def _render_sysadmin_panel(admin_service, role: str, user_id: str, lang: str) -> None:
    """SystemAdmin-only controls."""
    st.markdown(f"### System Administration")

    if not has_permission(role, "sysadmin.panel.access"):
        st.error(t("msg_permission_denied", lang))
        return

    # Retention policies
    if has_permission(role, "sysadmin.retention.override"):
        st.markdown("#### Retention Policies")
        policies = admin_service.list_retention_policies(requester_role=role)
        for p in policies:
            col1, col2, col3, col4 = st.columns(4)
            col1.write(f"**{p['tier']}**")
            col2.write(f"Versions: {p['cv_version_days']}d")
            col3.write(f"Deleted CVs: {p['deleted_cv_days']}d")
            col4.write(f"Exports: {p['export_log_days']}d")

    # Language control
    if has_permission(role, "sysadmin.language.control"):
        st.markdown("#### Active Languages")
        active = admin_service.get_active_languages()
        st.write(f"Currently active: {', '.join(active)}")
        all_langs = ["en", "es", "fr", "de"]
        new_selection = st.multiselect(
            "Set Active Languages",
            all_langs,
            default=active,
            key="sysadmin_lang_select",
        )
        if st.button("Update Languages"):
            try:
                updated = admin_service.set_active_languages(new_selection, role)
                set_flash(f"Active languages: {', '.join(updated)}", "success")
                st.rerun()
            except Exception as exc:
                st.error(str(exc))
