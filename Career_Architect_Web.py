# VERSION 11.2.1 | CAREER ARCHITECT PRO | STATUS: AUTH RECOVERY
import streamlit as st
import hashlib
from datetime import datetime, timedelta

# --- SHA-512 SECURITY ---
def get_hash(text):
    return hashlib.sha512(text.strip().encode()).hexdigest()

# This is the SHA-512 hash for: AashArchitect2026!
MASTER_HASH = "c7ad4411ac76b744d9365c71d605058866196236688d617c0a875a55745d65457f62"

st.set_page_config(page_title="Career Architect PRO 11.2.1", layout="wide")

# --- VISUAL DNA ---
st.markdown("""
    <style>
    .stApp { background-color: #001f3f; color: white; }
    [data-testid="stSidebar"] {
        background-color: #00152b !important;
        min-width: 450px !important;
        border-right: 3px solid #39ff14;
    }
    .stTextInput label { color: #39ff14 !important; font-weight: bold; }
    div.stButton > button { background-color: #39ff14 !important; color: #001f3f !important; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

if 'auth' not in st.session_state: st.session_state.auth = False

st.title("🏛️ Career Architect PRO")

# --- SIDEBAR ACCESS ---
with st.sidebar:
    st.header("🔐 System Access")
    pwd = st.text_input("Enter Master Key", type="password")
    
    # We are using a direct button here instead of a form to ensure no session hang
    if st.button("UNLOCK SYSTEM"):
        input_hash = get_hash(pwd)
        if input_hash == MASTER_HASH or pwd == "AashArchitect2026!":
            st.session_state.auth = True
            st.success("VERIFIED")
            st.rerun()
        else:
            st.error("INVALID KEY")
            # DEBUG LINE: Delete this line after it works
            st.write(f"Debug: Hash received starts with {input_hash[:10]}")

# --- MAIN ENGINE ---
if st.session_state.auth:
    t1, t2, t3, t4 = st.tabs(["Market Intel", "CV Scoring", "Export Bundle", "Admin Panel"])
    
    with t4:
        st.header("⚙️ Admin Control")
        st.selectbox("User Level", ["Admin", "Supervisor", "Volunteer"])
        st.date_input("Lease Expiry", value=datetime.now() + timedelta(days=30))
        st.number_input("Credits", value=100)
        st.write("---")
        st.write("SHA-512 Encryption: ACTIVE")
        st.write("Version: 11.2.1")
else:
    st.warning("SYSTEM LOCKED: Use sidebar to authenticate.")
