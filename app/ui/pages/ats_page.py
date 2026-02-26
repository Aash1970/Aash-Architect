"""
ATS Analysis Page — Streamlit UI only.
Zero business logic. Zero scoring logic. Zero tier branching.
Calls ATSService exclusively. Handles exceptions only.
All user-visible strings via t().
"""

import streamlit as st
from typing import List, Dict, Any

from app.i18n import t
from app.ui.state import get_language, get_role, get_tier, get_user_id
from app.ui.components import show_flash, ats_score_display, upgrade_prompt, section_header
from app.tier.tier_rules import TierGateError
from app.services.role_service import PermissionDeniedError


def render_ats_page(ats_service, cv_list: List[Dict[str, Any]]) -> None:
    """
    Renders the ATS analysis page.

    Args:
        ats_service: ATSService instance
        cv_list:     List of CV summary dicts for the current user
    """
    lang = get_language()
    role = get_role()
    tier = get_tier()
    user_id = get_user_id()

    show_flash()
    section_header(t("nav_ats", lang))

    active_cvs = [c for c in cv_list if not c.get("is_deleted")]
    if not active_cvs:
        st.info(t("no_cvs_found", lang))
        return

    cv_options = {
        f"{c.get('title', t('cv_title_default', lang))} (v{c.get('version', 1)})": c["cv_id"]
        for c in active_cvs
    }

    selected_label = st.selectbox(
        t("ats_select_cv", lang),
        list(cv_options.keys()),
        key="ats_cv_selector",
    )
    selected_cv_id = cv_options.get(selected_label)

    st.markdown(f"**{t('ats_job_description', lang)}**")
    job_description = st.text_area(
        t("ats_job_description", lang),
        height=200,
        key="ats_jd_input",
        placeholder=t("ats_jd_placeholder", lang),
        label_visibility="collapsed",
    )

    run_clicked = st.button(
        t("btn_analyse_ats", lang),
        type="primary",
        key="ats_run_btn",
    )

    if run_clicked:
        try:
            with st.spinner(t("ats_analysing", lang)):
                score = ats_service.analyse_cv(
                    cv_id=selected_cv_id,
                    job_description=job_description,
                    requester_id=user_id,
                    requester_role=role,
                    requester_tier=tier,
                )

            st.markdown("---")
            st.markdown(f"## {t('ats_results_header', lang)}")
            ats_score_display(score, lang)

            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"**✓ {t('ats_matched_keywords', lang)}**")
                matched = score.get("matched_keywords", [])
                if matched:
                    st.write(", ".join(matched))
                else:
                    st.write(t("ats_no_match", lang))

            with col2:
                st.markdown(f"**✗ {t('ats_missing_keywords', lang)}**")
                missing = score.get("missing_keywords", [])
                if missing:
                    st.write(", ".join(missing[:20]))
                else:
                    st.write(t("ats_all_matched", lang))

            recommendations = score.get("recommendations", [])
            if recommendations:
                st.markdown(f"### {t('ats_recommendations', lang)}")
                for rec in recommendations[:5]:
                    priority = rec.get("priority", "low")
                    priority_icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(priority, "⚪")
                    msg = rec.get("message", "")
                    with st.expander(
                        f"{priority_icon} {msg[:80]}{'...' if len(msg) > 80 else ''}",
                        expanded=(priority == "high"),
                    ):
                        st.write(msg)
                        st.caption(
                            f"{t('ats_category', lang)}: {rec.get('category', '')} | "
                            f"{t('ats_potential_impact', lang)}: +{rec.get('impact_score', 0):.1f} pts"
                        )

            advanced = score.get("advanced_analytics")
            if advanced:
                st.markdown(f"### {t('ats_enterprise_analytics', lang)}")
                cols = st.columns(4)
                cols[0].metric(t("ats_experience_est", lang), f"{advanced.get('experience_years', 0):.1f} yrs")
                cols[1].metric(t("ats_cv_word_count", lang), advanced.get("cv_word_count", 0))
                cols[2].metric(t("ats_keyword_density", lang), f"{advanced.get('keyword_density_pct', 0):.2f}%")
                cols[3].metric(t("ats_jd_keywords", lang), advanced.get("total_jd_keywords", 0))

        except TierGateError as tge:
            upgrade_prompt(tge.feature, tge.required_tier, lang)
        except PermissionDeniedError:
            st.error(t("msg_permission_denied", lang))
        except ValueError as ve:
            st.error(str(ve))
        except Exception as exc:
            st.error(f"{t('ats_analysis_failed', lang)}: {exc}")
