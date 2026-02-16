# VERSION 9.2.0 | CAREER ARCHITECT | STATUS: BULLETPROOF RECOVERY
import streamlit as st
import json

# --- 1. THE UI FIX (SIDEBAR OVERLAP) ---
st.set_page_config(page_title="Career Architect 9.2.0", layout="wide")

st.markdown("""
    <style>
    /* Force sidebar width and prevent text overlap */
    [data-testid="stSidebar"] { min-width: 420px !important; padding: 2rem 1rem !important; }
    .stTextInput input { 
        padding-right: 45px !important; 
        border: 2px solid #39ff14 !important; 
    }
    </style>
""", unsafe_content_allowed=True)

if 'auth' not in st.session_state:
    st.session_state.auth = False

st.title("Career Architect")

# --- 2. THE SECURITY GATE ---
with st.sidebar:
    st.header("🔐 System Access")
    # Using a direct form to ensure the 'Unlock' button is the ONLY trigger
    with st.form("auth_gate"):
        key_input = st.text_input("Enter Master Key", type="password")
        unlock_clicked = st.form_submit_button("UNLOCK SYSTEM")
        
        if unlock_clicked:
            # DIRECT STRING CHECK: No hashing, no margin for error
            if key_input == "AashArchitect2026!":
                st.session_state.auth = True
                st.success("VERIFIED")
            else:
                st.error("ACCESS DENIED")

# --- 3. THE APP ENGINE ---
if st.session_state.auth:
    t1, t2, t3 = st.tabs(["Market Intel", "Export Bundle", "Recovery"])
    
    with t1:
        st.subheader("Live Market Search")
        st.info("System Ready.")
        
    with t2:
        st.subheader("Friction Export")
        name = st.text_input("Client Name")
        if st.button("Generate"):
            st.write(f"Generating bundle for {name}...")

    with t3:
        st.subheader("Client Recovery")
        st.file_uploader("Upload .carf", type=["carf"])

else:
    st.warning("⚠️ SYSTEM LOCKED: Use the sidebar to authenticate.")

# --- 4. FOOTER ---
st.markdown("---")
st.write("Version 9.2.0 | © 2026 Career Architect")
