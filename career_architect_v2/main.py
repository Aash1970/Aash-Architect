import streamlit as st
import hashlib
from datetime import datetime, timedelta

# ==============================================================
# CONSTANTS
# ==============================================================
APP_TITLE   = "CAREER ARCHITECT PRO"
VERSION     = "v2.0.0 — MODULAR"
COPYRIGHT   = "© 2026 CAREER ARCHITECT"

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
    """Returns True if role_a has equal or higher permissions than role_b."""
    return ROLE_HIERARCHY.get(role_a, 0) >= ROLE_HIERARCHY.get(role_b, 0)

# ==============================================================
# HELPERS
# ==============================================================

def get_hash(text: str) -> str:
    return hashlib.sha512(text.strip().encode()).hexdigest()

# ==============================================================
# SESSION STATE INITIALISATION
# ==============================================================

def _init_state():
    if "auth" not in st.session_state:
        st.session_state.auth = False
    if "current_user" not in st.session_state:
        st.session_state.current_user = None
    if "login_attempts" not in st.session_state:
        st.session_state.login_attempts = 0
    if "page" not in st.session_state:
        st.session_state.page = "cv_builder"
    if "user_db" not in st.session_state:
        lockdown_date = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
        st.session_state.user_db = {
            "SystemAdmin": {
                "pwd": get_hash("SystemAdmin2026"),
                "role": "SystemAdmin",
                "uses": "UNLIMITED",
                "expiry": "PERPETUAL",
            },
            "Admin": {
                "pwd": get_hash("PosePerfectLtd2026"),
                "role": "Admin",
                "uses": "UNLIMITED",
                "expiry": "PERPETUAL",
            },
            "Coach": {
                "pwd": get_hash("Coach2026"),
                "role": "Coach",
                "uses": 50,
                "expiry": lockdown_date,
            },
            "User": {
                "pwd": get_hash("User2026"),
                "role": "User",
                "uses": 10,
                "expiry": lockdown_date,
            },
        }

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
    border-right: 2px solid #6366F1 !important;
}

/* ── GLOBAL FONT ───────────────────────────────────────────── */
*, p, span, div, label, h1, h2, h3, h4, h5, h6, li {
    font-family: 'Segoe UI', sans-serif !important;
    color: #1E293B !important;
}

/* ── SIDEBAR OVERRIDES ─────────────────────────────────────── */
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] span,
[data-testid="stSidebar"] div,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3,
[data-testid="stSidebar"] h4,
[data-testid="stSidebar"] li {
    color: #F8FAFC !important;
}

/* ── BUTTONS ───────────────────────────────────────────────── */
div.stButton > button {
    background-color: #6366F1 !important;
    color: #ffffff !important;
    border: none !important;
    font-weight: 600 !important;
    width: 100% !important;
    border-radius: 6px !important;
    height: 3em !important;
    letter-spacing: 0.5px;
}
div.stButton > button:hover {
    background-color: #4F46E5 !important;
    color: #ffffff !important;
}
div.stButton > button:active {
    background-color: #4338CA !important;
    color: #ffffff !important;
}

/* ── INPUTS ────────────────────────────────────────────────── */
input, textarea,
[data-baseweb="input"] input,
[data-baseweb="textarea"] textarea {
    background-color: #ffffff !important;
    color: #1E293B !important;
    border: 1px solid #CBD5E1 !important;
    border-radius: 4px !important;
}

/* ── SELECTBOX ─────────────────────────────────────────────── */
[data-baseweb="select"] > div,
[data-baseweb="select"] div,
[data-baseweb="popover"] {
    background-color: #ffffff !important;
    color: #1E293B !important;
    border: 1px solid #CBD5E1 !important;
}

/* ── ALERT BOXES ───────────────────────────────────────────── */
[data-testid="stAlert"], .stAlert {
    background-color: #EEF2FF !important;
    border: 1px solid #6366F1 !important;
    color: #1E293B !important;
}

