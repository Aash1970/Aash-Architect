"""
Shared UI Components — Streamlit only.
Reusable UI building blocks. No business logic here.
All display strings loaded via i18n.t().
"""

import streamlit as st
from typing import Optional, Dict, Any, List

from app.i18n import t
from app.ui.state import get_language, consume_flash


def show_flash() -> None:
    """Displays and clears any pending flash message."""
    flash = consume_flash()
    if not flash:
        return
    msg = flash["message"]
    ft = flash["type"]
    if ft == "success":
        st.success(msg)
    elif ft == "error":
        st.error(msg)
    elif ft == "warning":
        st.warning(msg)
    else:
        st.info(msg)


def show_validation_errors(errors: Dict[str, List[str]]) -> None:
    """Displays a validation error block."""
    lang = get_language()
    st.error(t("msg_validation_error", lang))
    for field, msgs in errors.items():
        for m in msgs:
            st.error(f"• {m}")


def tier_badge(tier: str) -> None:
    """Renders a styled tier badge."""
    colors = {
        "Free": "#6B7280",
        "Premium": "#7C3AED",
        "Enterprise": "#059669",
    }
    color = colors.get(tier, "#6B7280")
    st.markdown(
        f'<span style="background:{color}; color:white; padding:2px 10px; '
        f'border-radius:12px; font-size:12px; font-weight:600;">{tier}</span>',
        unsafe_allow_html=True,
    )


def role_badge(role: str) -> None:
    """Renders a styled role badge."""
    colors = {
        "User": "#3B82F6",
        "Coach": "#F59E0B",
        "Admin": "#EF4444",
        "SystemAdmin": "#1F2937",
    }
    color = colors.get(role, "#3B82F6")
    st.markdown(
        f'<span style="background:{color}; color:white; padding:2px 10px; '
        f'border-radius:12px; font-size:12px; font-weight:600;">{role}</span>',
        unsafe_allow_html=True,
    )


def section_header(title: str, divider: bool = True) -> None:
    """Renders a consistent section header."""
    st.markdown(f"### {title}")
    if divider:
        st.divider()


def ats_score_display(score_dict: Dict[str, Any], lang: str = "en") -> None:
    """Renders an ATS score result card."""
    overall = score_dict.get("overall_score", 0)
    grade = "A" if overall >= 85 else "B" if overall >= 70 else "C" if overall >= 55 else "D" if overall >= 40 else "F"
    color = "#059669" if overall >= 70 else "#D97706" if overall >= 40 else "#DC2626"

    st.markdown(
        f"""
        <div style="background:#F8FAFC; border:1px solid #E2E8F0; border-radius:12px;
                    padding:20px; margin:10px 0;">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <div>
                    <h2 style="color:{color}; margin:0;">{overall:.1f}/100</h2>
                    <p style="color:#64748B; margin:0;">Grade: {grade}</p>
                </div>
                <div style="text-align:right;">
                    <p style="color:#64748B; margin:0;">{t("ats_match_rate", lang)}</p>
                    <h3 style="color:{color}; margin:0;">
                        {score_dict.get("keyword_match_rate", 0):.1f}%
                    </h3>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns(2)
    with col1:
        st.metric(t("ats_score", lang), f"{overall:.1f}")
        st.metric("Completeness", f"{score_dict.get('completeness_score', 0):.1f}%")
    with col2:
        st.metric("Format Score", f"{score_dict.get('format_score', 0):.1f}%")
        matched = len(score_dict.get("matched_keywords", []))
        missing = len(score_dict.get("missing_keywords", []))
        st.metric("Keywords", f"{matched} matched / {missing} missing")


def upgrade_prompt(feature_name: str, required_tier: str, lang: str = "en") -> None:
    """Renders a tier upgrade prompt."""
    st.warning(
        f"⭐ **{t('tier_upgrade_required', lang)}**: "
        f"**{feature_name}** requires the **{required_tier}** tier. "
        f"{t('tier_upgrade_message', lang)}"
    )


def confirm_dialog(label: str, key: str, lang: str = "en") -> bool:
    """Renders a confirm/cancel pair. Returns True if confirmed."""
    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button(f"✓ {t('yes_delete', lang)}", key=f"confirm_{key}", type="primary"):
            return True
    with col2:
        if st.button(t("keep", lang), key=f"cancel_{key}"):
            return False
    return False
