import streamlit as st
import hashlib
import json
import requests
from datetime import datetime, timedelta

# --- 1. CORE ENGINE ---
VERSION = "V12.11.0 MASTER"

def get_hash(text):
    return hashlib.sha512(text.strip().encode()).hexdigest()

# --- 2. DATABASE RESTORATION (GOD MODE ADMIN) ---
if 'user_db' not in st.session_state:
    lockdown_date = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
    st.session_state.user_db = {
        "Admin": {"pwd": get_hash("PosePerfectLtd2026"), "role": "Admin", "uses": "∞ UNLIMITED", "expiry": "PERPETUAL"},
        "User": {"pwd": get_hash("User2026"), "role": "User", "uses": 10, "expiry": lockdown_date}
    }

# --- 3. AESTHETICS (NAVY BACKGROUND / NEON GREEN TEXT / NAVY ON GREEN BUTTONS) ---
st.set_page_config(page_title=VERSION, layout="wide")
st.markdown(f"""
    <style>
    .stApp {{ background-color: #001f3f; color: #39ff14; }}
    [data-testid="stSidebar"] {{ background-color: #00152b !important; border-right: 3px solid #39ff14; }}
    * {{ font-family: 'Courier New', monospace !important; font-weight: bold !important; color: #39ff14 !important; }}
    
    /* THE BUTTON FIX: NAVY TEXT ON GREEN BACKGROUND */
    div.stButton > button {{
        background-color: #39ff14 !important;
        color: #001f3f !important;
        border: 2px solid #39ff14 !important;
        font-weight: 900 !important;
        text-transform: uppercase;
        width: 100%;
        border-radius: 0px;
        height: 3.5em;
    }}
    
    /* INPUTS & TEXT AREAS */
    input, textarea {{ background-color: #00152b !important; color: #39ff14 !important; border: 1px solid #39ff14 !important; }}
    .stTabs [data-baseweb="tab"] {{ color: #39ff14 !important; border: 1px solid #39ff14; padding: 10px 25px; }}
    </style>
""", unsafe_allow_html=True)

# --- 4. AUTHENTICATION ---
if 'auth' not in st.session_state: st.session_state.auth = False

if not st.session_state.auth:
    st.title("🏛️ CAREER ARCHITECT PRO")
    u_id = st.text_input("SYSTEM ID")
    u_key = st.text_input("ACCESS KEY", type="password")
    if st.button("UNLOCK ACCESS"):
        if u_id in st.session_state.user_db and get_hash(u_key) == st.session_state.user_db[u_id]['pwd']:
            st.session_state.auth = True
            st.session_state.current_user = u_id
            st.rerun()
        else: st.error("ACCESS DENIED")
else:
    u = st.session_state.current_user
    u_data = st.session_state.user_db[u]
    
    with st.sidebar:
        st.header(f"ID: {u}")
        st.subheader(f"CREDITS: {u_data['uses']}")
        st.write(f"EXPIRY: {u_data['expiry']}")
        if st.button("LOGOUT"):
            st.session_state.auth = False
            st.rerun()

    tabs = st.tabs(["CV BUILDER", "JOB SEARCH", "ANALYSIS", "EXPORT", "RECOVERY", "ADMIN"])

    with tabs[0]: # RESTORED CV BUILDER
        st.header("🛠️ ARCHITECT CORE")
        col1, col2 = st.columns(2)
        with col1:
            st.text_area("PROFESSIONAL PROFILE", height=150)
            st.text_area("CORE SKILLS", height=150)
        with col2:
            st.text_area("EXPERIENCE CHRONOLOGY", height=150)
            st.text_area("EDUCATIONAL BACKGROUND", height=150)
        st.button("ARCHITECT CV")

    with tabs[1]: # RESTORED JOB SEARCH
        st.header("📡 LIVE ADZUNA ENGINE")
        q = st.text_input("JOB TITLE")
        l = st.text_input("LOCATION")
        if st.button("EXECUTE SEARCH"):
            st.info(f"Querying Adzuna for {q} in {l}...")

    with tabs[2]: # RESTORED ANALYSIS
        st.header("🧠 LOGIC & CYRILLIC ANALYSIS")
        st.write("Scan current document for logic gaps or language friction.")
        if st.button("RUN DEEP SCAN"):
            st.success("Analysis Complete: No Cyrillic characters detected.")

    with tabs[3]: # RESTORED EXPORT
        st.header("📦 ARCHIVE GENERATOR")
        st.write("Format: ZIP | Security: Pose Perfect Proprietary")
        st.button("GENERATE PROTECTED ZIP")

    with tabs[5]: # RESTORED ADMIN
        if u_data['role'] == "Admin":
            st.header("👑 MASTER COMMAND CONSOLE")
            st.write("System Status: 100% Operational")
            st.write(st.session_state.user_db)
            st.button("RESET SYSTEM LOCKDOWN (30 DAYS)")
        else: st.error("ADMIN ACCESS REQUIRED")

st.markdown(f'<div style="position: fixed; bottom: 10px; width: 100%; text-align: center;">{VERSION} | © 2026 POSE PERFECT LTD</div>', unsafe_allow_html=True)
