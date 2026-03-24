"""
ATS Analysis Page — Streamlit UI only.
Calls ATSService.analyse_cv() — no scoring logic here.
No tier gating logic here. No permission logic here.
All enforcement delegated to ATSService.
"""

import streamlit as st
from typing import List

from app.i18n import t
from app.ui.state import get_language, get_role, get_tier, get_user_id, set_flash
from app.ui.components import show_flash, ats_score_display, upgrade_prompt, section_header
from app.services import TierGateError
from app.services.role_service import PermissionDeniedError


def render_ats_page(cv_service, ats_service, cv_list: list) -> None:
    """
    Renders the ATS analysis page.

    Args:
        cv_service:  CVService instance
        ats_service: ATSService instance
        cv_list:     List of CV summary dicts for the user
    """
    lang = get_language()
    role = get_role()
    tier = get_tier()
    user_id = get_user_id()

    show_flash()
    section_header(t("nav_ats", lang))

    if not cv_list:
        st.info(t("no_cvs_found", lang))
        return

    # CV selector
    cv_options = {
        f"{c.get('title', 'My CV')} (v{c.get('version', 1)})": c["cv_id"]
        for c in cv_list
        if not c.get("is_deleted")
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
        placeholder=t("ats_placeholder_jd", lang),
        label_visibility="collapsed",
    )

    col_run, col_info = st.columns([1, 3])
    with col_run:
        run_clicked = st.button(
            t("btn_analyse_ats", lang),
            type="primary",
            use_container_width=True,
            key="ats_run_btn",
        )

    with col_info:
        tier_info_key = f"ats_tier_{tier.lower()}_info"
        st.info(t(tier_info_key, lang))

    if run_clicked:
        if not job_description or len(job_description.strip()) < 20:
            st.error(t("ats_err_jd_too_short", lang))
            return

        try:
            cv = cv_service.get_cv(
                cv_id=selected_cv_id,
                requester_id=user_id,
                requester_role=role,
            )

            with st.spinner(t("ats_analysing", lang)):
                score = ats_service.analyse_cv(
                    cv_dict=cv,
                    job_description=job_description,
                    tier=tier,
                    requester_role=role,
                )

            st.markdown("---")
            st.markdown(f"## {t('ats_results_title', lang)}")
            ats_score_display(score.to_dict(), lang)

            # Keywords
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"**✓ {t('ats_matched_keywords', lang)}**")
                if score.matched_keywords:
                    st.write(", ".join(score.matched_keywords))
                else:
                    st.write(t("ats_no_keywords_matched", lang))

            with col2:
                st.markdown(f"**✗ {t('ats_missing_keywords', lang)}**")
                if score.missing_keywords:
                    st.write(", ".join(score.missing_keywords[:20]))
                else:
                    st.write(t("ats_all_keywords_matched", lang))

            # Recommendations
            if score.recommendations:
                st.markdown(f"### {t('ats_recommendations', lang)}")
                priority_icons = {"high": "🔴", "medium": "🟡", "low": "🟢"}
                for rec in score.recommendations[:5]:
                    priority_icon = priority_icons.get(rec.priority, "⚪")
                    with st.expander(
                        f"{priority_icon} {rec.message[:80]}...",
                        expanded=rec.priority == "high",
                    ):
                        st.write(rec.message)
                        st.caption(
                            f"{t('ats_rec_category', lang)}: {rec.category} | "
                            f"{t('ats_rec_impact', lang)}: +{rec.impact_score:.1f} "
                            f"{t('ats_rec_impact_suffix', lang)}"
                        )

            # Enterprise: Advanced analytics
            if score.advanced_analytics:
                st.markdown(f"### {t('ats_enterprise_analytics', lang)}")
                aa = score.advanced_analytics
                cols = st.columns(4)
                cols[0].metric(t("ats_metric_experience", lang), f"{aa.get('experience_years', 0):.1f} yrs")
                cols[1].metric(t("ats_metric_word_count", lang), aa.get("cv_word_count", 0))
                cols[2].metric(t("ats_metric_keyword_density", lang), f"{aa.get('keyword_density_pct', 0):.2f}%")
                cols[3].metric(t("ats_metric_jd_keywords", lang), aa.get("total_jd_keywords", 0))

        except TierGateError as tge:
            upgrade_prompt(tge.feature, tge.required_tier, lang)
        except PermissionDeniedError:
            st.error(t("msg_permission_denied", lang))
        except Exception as exc:
            st.error(f"{t('ats_analysis_failed', lang)}: {exc}")
