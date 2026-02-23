from __future__ import annotations
import streamlit as st
from db.client import get_client
from db.roles import list_all_users, update_user_role, VALID_ROLES
from db.feature_flags import fetch_feature_flags, update_flag, set_user_override


# ── DB helpers ────────────────────────────────────────────────

def _get_all_ats_results(limit: int = 100) -> list[dict]:
    try:
        result = (
            get_client()
            .table("ats_results")
            .select("user_id, level, job_title, score, created_at")
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        return result.data or []
    except Exception:
        return []


def _get_all_export_audit(limit: int = 100) -> list[dict]:
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


def _get_table_counts() -> dict:
    counts: dict[str, int] = {}
    for table in ("user_roles", "cvs", "reflections", "ats_results", "export_audit",
                  "feature_flags", "user_feature_overrides", "coach_assignments"):
        try:
            r = get_client().table(table).select("id", count="exact").execute()
            counts[table] = r.count or 0
        except Exception:
            counts[table] = -1
    return counts


# ── Main render ───────────────────────────────────────────────

def render_sysadmin_console(user_id: str, flags: dict) -> None:
    st.header("System Admin Console")
    st.caption("Full system access — changes affect all users immediately.")

    tab_health, tab_flags, tab_roles, tab_ats, tab_audit = st.tabs([
        "System Health", "Feature Flags", "Role Management", "ATS Data", "Full Audit"
    ])

    # ── System health ─────────────────────────────────────────
    with tab_health:
        st.subheader("Database Table Counts")
        counts = _get_table_counts()
        cols   = st.columns(4)
        for i, (table, count) in enumerate(counts.items()):
            label = table.replace("_", " ").title()
            cols[i % 4].metric(label, count if count >= 0 else "Error")

        st.divider()
        st.subheader("Platform Constants")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**App Version:** v2.0.0 — Enterprise")
            st.markdown("**Auth Provider:** Supabase Email/Password")
            st.markdown("**Encryption:** Fernet / PBKDF2-HMAC-SHA256")
        with col2:
            st.markdown("**RLS Status:** Enabled on all tables")
            st.markdown("**Role Hierarchy:** User → Coach → Admin → SystemAdmin")
            st.markdown("**Feature Flags:** DB-driven with per-user overrides")

    # ── Feature flags ─────────────────────────────────────────
    with tab_flags:
        st.subheader("Global Feature Flag Management")
        st.warning("Changes take effect on next page load for each user.")

        flags_data = fetch_feature_flags()

        for flag_name, cfg in flags_data.items():
            with st.expander(
                f"{flag_name.replace('_',' ').title()} — {'✅ Enabled' if cfg['enabled'] else '❌ Disabled'}",
                expanded=False,
            ):
                col1, col2 = st.columns(2)
                with col1:
                    new_state = st.toggle(
                        "Enabled",
                        value=cfg["enabled"],
                        key=f"sysadmin_flag_{flag_name}",
                    )
                with col2:
                    st.markdown(f"**Minimum Role:** `{cfg['min_role']}`")

                if new_state != cfg["enabled"]:
                    if update_flag(flag_name, new_state):
                        st.success(f"'{flag_name}' {'enabled' if new_state else 'disabled'}.")
                        st.rerun()
                    else:
                        st.error("Update failed.")

    # ── Role management ───────────────────────────────────────
    with tab_roles:
        st.subheader("User Role Management")
        users  = list_all_users()
        search = st.text_input("Filter by email", key="sysadmin_role_search")

        filtered = (
            [u for u in users if search.lower() in (u.get("email") or "").lower()]
            if search else users
        )

        if not filtered:
            st.info("No users found.")
        else:
            for u in filtered:
                col1, col2, col3 = st.columns([3, 2, 2])
                with col1:
                    st.markdown(u.get("email") or u.get("user_id", "—"))
                with col2:
                    current = u.get("role", "User")
                    new_role = st.selectbox(
                        "",
                        VALID_ROLES,
                        index=VALID_ROLES.index(current) if current in VALID_ROLES else 0,
                        key=f"sysadmin_role_{u['user_id']}",
                        label_visibility="collapsed",
                    )
                with col3:
                    if new_role != current:
                        if st.button("Apply", key=f"sysadmin_apply_{u['user_id']}"):
                            if update_user_role(u["user_id"], new_role):
                                st.success(f"Updated to {new_role}.")
                                st.rerun()
                            else:
                                st.error("Failed.")
                    else:
                        st.markdown(
                            f'<span style="color:#94A3B8;font-size:0.8em;">no change</span>',
                            unsafe_allow_html=True,
                        )

    # ── ATS data ──────────────────────────────────────────────
    with tab_ats:
        st.subheader("All ATS Results")
        results = _get_all_ats_results()

        if not results:
            st.info("No ATS results recorded.")
        else:
            scores = [r["score"] for r in results]
            col1, col2, col3 = st.columns(3)
            col1.metric("Total Scans",  len(results))
            col2.metric("Avg Score",    f"{sum(scores)/len(scores):.1f}")
            col3.metric("Highest",      f"{max(scores):.1f}")

            st.divider()
            for r in results:
                score  = r.get("score", 0)
                colour = "#22c55e" if score >= 75 else "#f59e0b" if score >= 50 else "#ef4444"
                st.markdown(
                    f'<div style="background:#F8FAFC;border:1px solid #E2E8F0;'
                    f'padding:8px 14px;border-radius:4px;margin-bottom:6px;'
                    f'display:flex;justify-content:space-between;font-size:0.85em;">'
                    f'<span>L{r.get("level")} — {r.get("job_title","—")}</span>'
                    f'<span style="color:{colour};font-weight:700;">{score:.1f}</span>'
                    f'<span style="color:#94A3B8;">{(r.get("created_at") or "")[:10]}</span>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

    # ── Full audit ────────────────────────────────────────────
    with tab_audit:
        st.subheader("Full Export Audit Log")
        audits = _get_all_export_audit()

        if not audits:
            st.info("No exports recorded.")
        else:
            st.caption(f"{len(audits)} records (most recent first)")
            for a in audits:
                st.markdown(
                    f'<div style="background:#F8FAFC;border:1px solid #E2E8F0;'
                    f'padding:8px 14px;border-radius:4px;margin-bottom:4px;font-size:0.82em;">'
                    f'<code>{(a.get("user_id") or "")[:8]}…</code> &nbsp;·&nbsp; '
                    f'<strong>{a.get("export_type","—")}</strong> &nbsp;·&nbsp; '
                    f'{(a.get("exported_at") or "")[:16]} &nbsp;·&nbsp; '
                    f'<code>{(a.get("file_checksum") or "")[:16]}…</code>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
