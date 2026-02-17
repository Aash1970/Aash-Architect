# VERSION 11.9.0 | CAREER ARCHITECT PRO | STATUS: FULL CONSOLE RESTORATION
import streamlit as st
import hashlib
import json
from datetime import datetime, timedelta

# --- 1. CORE SECURITY ---
def get_hash(text):
    return hashlib.sha512(text.strip().encode()).hexdigest()

# Persistent Database & Request Queue
if 'user_db' not in st.session_state:
    st.session_state.user_db = {
        "Admin": {"pwd": get_hash("PosePerfectLtd2026"), "role": "Admin", "uses": 999},
        "Supervisor": {"pwd": get_hash("Super2026"), "role": "Supervisor", "uses": 50},
        "User": {"pwd": get_hash("User2026"), "role": "User", "uses": 10}
    }
if 'pending_requests' not in st.session_state: st.session_state.pending_requests = []
if 'wa_number' not in st.session_state: st.session_state.wa_number = "447000000000"

# --- 2. THE VISUAL DNA (SYNCHRONIZED) ---
st.set_page_config(page_title="Career Architect PRO 11.9.0", layout="wide")
st.markdown(f"""
    <style>
    .stApp {{ background-color: #001f3f; color: white; }}
    [data-testid="stSidebar"] {{ background-color: #00152b !important; min-width: 450px !important; border-right: 3px solid #39ff14; }}
    h1, h2, h3, label, [data-baseweb="tab"] p, .stMarkdown p strong {{
        color: #39ff14 !important; font-family: 'Courier New', monospace !important; font-weight: bold !important; text-transform: uppercase !important;
    }}
    [data-baseweb="tab"] p {{ font-size: 1.1rem !important; }}
    div.stButton > button {{ background-color: #39ff14 !important; color: #001f3f !important; font-weight: bold !important; border-radius: 8px; }}
    .footer {{ position: fixed; bottom: 0; left: 0; width: 100%; background: #001f3f; color: #39ff14; text-align: center; padding: 5px; font-size: 0.8rem; border-top: 1px solid #39ff14; }}
    </style>
""", unsafe_allow_html=True)

if 'auth' not in st.session_state: st.session_state.auth = False

st.title("🏛️ Career Architect PRO")

# --- 3. THE SIDEBAR (LOGIN & WHATSAPP) ---
with st.sidebar:
    st.header("🔐 SYSTEM ACCESS")
    if not st.session_state.auth:
        u_name = st.text_input("USERNAME")
        p_word = st.text_input("PASSWORD", type="password")
        if st.button("UNLOCK SYSTEM"):
            if u_name in st.session_state.user_db and get_hash(p_word) == st.session_state.user_db[u_name]["pwd"]:
                st.session_state.auth, st.session_state.current_user = True, u_name
                st.rerun()
            else: st.error("INVALID CREDENTIALS")
    else:
        st.success(f"ACTIVE SESSION: {st.session_state.current_user}")
        # WHATSAPP BIT
        st.write("---")
        st.header("📲 SUPPORT")
        wa_url = f"https://wa.me/{st.session_state.wa_number}?text=Requesting%20More%20Uses"
        st.markdown(f"[REQUEST USES VIA WHATSAPP]({wa_url})")
        if st.button("LOGOUT"):
            st.session_state.auth = False
            st.rerun()

# --- 4. THE ENGINE ---
if st.session_state.auth:
    user = st.session_state.user_db[st.session_state.current_user]
    
    # AGREED TABS
    tabs = st.tabs(["Job Search", "CV Analysis", "Export CV", "CV Recovery", "Admin Console"])
    
    with tabs[0]: # Job Search
        if user['role'] in ['Admin', 'Supervisor']:
            st.subheader("Job Search (Adzuna)")
            st.text_input("Postcode/City")
            st.button("Search 50 Roles")
        else: st.warning("USER ACCESS: Job Search Disabled.")

    with tabs[1]: # CV Analysis
        if user['role'] in ['Admin', 'Supervisor']:
            st.subheader("CV Analysis & ATS scoring")
            st.text_area("Paste CV")
            st.button("Run AI Scoring")
        else: st.warning("USER ACCESS: CV Analysis Disabled.")

    with tabs[2]: # Export CV
        st.subheader("Export CV (Cyrillic Friction)")
        st.write(f"Uses Remaining: {user['uses']}")
        if st.button("Request More Uses"):
            st.session_state.pending_requests.append(f"{st.session_state.current_user} requested 10 uses")
            st.success("Request sent to Admin.")
        st.button("Generate Protected ZIP")

    with tabs[3]: # CV Recovery
        st.subheader("CV Recovery")
        st.file_uploader("Upload .carf Metadata file")

    with tabs[4]: # Admin Console
        if user['role'] == 'Admin':
            st.subheader("👑 ADMIN CONTROL CENTER")
            
            col1, col2 = st.columns(2)
            with col1:
                st.write("**PENDING USE REQUESTS**")
                for req in st.session_state.pending_requests:
                    st.write(f"⚠️ {req}")
                if st.button("Clear Requests"): st.session_state.pending_requests = []
            
            with col2:
                st.write("**LIVE VIEW: USERS**")
                st.json(st.session_state.user_db)
            
            st.write("---")
            st.subheader("WHATSAPP CONFIG")
            st.session_state.wa_number = st.text_input("SET ADMIN WHATSAPP (Format: 447000...)", value=st.session_state.wa_number)
        else:
            st.warning("RESTRICTED: ADMIN EYES ONLY")

st.markdown(f'<div class="footer">Version 11.9.0 | © 2026 Career Architect</div>', unsafe_allow_html=True)