/* ── SCROLLBAR ─────────────────────────────────────────────── */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: #F8FAFC; }
::-webkit-scrollbar-thumb { background: #6366F1; border-radius: 3px; }
</style>
""", unsafe_allow_html=True)

# ==============================================================
# SPLASH SCREEN / AUTHENTICATION GATE
# ==============================================================

if not st.session_state.auth:
    st.markdown(
        '<h1 style="text-align:center;color:#6366F1;font-family:Segoe UI,sans-serif;">'
        '&#127963; CAREER ARCHITECT PRO</h1>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<p style="text-align:center;color:#1E293B;font-family:Segoe UI,sans-serif;">'
        f'{VERSION} &nbsp;|&nbsp; {COPYRIGHT}</p>',
        unsafe_allow_html=True,
    )
    st.markdown("---")

    col_l, col_c, col_r = st.columns([1, 2, 1])
    with col_c:
        u_id  = st.text_input("SYSTEM ID",   placeholder="Enter your user ID")
        u_key = st.text_input("ACCESS KEY",  placeholder="Enter your access key", type="password")

        if st.button("UNLOCK ACCESS"):
            db = st.session_state.user_db
            if u_id in db and get_hash(u_key) == db[u_id]["pwd"]:
                user_expiry = db[u_id]["expiry"]
                if user_expiry != "PERPETUAL":
                    try:
                        if datetime.strptime(user_expiry, "%Y-%m-%d") < datetime.now():
                            st.error("ACCOUNT EXPIRED. CONTACT ADMINISTRATOR.")
                            st.stop()
                    except ValueError:
                        pass
                user_uses = db[u_id]["uses"]
                if user_uses != "UNLIMITED" and isinstance(user_uses, int) and user_uses <= 0:
                    st.error("CREDIT LIMIT REACHED. CONTACT ADMINISTRATOR.")
                    st.stop()
                st.session_state.auth         = True
                st.session_state.current_user = u_id
                st.session_state.login_attempts = 0
                st.session_state.page         = "cv_builder"
                st.rerun()
            else:
                st.session_state.login_attempts += 1
                st.error(f"ACCESS DENIED — ATTEMPT {st.session_state.login_attempts}")

    st.markdown(
        f'<div style="position:fixed;bottom:10px;width:100%;text-align:center;'
        f'font-family:Segoe UI,sans-serif;font-weight:600;color:#1E293B;font-size:0.75em;">'
        f'{APP_TITLE} | {VERSION} | {COPYRIGHT}</div>',
        unsafe_allow_html=True,
    )
    st.stop()

# ==============================================================
# AUTHENTICATED ZONE
# ==============================================================

u      = st.session_state.current_user
u_data = st.session_state.user_db[u]
role   = u_data["role"]

# ==============================================================
# ROLE-BASED NAVIGATION MAP
# ==============================================================

NAV_PAGES = {
    "cv_builder":      {"label": "CV BUILDER",            "min_role": "User"},
    "ats_scoring":     {"label": "ATS SCORING",            "min_role": "User"},
    "reflection":      {"label": "REFLECTION",             "min_role": "User"},
    "admin_dashboard": {"label": "ADMIN DASHBOARD",        "min_role": "Admin"},
    "system_config":   {"label": "SYSTEM CONFIGURATION",   "min_role": "SystemAdmin"},
}

def _user_pages() -> list:
    return [key for key, cfg in NAV_PAGES.items() if role_gte(role, cfg["min_role"])]

# ==============================================================
# SIDEBAR NAVIGATION
# ==============================================================

with st.sidebar:
    st.markdown(f"### SYSTEM ID: {u}")
    st.markdown(f"**ROLE:** {role}")
    st.markdown("---")

    uses   = u_data["uses"]
    expiry = u_data["expiry"]

    if uses == "UNLIMITED":
        st.markdown("**CREDITS:** ∞ UNLIMITED")
    else:
        st.markdown(f"**CREDITS REMAINING:** {uses}")

    if expiry == "PERPETUAL":
        st.markdown("**ACCESS:** PERPETUAL")
    else:
        try:
            expiry_dt      = datetime.strptime(expiry, "%Y-%m-%d")
            days_remaining = (expiry_dt - datetime.now()).days
            if days_remaining <= 7:
                st.warning(f"EXPIRY: {expiry} ({days_remaining} DAYS REMAINING)")
            else:
                st.markdown(f"**EXPIRY:** {expiry}")
        except ValueError:
            st.markdown(f"**EXPIRY:** {expiry}")

    st.markdown("---")
    st.markdown("**NAVIGATION**")

    for page_key in _user_pages():
        label = NAV_PAGES[page_key]["label"]
        if st.button(label, key=f"nav_{page_key}"):
            st.session_state.page = page_key
            st.rerun()

    st.markdown("---")
    if st.button("LOGOUT"):
        st.session_state.auth         = False
        st.session_state.current_user = None
        st.session_state.page         = "cv_builder"
        st.rerun()

# ==============================================================
# PAGE ROUTER
# ==============================================================

def _guard(page_key: str) -> bool:
    """Returns True if current user is allowed on this page."""
    min_role = NAV_PAGES.get(page_key, {}).get("min_role", "SystemAdmin")
    if not role_gte(role, min_role):
        st.error("ACCESS DENIED — INSUFFICIENT PERMISSIONS.")
        return False
    return True

current_page = st.session_state.page

# ── CV BUILDER ────────────────────────────────────────────────
if current_page == "cv_builder":
    if _guard("cv_builder"):
        st.header("CV BUILDER")
        st.info("CV BUILDER MODULE — HOOK READY FOR INTEGRATION.")
        # TODO: import and call render_cv_builder() from modules/cv_builder.py

# ── ATS SCORING ───────────────────────────────────────────────
elif current_page == "ats_scoring":
    if _guard("ats_scoring"):
        st.header("ATS SCORING")
        st.info("ATS SCORING MODULE — HOOK READY FOR INTEGRATION.")
        # TODO: import and call render_ats_scoring() from modules/ats_scoring.py

# ── REFLECTION ────────────────────────────────────────────────
elif current_page == "reflection":
    if _guard("reflection"):
        st.header("REFLECTION")
        st.info("REFLECTION MODULE — HOOK READY FOR INTEGRATION.")
        # TODO: import and call render_reflection() from modules/reflection.py

# ── ADMIN DASHBOARD ───────────────────────────────────────────
elif current_page == "admin_dashboard":
    if _guard("admin_dashboard"):
        st.header("ADMIN DASHBOARD")
        st.info("ADMIN DASHBOARD MODULE — HOOK READY FOR INTEGRATION.")
        # TODO: import and call render_admin_dashboard() from modules/admin_dashboard.py

# ── SYSTEM CONFIGURATION ──────────────────────────────────────
elif current_page == "system_config":
    if _guard("system_config"):
        st.header("SYSTEM CONFIGURATION")
        st.info("SYSTEM CONFIGURATION MODULE — HOOK READY FOR INTEGRATION.")
        # TODO: import and call render_system_config() from modules/system_config.py

else:
    st.warning(f"UNKNOWN PAGE: '{current_page}'. USE SIDEBAR TO NAVIGATE.")

# ==============================================================
# FOOTER
# ==============================================================

st.markdown(
    f'<div style="position:fixed;bottom:10px;width:100%;text-align:center;'
    f'font-family:Segoe UI,sans-serif;font-weight:600;color:#1E293B;'
    f'font-size:0.75em;z-index:9999;pointer-events:none;">'
    f'{APP_TITLE} &nbsp;|&nbsp; {VERSION} &nbsp;|&nbsp; {COPYRIGHT}'
    f'</div>',
    unsafe_allow_html=True,
)
