# VERSION 12.4.0 | CAREER ARCHITECT PRO | STATUS: VISIBILITY & ADMIN LOGIC FIX
import streamlit as st
import hashlib
from datetime import datetime, timedelta

def get_hash(text):
    return hashlib.sha512(text.strip().encode()).hexdigest()

# INITIALIZING MASTER DATABASE (ADMIN = UNLIMITED)
if 'user_db' not in st.session_state:
    st.session_state.user_db = {
        "Admin": {"pwd": get_hash("PosePerfectLtd2026"), "role": "Admin", "uses": float('inf'), "lease": "PERPETUAL"},
        "Supervisor": {"pwd": get_hash("Super2026"), "role": "Supervisor", "uses": 50, "lease": 30},
        "User": {"pwd": get_hash("User2026"), "role": "User", "uses": 10, "lease": 7}
    }

if 'pending_credits' not in st.session_state: st.session_state.pending_credits = []
if 'wa_number' not in st.session_state: st.session_state.wa_number = "447000000000"
if 'draft_cv' not in st.session_state: st.session_state.draft_cv = {"name": "", "role": "", "content": ""}

# --- VISUAL DNA FIX (NAVY TEXT ON GREEN BUTTONS) ---
st.set_page_config(page_title="Career Architect PRO V12.4", layout="wide")
st.markdown(f"""
    <style>
    .stApp {{ background-color: #001f3f; color: white; }}
    [data-testid="stSidebar"] {{ background-color: #00152b !important; border-right: 3px solid #39ff14; }}
    
    /* GLOBAL FONT: GREEN COURIER BOLD */
    h1, h2, h3, h4, label, p, span, div, [data-baseweb="tab"] p, .stMarkdown p strong {{
        color: #39ff14 !important;
        font-family: 'Courier New', Courier, monospace !important;
        font-weight: bold !important;
        text-transform: uppercase !important;
    }}
    
    /* BUTTON FIX: NAVY TEXT ON GREEN BACKGROUND */
    div.stButton > button {{
        background-color: #39ff14 !important;
        color: #001f3f !important; /* DARK NAVY TEXT FOR READABILITY */
        border-radius: 0px !important;
        border: none !important;
        font-weight: 900 !important;
    }}
    
    .footer {{ position: fixed; bottom: 0; left: 0; width: 100%; background: #001f3f; text-align: center; padding: 10px; border-top: 2px solid #39ff14; font-family: 'Courier New', monospace; color: #39ff14; }}
    </style>
""", unsafe_allow_html=True)

st.title("🏛️ Career Architect PRO")

# --- SIDEBAR ACCESS ---
with st.sidebar:
    st.header("🔐 SYSTEM ACCESS")
    if not st.session_state.get('auth'):
        u = st.text_input("USERNAME")
        p = st.text_input("PASSWORD", type="password")
        if st.button("UNLOCK SYSTEM"):
            if u in st.session_state.user_db and get_hash(p) == st.session_state.user_db[u]["pwd"]:
                st.session_state.auth = True
                st.session_state.current_user = u
                st.rerun()
            else: st.error("❌ ACCESS DENIED")
    else:
        st.success(f"✅ LOGGED IN: {st.session_state.current_user}")
        
        # ADMIN DISPLAY LOGIC: UNLIMITED VS NUMERIC
        u_data = st.session_state.user_db[st.session_state.current_user]
        uses_display = "∞ UNLIMITED" if u_data['uses'] == float('inf') else u_data['uses']
        lease_display = u_data['lease']
        
        st.write(f"REMAINING USES: {uses_display}")
        st.write(f"LEASE STATUS: {lease_display}")
        st.markdown(f"[📲 WHATSAPP SUPPORT](https://wa.me/{st.session_state.wa_number})")
        if st.button("LOGOUT"):
            st.session_state.auth = False
            st.rerun()

# --- MAIN ENGINE ---
if st.session_state.get('auth'):
    user = st.session_state.user_db[st.session_state.current_user]
    tabs = st.tabs(["CV Builder", "Job Search", "CV Analysis", "Export CV", "CV Recovery", "Admin Console"])
    
    with tabs[0]: # CV Builder
        st.subheader("🏛️ CV BUILDER ENGINE")
        st.text_input("FULL NAME")
        st.text_area("EXPERIENCE SUMMARY", height=200)
        st.button("SAVE DRAFT")

    with tabs[1]: # Job Search
        st.subheader("🌍 GEOGRAPHIC SEARCH")
        if user['role'] in ['Admin', 'Supervisor']:
            st.radio("SCOPE", ["LOCAL", "NATIONAL", "INTERNATIONAL"])
            st.button("SEARCH JOBS")
        else: st.warning("🚫 RESTRICTED")

    with tabs[5]: # Admin Console
        if user['role'] == "Admin":
            st.subheader("👑 MASTER ADMIN CONSOLE")
            col1, col2 = st.columns(2)
            with col1:
                st.write("**PENDING CREDIT REQUESTS**")
                # Clear, Reject, Approve logic here
            with col2:
                st.write("**LIVE USER REGISTRY**")
                st.write(st.session_state.user_db)
        else:
            st.warning("🚫 ADMIN ACCESS ONLY")

st.markdown(f'<div class="footer">Version 12.4.0 | © 2026 Career Architect</div>', unsafe_allow_html=True)
