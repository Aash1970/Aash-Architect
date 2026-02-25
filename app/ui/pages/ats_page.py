"""
ATS Analysis Page — Streamlit UI only.
Calls ATS service via cv_service and ats engine.
No ATS logic here. Tier gating enforced in service layer.
"""

import streamlit as st
from typing import Optional, Dict, Any

from app.i18n import t
from app.ui.state import get_language, get_role, get_tier, get_user_id, set_flash
from app.ui.components import show_flash, ats_score_display, upgrade_prompt, section_header
from app.ats.scoring_engine import score_cv_against_job
from app.tier.tier_rules import TierGateError


def render_ats_page(cv_service, cv_list: list) -> None:
    """
    Renders the ATS analysis page.

    Args:
        cv_service: CVService instance
        cv_list:    List of CV summary dicts for the user
    """
    lang = get_language()
    role = get_role()
    tier = get_tier()
    user_id = get_user_id()

    show_flash()
    section_header(t("nav_ats", lang))

    # Tier gate check
    from app.tier.tier_rules import is_feature_allowed
    if not is_feature_allowed(tier, "ats_basic"):
        upgrade_prompt("ATS Analysis", "Premium", lang)
        return

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
        "Select CV to analyse",
        list(cv_options.keys()),
        key="ats_cv_selector",
    )
    selected_cv_id = cv_options.get(selected_label)

    st.markdown(f"**{t('ats_job_description', lang)}**")
    job_description = st.text_area(
        t("ats_job_description", lang),
        height=200,
        key="ats_jd_input",
        placeholder=(
            "Paste the job description here. The more detail you provide, "
            "the more accurate your ATS score will be."
        ),
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
        if tier == "Premium":
            st.info("Premium ATS: keyword matching + completeness + format scoring.")
        elif tier == "Enterprise":
            st.success("Enterprise ATS: full analytics including seniority detection.")
        else:
            st.info("Free tier: basic completeness check only.")

    if run_clicked:
        if not job_description or len(job_description.strip()) < 20:
            st.error("Please provide a job description (at least 20 characters).")
            return

        try:
            cv = cv_service.get_cv(
                cv_id=selected_cv_id,
                requester_id=user_id,
                requester_role=role,
            )

            with st.spinner("Analysing your CV..."):
                score = score_cv_against_job(
                    cv_dict=cv,
                    job_description=job_description,
                    tier=tier,
                )

            st.markdown("---")
            st.markdown("## ATS Score Results")
            ats_score_display(score.to_dict(), lang)

            # Keywords
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"**✓ {t('ats_matched_keywords', lang)}**")
                if score.matched_keywords:
                    st.write(", ".join(score.matched_keywords))
                else:
                    st.write("None matched.")

            with col2:
                st.markdown(f"**✗ {t('ats_missing_keywords', lang)}**")
                if score.missing_keywords:
                    st.write(", ".join(score.missing_keywords[:20]))
                else:
                    st.write("All keywords matched!")

            # Recommendations
            if score.recommendations:
                st.markdown(f"### {t('ats_recommendations', lang)}")
                for rec in score.recommendations[:5]:
                    priority_icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(
                        rec.priority, "⚪"
                    )
                    with st.expander(
                        f"{priority_icon} {rec.message[:80]}...",
                        expanded=rec.priority == "high",
                    ):
                        st.write(rec.message)
                        st.caption(
                            f"Category: {rec.category} | "
                            f"Potential impact: +{rec.impact_score:.1f} points"
                        )

            # Enterprise: Advanced analytics
            if tier == "Enterprise" and score.advanced_analytics:
                st.markdown("### Enterprise Analytics")
                aa = score.advanced_analytics
                cols = st.columns(4)
                cols[0].metric("Experience (Est.)", f"{aa.get('experience_years', 0):.1f} yrs")
                cols[1].metric("CV Word Count", aa.get("cv_word_count", 0))
                cols[2].metric("Keyword Density", f"{aa.get('keyword_density_pct', 0):.2f}%")
                cols[3].metric("JD Keywords", aa.get("total_jd_keywords", 0))

        except TierGateError as tge:
            upgrade_prompt(tge.feature, tge.required_tier, lang)
        except Exception as exc:
            st.error(f"ATS analysis failed: {exc}")
