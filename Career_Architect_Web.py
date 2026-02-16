# VERSION 9.3.0 | CAREER ARCHITECT | STATUS: LAYOUT RECOVERY
import streamlit as st
import json

# --- 1. BRUTE FORCE CSS FIX (ITEM 1.01) ---
st.set_page_config(page_title="Career Architect 9.3.0", layout="wide")

st.markdown("""
    <style>
    /* 1. Force the sidebar to be much wider so labels can't overlap */
    [data-testid="stSidebar"] {
        min-width: 450px !important;
        max-width: 450px !important;
    }
    
    /* 2. Add massive spacing to the input field so text has room to breathe */
    .stTextInput label {
        font-size: 1.2rem !important;
        margin-bottom: 10px !important;
        display: block !important;
    }
    
    /* 3. Fix the input box itself */
    .stTextInput div[data-baseweb="input"] {
        margin-right: 20px !important;
    }
    </style>
""", unsafe_content_allowed=True)

if 'auth' not in st.session_state:
    st.session_state.auth = False

st.title("Career Architect")

# --- 2. THE SECURITY GATE ---
with st.sidebar:
    st.header("🔐 System Access")
    st.write("---")
    
    # Simple, direct form
    with st.form("gate"):
        key_input = st.text_input("Enter Master Key", type="password")
        # I have added clear instructions here to help
        st.caption("Key is case-sensitive. Click button below to unlock.")
        
        if st.form_submit_button("UNLOCK SYSTEM"):
            if key_input == "AashArchitect2026!":
                st.session_state.auth = True
                st.success("VERIFIED")
            else:
                st.error("INVALID KEY")

# --- 3. THE APP ENGINE ---
if st.session_state.auth:
    t1, t2, t3 = st.tabs(["Market Intel", "Export Bundle", "Recovery"])
    
    with t1:
        st.subheader("Market Intel Search")
        st.info("System Ready for Adzuna Query.")
        
    with t2:
        st.subheader("Friction Export")
        name = st.text_input("Client Name")
        if st.button("Generate"):
            st.write(f"Building bundle for {name}...")

    with t3:
        st.subheader("Client Recovery")
        st.file_uploader("Upload .carf file", type=["carf"])

else:
    st.warning("⚠️ SYSTEM LOCKED: Please enter the key in the sidebar.")

# --- 4. FOOTER ---
st.markdown("---")
st.write("Version 9.3.0 | © 2026 Career Architect")
