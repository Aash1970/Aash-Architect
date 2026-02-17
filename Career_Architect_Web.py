import streamlit as st
import hashlib
from datetime import datetime, timedelta

# 1. VERSION DEFINITION
VERSION = "V12.7.5"

def get_hash(text):
    return hashlib.sha512(text.strip().encode()).hexdigest()

# 2. DATABASE & ADMIN GOD-MODE
if 'user_db' not in st.session_state:
    lockdown_date = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
    st.session_state.user_db = {
        "Admin": {
            "pwd": get_hash("PosePerfectLtd2026"), 
            "role": "Admin", 
            "uses": "∞ UNLIMITED", 
            "expiry": "NEVER (PERPETUAL)"
        },
        "User": {
            "pwd": get_hash("User2026"), 
            "role": "User", 
            "uses": 10, 
            "expiry": lockdown_date
        }
    }

# 3. HIGH-CONTRAST VISUALS (NAVY & GREEN)
st.set_page_config(page_title=f"Career Architect {VERSION}", layout="wide")
st.markdown(f"""
    <style>
    .stApp {{ background-color: #001f3f; color: #39ff14; }}
    * {{ font-family: 'Courier New', Courier, monospace !important; font-weight: bold !important; }}
    
    /* THE BUTTON FIX: NAVY TEXT ON GREEN BACKGROUND */
    div.stButton > button {{
        background-color: #39ff14 !important;
        color: #001f3f !important;
        border: 2px solid #39ff14 !important;
        font-weight: 900 !important;
        text-transform: uppercase;
    }}
    </style>
""", unsafe_allow_html=True)

# 4. LOGIN LOGIC
if 'auth' not in st.session_state: st.session_state.auth = False

if not st.session_state.auth:
    st.title(f"🏛️ SYSTEM ACCESS {VERSION}")
    u = st.sidebar.text_input("USERNAME")
    p = st.sidebar.text_input("PASSWORD", type="password")
    if st.sidebar.button("UNLOCK"):
        if u in st.session_state.user_db and get_hash(p) == st.session_state.user_db[u]["pwd"]:
            st.session_state.auth = True
            st.session_state.current_user = u
            st.rerun()
        else: st.error("ACCESS DENIED")
else:
    # 5. MAIN INTERFACE
    u_data = st.session_state.user_db[st.session_state.current_user]
    with st.sidebar:
        st.write(f"VERSION: {VERSION}")
        st.write(f"USER: {st.session_state.current_user}")
        st.write(f"CREDITS: {u_data['uses']}")
        if st.button("LOGOUT"):
            st.session_state.auth = False
            st.rerun()

    tabs = st.tabs(["CV Builder", "Job Search", "Analysis", "Export", "Admin Console"])

    with tabs[4]: # Admin Console
        if u_data['role'] == "Admin":
            st.subheader(f"👑 ADMIN COMMAND - {VERSION}")
            st.json(st.session_state.user_db)
        else:
            st.error("ADMIN ACCESS REQUIRED")

st.markdown(f'<div style="position: fixed; bottom: 10px; width: 100%; text-align: center;">{VERSION} | POSE PERFECT LTD</div>', unsafe_allow_html=True)
