from __future__ import annotations
import streamlit as st
from db.client import get_client
from db.roles import list_all_users, update_user_role, VALID_ROLES
from db.feature_flags import fetch_feature_flags, set_user_override


# ── DB helpers ────────────────────────────────────────────────

def _get_export_audit(limit: int = 50) -> list[dict]:
    try:
        result = (
            get_client()
            .table("export_audit")
            .select("user_id, export_type, file_checksum, exported_at")
            .order("exported_at", desc=True)
            .limit(limit)
            .execute()
        )
        return result.data or []
    except Exception:
        return []


def _get_ats_summary() -> dict:
    try:
        result = (
            get_client()
            .table("ats_results")
            .select("level, score")
            .execute()
        )
        rows = result.data or []
        if not rows:
            return {"count": 0, "avg": 0.0}
        scores = [r["score"] for r in rows]
        return {"count": len(scores), "avg": round(sum(scores) / len(scores), 1)}
    except Exception:
        return {"count": 0, "avg": 0.0}


def _get_reflection_count() -> int:
    try:
        result = get_client().table("reflections").select("id", count="exact").execute()
        return result.count or 0
    except Exception:
        return 0


def _get_cv_count() -> int:
    try:
        result = get_client().table("cvs").select("id", count="exact").execute()
        return result.count or 0
    except Exception:
        return 0


def _assign_coach(coach_id: str, user_id: str) -> bool:
    try:
        get_client().table("coach_assignments").upsert(
            {"coach_id": coach_id, "user_id": user_id},
            on_conflict="coach_id,user_id",
        ).execute()
        return True
    except Exception:
        return False


# ── Main render ───────────────────────────────────────────────

def render_admin_console(user_id: str, role: str, flags: dict) -> None:
    st.header("Admin Console")

    tab_overview, tab_users, tab_flags, tab_audit = st.tabs([
        "Overview", "User Management", "Feature Flags", "Export Audit"
    ])

    # ── Overview ──────────────────────────────────────────────
    with tab_overview:
        st.subheader("Platform Metrics")

        users      = list_all_users()
        ats_data   = _get_ats_summary()
        refl_count = _get_reflection_count()
        cv_count   = _get_cv_count()

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Users",       len(users))
        col2.metric("CVs Saved",         cv_count)
        col3.metric("ATS Scans",         ats_data["count"])
        col4.metric("Avg ATS Score",     f"{ats_data['avg']:.1f}")

        col5, col6 = st.columns(4)[:2]
        col5.metric("Reflections",       refl_count)

        if users:
            role_dist: dict[str, int] = {}
            for u in users:
                r = u.get("role", "User")
                role_dist[r] = role_dist.get(r, 0) + 1

            st.subheader("Role Distribution")
            for r, count in sorted(role_dist.items()):
                pct = count / len(users) * 100
                st.markdown(
                    f'<div style="margin-bottom:6px;">'
                    f'<div style="display:flex;justify-content:space-between;font-size:0.85em;">'
                    f'<span>{r}</span><span style="font-weight:700;">{count} ({pct:.0f}%)</span></div>'
                    f'<div style="background:#E2E8F0;border-radius:4px;height:6px;">'
                    f'<div style="background:#6366F1;width:{pct}%;height:6px;border-radius:4px;"></div>'
                    f'</div></div>',
                    unsafe_allow_html=True,
                )

    # ── User management ───────────────────────────────────────
    with tab_users:
        st.subheader("All Users")
        users = list_all_users()

        if not users:
            st.info("No users found.")
        else:
            search = st.text_input("Filter by email", key="admin_user_search")
            filtered = [u for u in users if search.lower() in (u.get("email") or "").lower()] if search else users

            for u in filtered:
                with st.expander(
                    f"{u.get('email') or u.get('user_id','—')}  ·  {u.get('role','User')}",
                    expanded=False,
                ):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown(f"**User ID:** `{u.get('user_id','')}`")
                        st.markdown(f"**Joined:** {(u.get('created_at') or '')[:10]}")
                    with col2:
                        current_role = u.get("role", "User")
                        # Admins cannot promote to/from SystemAdmin
                        available = [r for r in VALID_ROLES if r != "SystemAdmin"] if role == "Admin" else list(VALID_ROLES)
                        if current_role not in available:
                            st.markdown(f"**Role:** {current_role} *(read-only)*")
                        else:
                            new_role = st.selectbox(
                                "Role",
                                available,
                                index=available.index(current_role),
                                key=f"admin_role_{u['user_id']}",
                            )
                            if new_role != current_role:
                                if st.button("Update Role", key=f"admin_update_{u['user_id']}"):
                                    if update_user_role(u["user_id"], new_role):
                                        st.success(f"Role updated to {new_role}.")
                                        st.rerun()
                                    else:
                                        st.error("Update failed.")

                    st.markdown("**Per-User Feature Overrides**")
                    current_flags = fetch_feature_flags(u["user_id"])
                    flag_options  = [f for f in current_flags.keys() if not f.endswith("_dashboard") and f != "system_config"]
                    for flag in flag_options:
                        cfg     = current_flags[flag]
                        enabled = cfg.get("enabled", True)
                        toggled = st.checkbox(
                            f"{flag.replace('_',' ').title()}",
                            value=enabled,
                            key=f"flag_override_{u['user_id']}_{flag}",
                        )
                        if toggled != enabled:
                            set_user_override(u["user_id"], flag, toggled)

    # ── Feature flags ─────────────────────────────────────────
    with tab_flags:
        st.subheader("Global Feature Flags")
        st.caption("Changes apply to all users (overridden by per-user settings).")

        if role != "SystemAdmin":
            st.info("SystemAdmin access required to modify global feature flags. You can set per-user overrides in User Management.")
        else:
            flags_data = fetch_feature_flags()
            for flag_name, cfg in flags_data.items():
                col1, col2, col3 = st.columns([3, 1, 2])
                with col1:
                    st.markdown(f"**{flag_name.replace('_',' ').title()}**")
                with col2:
                    st.markdown(
                        f'<span style="color:{"#22c55e" if cfg["enabled"] else "#ef4444"};">'
                        f'{"Enabled" if cfg["enabled"] else "Disabled"}</span>',
                        unsafe_allow_html=True,
                    )
                with col3:
                    st.markdown(f"Min role: `{cfg['min_role']}`")

    # ── Export audit ──────────────────────────────────────────
    with tab_audit:
        st.subheader("Export Audit Log")
        audits = _get_export_audit()

        if not audits:
            st.info("No exports recorded yet.")
        else:
            for a in audits:
                st.markdown(
                    f'<div style="background:#F8FAFC;border:1px solid #E2E8F0;'
                    f'padding:8px 14px;border-radius:4px;margin-bottom:6px;font-size:0.85em;">'
                    f'<strong>{a.get("export_type","—")}</strong> &nbsp;·&nbsp; '
                    f'{(a.get("exported_at") or "")[:16]} &nbsp;·&nbsp; '
                    f'checksum: <code>{(a.get("file_checksum") or "")[:12]}…</code></div>',
                    unsafe_allow_html=True,
                )
