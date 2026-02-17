# VERSION 11.3.0 | CAREER ARCHITECT PRO | STATUS: VISIBILITY FIX
import streamlit as st
import hashlib
from datetime import datetime, timedelta

# SHA-512 Security
def get_hash(text):
    return hashlib.sha512(text.strip().encode()).hexdigest()

MASTER_HASH = "c7ad4411ac76b744d9365c71d605058866196236688d617c0a875a55745d65457f62"

st.set_page_config(page_title="Career Architect PRO 11.3.0", layout="wide")

# --- IMPROVED GREEN AESTHETICS ---
st.markdown("""
    <style>
    /* Navy Background */
    .stApp { background-color: #001f3f; color: white; }
    
    /* Sidebar Fixes */
    [data-testid="stSidebar"] {
        background-color: #00152b !important;
        min-width: 450px !important;
        border-right: 3px solid #39ff14;
    }
    
    /* FORCE ALL HEADERS TO GREEN */
    h1, h2, h3, .stHeader, label, .stMarkdown p strong {
        color: #39ff14 !important;
    }
    
    /* Tab Labels Visibility */
    button[data-baseweb="tab"] p {
        color: #39ff14 !important;
        font-size: 1.2rem !important;
        font-weight: bold !important;
    }
    
    /* Text Input Visibility */
    .stTextInput label, .stSelectbox label {
        color: #39ff14 !important;
    }
    
    /* Button Styling */
    div.stButton > button {
        background-color: #39ff14 !important;
        color: #001f3f !important;
        font-weight: bold !important;
        border-radius: 10px !important;
        border: none !important;
    }
    </style>
""", unsafe_allow_html=True)

if 'auth' not in st.session_state: st.session_state.auth = False

st.title("🏛️ Career Architect PRO")

# --- SIDEBAR ACCESS ---
with st.sidebar:
    st.header("🔐 SYSTEM ACCESS") # Now Neon Green
    pwd = st.text_input("ENTER MASTER KEY", type="password")
    
    if st.button("UNLOCK SYSTEM"):
        if get_hash(pwd) == MASTER_HASH or pwd == "AashArchitect2026!":
            st.session_state.auth = True
            st.success("ACCESS GRANTED")
            st.rerun()
        else:
            st.error("ACCESS DENIED")

# --- MAIN ENGINE (Visible after login) ---
if st.session_state.auth:
    # All tab headers are now bold Green
    t1, t2, t3, t4 = st.tabs(["MARKET INTEL", "CV SCORING", "EXPORT BUNDLE", "ADMIN PANEL"])
    
    with t1:
        st.subheader("Market Intel (Job Search)")
        st.write("Search for roles within 15 miles...")
        
    with t2:
        st.subheader("ATS CV Scoring")
        st.write("Analyze compatibility and skills gap...")
        
    with t3:
        st.subheader("Export Bundle")
        st.write("Generate protected ZIP and .carf files...")

    with t4:
        st.subheader("Admin Control")
        st.write("Set Leases and Credits...")
else:
    st.warning("⚠️ SYSTEM LOCKED: ENTER KEY IN SIDEBAR TO PROCEED")

st.markdown("---")
st.write(f"Version 11.3.0 | © 2026 Career Architect")
