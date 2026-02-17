import streamlit as st
import hashlib
from datetime import datetime, timedelta

# --- 1. THE TRUTH ---
VERSION = "V12.8.0 - EMERGENCY STABLE"

def get_hash(text):
    return hashlib.sha512(text.strip().encode()).hexdigest()

# --- 2. THE DATABASE (INFINITY FIX) ---
if 'user_db' not in st.session_state:
    st.session_state.user_db = {
        "Admin": {
            "pwd": get_hash("PosePerfectLtd2026"), 
            "role": "Admin", 
            "uses": "∞ UNLIMITED", 
            "expiry": "PERPETUAL"
        },
        "User": {
            "pwd": get_hash("User2026"), 
            "role": "User", 
            "uses": 10, 
            "expiry": (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
        }
    }

# --- 3. THE STYLE (FORCED CONTRAST) ---
st.set_page_config(page_title=VERSION, layout="wide")
st.markdown(f"""
    <style>
    /* DARK NAVY BACKGROUND */
    .stApp {{ background-color: #000b1a; }}
    
    /* NEON GREEN TEXT EVERYWHERE */
    * {{ 
        font-family: 'Courier New', monospace !important; 
        font-weight: 900 !important; 
        color: #39ff14 !important; 
    }}
    
    /* THE BUTTON FIX: BLACK TEXT ON NEON GREEN */
    div.stButton > button {{
        background-color: #39ff14 !important;
        color: #000000 !important;
        border: 3px solid #ffffff !important;
        font-size: 20px !important;
        height: 60px !important;
        width: 100% !important;
    }}

    /* TABS FIX: VISIBLE SELECTION */
    .stTabs [data-baseweb="tab"] {{
        background-color: #00152b !important;
        border: 1px solid #39ff14 !important;
        padding: 10px !important;
    }}
    </style>
""", unsafe_allow_html=True)

# --- 4. THE INTERFACE ---
st.title(f"🏛️ SYSTEM STATUS: {VERSION}")

if 'auth' not in st.session_state: st.session_state.auth = False

if not st.session_state.auth:
    col1, _ = st.columns([1, 1])
    with col1:
        u = st.text_input("ENTER USERNAME")
        p = st.text_input("ENTER PASSWORD", type="password")
        if st.button("UNLOCK SYSTEM NOW"):
            if u in st.session_state.user_db and get_hash(p) == st.session_state.user_db[u]["pwd"]:
                st.session_state.auth = True
                st.session_state.current_user = u
                st.rerun()
            else: st.error("!!! ACCESS DENIED !!!")
else:
    u_data = st.session_state.user_db[st.session_state.current_user]
    
    # SIDEBAR INFO
    st.sidebar.header(f"USER: {st.session_state.current_user}")
    st.sidebar.subheader(f"CREDITS: {u_data['uses']}")
    if st.sidebar.button("LOGOUT / LOCK"):
        st.session_state.auth = False
        st.rerun()

    # TABS
    t1, t2, t3, t4 = st.tabs(["BUILDER", "JOB SEARCH", "EXPORT", "ADMIN"])
    
    with t4: # Admin
        if u_data['role'] == "Admin":
            st.header("👑 MASTER COMMAND")
            st.write("CURRENT REGISTRY:")
            st.json(st.session_state.user_db)
        else:
            st.error("ADMIN ACCESS ONLY")
            
    with t1:
        st.write("SYSTEM READY. PROCEED WITH CV ARCHITECTURE.")
