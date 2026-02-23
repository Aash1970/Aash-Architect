import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import streamlit as st
from db.client import get_client
from db.roles import fetch_user_role
from db.feature_flags import fetch_feature_flags

# ==============================================================
# CONSTANTS
# ==============================================================
APP_TITLE  = "CAREER ARCHITECT PRO"
VERSION    = "v2.0.0 — ENTERPRISE"
COPYRIGHT  = "© 2026 Career Architect"

# ==============================================================
# ROLE HIERARCHY
# ==============================================================
ROLE_HIERARCHY = {
    "User":        1,
    "Coach":       2,
    "Admin":       3,
    "SystemAdmin": 4,
}


def role_gte(role_a: str, role_b: str) -> bool:
    """True if role_a has equal or higher permissions than role_b."""
    return ROLE_HIERARCHY.get(role_a, 0) >= ROLE_HIERARCHY.get(role_b, 0)


# ==============================================================
# SESSION STATE
# ==============================================================

def _init_state() -> None:
    defaults = {
        "auth":           False,
        "current_user":   None,   # email
        "user_id":        None,   # Supabase UUID
        "user_role":      "User",
        "access_token":   None,
        "refresh_token":  None,
        "flags":          None,
        "role_fetched":   False,
        "login_attempts": 0,
        "page":           "cv_builder",
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


_init_state()

# ==============================================================
# PAGE CONFIG & CSS
# ==============================================================

st.set_page_config(page_title=f"{APP_TITLE} | {VERSION}", layout="wide")

st.markdown("""
<style>
/* ── CORE PALETTE ──────────────────────────────────────────── */
.stApp { background-color: #F8FAFC !important; color: #1E293B !important; }

[data-testid="stSidebar"] {
    background-color: #0F172A !important;
    border-right: 2px solid #4F46E5 !important;
    overflow: hidden !important;
}

/* ── TYPOGRAPHY ─────────────────────────────────────────────  */
html, body, [class*="css"] {
    font-family: 'Segoe UI', system-ui, -apple-system, sans-serif !important;
}
*, p, span, div, label, h1, h2, h3, h4, h5, h6, li {
    font-family: 'Segoe UI', system-ui, -apple-system, sans-serif !important;
    color: #1E293B !important;
}

/* ── SIDEBAR TEXT ────────────────────────────────────────────  */
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] span,
[data-testid="stSidebar"] div,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3,
[data-testid="stSidebar"] h4,
[data-testid="stSidebar"] li,
[data-testid="stSidebar"] a,
[data-testid="stSidebar"] small,
[data-testid="stSidebar"] .stMarkdown {
    color: #E2E8F0 !important;
}

/* ── SIDEBAR ICON OVERFLOW FIX ───────────────────────────────  */
[data-testid="stSidebar"] svg,
[data-testid="stSidebar"] [data-testid="stIconMaterial"],
[data-testid="stSidebar"] button svg {
    max-width: 20px !important;
    max-height: 20px !important;
    overflow: hidden !important;
    flex-shrink: 0 !important;
}

/* ── BUTTONS ─────────────────────────────────────────────────  */
div.stButton > button {
    background-color: #4F46E5 !important;
    color: #ffffff !important;
    border: none !important;
    font-weight: 600 !important;
    width: 100% !important;
    border-radius: 6px !important;
    height: 2.8em !important;
    letter-spacing: 0.3px;
    transition: background-color 0.15s ease;
}
div.stButton > button:hover {
    background-color: #4338CA !important;
    color: #ffffff !important;
}
div.stButton > button:active,
div.stButton > button:focus {
    background-color: #3730A3 !important;
    color: #ffffff !important;
    box-shadow: none !important;
    outline: none !important;
}

/* ── FORM SUBMIT ─────────────────────────────────────────────  */
div.stFormSubmitButton > button {
    background-color: #4F46E5 !important;
    color: #ffffff !important;
    border: none !important;
    font-weight: 600 !important;
    border-radius: 6px !important;
}
div.stFormSubmitButton > button:hover {
    background-color: #4338CA !important;
}

/* ── INPUTS ──────────────────────────────────────────────────  */
input, textarea,
[data-baseweb="input"] input,
[data-baseweb="textarea"] textarea {
    background-color: #ffffff !important;
    color: #1E293B !important;
    border: 1px solid #CBD5E1 !important;
    border-radius: 5px !important;
}
input:focus, textarea:focus {
    border-color: #4F46E5 !important;
    box-shadow: 0 0 0 2px rgba(79,70,229,0.15) !important;
}

/* ── SELECTBOX ───────────────────────────────────────────────  */
[data-baseweb="select"] > div,
[data-baseweb="select"] div,
[data-baseweb="popover"] {
    background-color: #ffffff !important;
    color: #1E293B !important;
    border: 1px solid #CBD5E1 !important;
}

/* ── TABS ────────────────────────────────────────────────────  */
[data-baseweb="tab-list"] {
    background-color: #F1F5F9 !important;
    border-radius: 8px !important;
    padding: 4px !important;
}
[data-baseweb="tab"] { border-radius: 6px !important; color: #64748B !important; }
[aria-selected="true"][data-baseweb="tab"] {
    background-color: #ffffff !important;
    color: #4F46E5 !important;
    font-weight: 600 !important;
}

/* ── METRICS ─────────────────────────────────────────────────  */
[data-testid="stMetric"] label { color: #64748B !important; font-size: 0.82em !important; }
[data-testid="stMetricValue"] { color: #1E293B !important; font-weight: 700 !important; }

/* ── ALERTS ──────────────────────────────────────────────────  */
[data-testid="stAlert"] {
    background-color: #EEF2FF !important;
    border: 1px solid #6366F1 !important;
    color: #1E293B !important;
    border-radius: 6px !important;
}

/* ── EXPANDER ────────────────────────────────────────────────  */
[data-testid="stExpander"] {
    border: 1px solid #E2E8F0 !important;
    border-radius: 6px !important;
}

/* ── SCROLLBAR ───────────────────────────────────────────────  */
::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: #F1F5F9; }
::-webkit-scrollbar-thumb { background: #94A3B8; border-radius: 4px; }
::-webkit-scrollbar-thumb:hover { background: #4F46E5; }
</style>
""", unsafe_allow_html=True)

# ==============================================================
# SUPABASE SESSION RESTORE
# ==============================================================

def _restore_session() -> bool:
    """Re-authenticate the Supabase client from stored tokens each rerun."""
    if not st.session_state.access_token or not st.session_state.refresh_token:
        return False
    try:
        get_client().auth.set_session(
            st.session_state.access_token,
            st.session_state.refresh_token,
        )
        return True
    except Exception:
        return False


# ==============================================================
# SPLASH SCREEN / AUTHENTICATION GATE
# ==============================================================

if not st.session_state.auth:
    st.markdown(
        '<h1 style="text-align:center;color:#4F46E5;font-family:Segoe UI,sans-serif;'
        'font-weight:700;margin-top:32px;">&#127963; Career Architect Pro</h1>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<p style="text-align:center;color:#64748B;">'
        f'{VERSION} &nbsp;|&nbsp; {COPYRIGHT}</p>',
        unsafe_allow_html=True,
    )
    st.markdown("---")

    col_l, col_c, col_r = st.columns([1, 2, 1])
    with col_c:
        tab_login, tab_signup = st.tabs(["Sign In", "Create Account"])

        with tab_login:
            login_email = st.text_input(
                "Email", placeholder="you@example.com", key="login_email"
            )
            login_password = st.text_input(
                "Password", placeholder="Your password",
                type="password", key="login_password"
            )
            if st.button("Sign In", key="btn_login"):
                if not login_email.strip() or not login_password:
                    st.error("Email and password are required.")
                else:
                    try:
                        resp = get_client().auth.sign_in_with_password(
                            {"email": login_email.strip(), "password": login_password}
                        )
                        if resp.session:
                            uid = resp.user.id
                            st.session_state.access_token   = resp.session.access_token
                            st.session_state.refresh_token  = resp.session.refresh_token
                            fetched_role = fetch_user_role(uid)
                            st.session_state.auth           = True
                            st.session_state.current_user   = resp.user.email
                            st.session_state.user_id        = uid
                            st.session_state.user_role      = fetched_role
                            st.session_state.login_attempts = 0
                            st.session_state.role_fetched   = True
                            st.session_state.flags          = None
                            st.session_state.page           = "cv_builder"
                            st.rerun()
                        else:
                            st.session_state.login_attempts += 1
                            st.error(
                                f"Sign in failed — attempt {st.session_state.login_attempts}."
                            )
                    except Exception:
                        st.session_state.login_attempts += 1
                        st.error(
                            f"Invalid credentials — attempt {st.session_state.login_attempts}."
                        )

        with tab_signup:
            su_email   = st.text_input("Email",            placeholder="you@example.com",            key="su_email")
            su_pwd     = st.text_input("Password",         placeholder="Choose a password (8+ chars)", type="password", key="su_pwd")
            su_confirm = st.text_input("Confirm Password", placeholder="Repeat password",              type="password", key="su_confirm")

            if st.button("Create Account", key="btn_signup"):
                if not su_email or not su_pwd or not su_confirm:
                    st.error("All fields are required.")
                elif len(su_pwd) < 8:
                    st.error("Password must be at least 8 characters.")
                elif su_pwd != su_confirm:
                    st.error("Passwords do not match.")
                else:
                    try:
                        resp = get_client().auth.sign_up(
                            {"email": su_email.strip(), "password": su_pwd}
                        )
                        if resp.user:
                            st.success(
                                "Account created. Check your email to confirm, then sign in."
                            )
                        else:
                            st.error("Sign up failed — please try again.")
                    except Exception as exc:
                        st.error(f"Sign up failed: {exc}")

    st.markdown(
        f'<div style="position:fixed;bottom:10px;width:100%;text-align:center;'
        f'color:#94A3B8;font-size:0.72em;pointer-events:none;">'
        f'{APP_TITLE} &nbsp;|&nbsp; {VERSION} &nbsp;|&nbsp; {COPYRIGHT}</div>',
        unsafe_allow_html=True,
    )
    st.stop()

# ==============================================================
# AUTHENTICATED ZONE
# ==============================================================

if not _restore_session():
    # Tokens have expired — force re-login
    for k in list(st.session_state.keys()):
        del st.session_state[k]
    st.rerun()

user_email = st.session_state.current_user
user_id    = st.session_state.user_id
role       = st.session_state.user_role

# Fetch feature flags once per session
if st.session_state.flags is None:
    st.session_state.flags = fetch_feature_flags(user_id)

flags = st.session_state.flags

# ==============================================================
# NAVIGATION MAP  (role-gated + feature-flag-gated)
# ==============================================================

NAV_PAGES: dict[str, dict] = {
    "cv_builder":      {"label": "CV Builder",           "flag": "cv_builder",         "min_role": "User",        "icon": "📄"},
    "ats_level1":      {"label": "ATS — Level 1",        "flag": "ats_level1",          "min_role": "User",        "icon": "🎯"},
    "ats_level2":      {"label": "ATS — Level 2",        "flag": "ats_level2",          "min_role": "User",        "icon": "🔬"},
    "gap_analysis":    {"label": "Gap Analysis",         "flag": "gap_analysis",        "min_role": "User",        "icon": "📊"},
    "linkedin":        {"label": "LinkedIn Generator",   "flag": "linkedin_generator",  "min_role": "User",        "icon": "💼"},
    "reflection":      {"label": "Reflection Journal",  "flag": "reflection",          "min_role": "User",        "icon": "✍️"},
    "export":          {"label": "Export & Package",     "flag": "cv_export",           "min_role": "User",        "icon": "📦"},
    "coach_console":   {"label": "Coach Console",        "flag": "coach_console",       "min_role": "Coach",       "icon": "🎓"},
    "admin_dashboard": {"label": "Admin Console",        "flag": "admin_dashboard",     "min_role": "Admin",       "icon": "🛠️"},
    "system_config":   {"label": "System Config",        "flag": "system_config",       "min_role": "SystemAdmin", "icon": "⚙️"},
}


def _user_pages() -> list[str]:
    visible: list[str] = []
    for key, cfg in NAV_PAGES.items():
        if not role_gte(role, cfg["min_role"]):
            continue
        flag_cfg = flags.get(cfg["flag"], {"enabled": True, "min_role": "User"})
        if not flag_cfg.get("enabled", True):
            continue
        if not role_gte(role, flag_cfg.get("min_role", "User")):
            continue
        visible.append(key)
    return visible


def _guard(page_key: str) -> bool:
    cfg = NAV_PAGES.get(page_key)
    if not cfg:
        st.error("Unknown page.")
        return False
    if not role_gte(role, cfg["min_role"]):
        st.error("Access denied — insufficient role.")
        return False
    flag_cfg = flags.get(cfg["flag"], {"enabled": True, "min_role": "User"})
    if not flag_cfg.get("enabled", True):
        st.error("This feature is currently disabled.")
        return False
    if not role_gte(role, flag_cfg.get("min_role", "User")):
        st.error("Access denied — insufficient role for this feature.")
        return False
    return True


# ==============================================================
# SIDEBAR
# ==============================================================

with st.sidebar:
    st.markdown(
        '<div style="padding:4px 0 12px 0;">'
        '<span style="color:#A5B4FC;font-weight:700;font-size:1.0em;">'
        '&#127963; Career Architect Pro</span></div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        f'<div style="background:#1E293B;border-radius:6px;padding:10px 12px;margin-bottom:14px;">'
        f'<div style="color:#E2E8F0;font-size:0.80em;font-weight:600;'
        f'overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">'
        f'{user_email}</div>'
        f'<div style="color:#94A3B8;font-size:0.73em;margin-top:2px;">{role}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div style="color:#94A3B8;font-size:0.70em;font-weight:600;'
        'letter-spacing:0.08em;margin-bottom:6px;padding-left:2px;">NAVIGATION</div>',
        unsafe_allow_html=True,
    )

    for page_key in _user_pages():
        cfg   = NAV_PAGES[page_key]
        label = f"{cfg['icon']}  {cfg['label']}"
        if st.button(label, key=f"nav_{page_key}"):
            st.session_state.page = page_key
            st.rerun()

    st.markdown('<hr style="border-color:#1E293B;margin:14px 0;">', unsafe_allow_html=True)

    if st.button("Sign Out", key="btn_logout"):
        try:
            get_client().auth.sign_out()
        except Exception:
            pass
        for k in list(st.session_state.keys()):
            del st.session_state[k]
        st.rerun()

    st.markdown(
        f'<div style="position:absolute;bottom:12px;left:0;right:0;'
        f'text-align:center;color:#334155;font-size:0.65em;">{VERSION}</div>',
        unsafe_allow_html=True,
    )

# ==============================================================
# PAGE ROUTER  (lazy imports — modules loaded on demand)
# ==============================================================

current_page = st.session_state.page

if current_page == "cv_builder":
    if _guard("cv_builder"):
        from modules.cv_builder import render_cv_builder
        render_cv_builder(user_id, flags)

elif current_page == "ats_level1":
    if _guard("ats_level1"):
        from modules.ats_level1 import render_ats_level1
        render_ats_level1(user_id, flags)

elif current_page == "ats_level2":
    if _guard("ats_level2"):
        from modules.ats_level2 import render_ats_level2
        render_ats_level2(user_id, flags)

elif current_page == "gap_analysis":
    if _guard("gap_analysis"):
        from modules.gap_analysis import render_gap_analysis
        render_gap_analysis(user_id, flags)

elif current_page == "linkedin":
    if _guard("linkedin"):
        from modules.linkedin_generator import render_linkedin_generator
        render_linkedin_generator(user_id, flags)

elif current_page == "reflection":
    if _guard("reflection"):
        from modules.reflection import render_reflection
        render_reflection(user_id, flags)

elif current_page == "export":
    if _guard("export"):
        from modules.export_system import render_export_system
        render_export_system(user_id, user_email, flags)

elif current_page == "coach_console":
    if _guard("coach_console"):
        from modules.coach_console import render_coach_console
        render_coach_console(user_id, role, flags)

elif current_page == "admin_dashboard":
    if _guard("admin_dashboard"):
        from modules.admin_console import render_admin_console
        render_admin_console(user_id, role, flags)

elif current_page == "system_config":
    if _guard("system_config"):
        from modules.sysadmin_console import render_sysadmin_console
        render_sysadmin_console(user_id, flags)

else:
    st.warning(f"Unknown page '{current_page}' — use the sidebar to navigate.")

# ==============================================================
# FOOTER
# ==============================================================

st.markdown(
    f'<div style="position:fixed;bottom:0;left:0;right:0;'
    f'background:rgba(248,250,252,0.95);backdrop-filter:blur(4px);'
    f'border-top:1px solid #E2E8F0;padding:5px 16px;'
    f'text-align:center;color:#94A3B8;font-size:0.70em;'
    f'z-index:9999;pointer-events:none;">'
    f'{APP_TITLE} &nbsp;|&nbsp; {VERSION} &nbsp;|&nbsp; {COPYRIGHT}'
    f'</div>',
    unsafe_allow_html=True,
)
