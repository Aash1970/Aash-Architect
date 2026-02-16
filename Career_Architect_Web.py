# VERSION 9.5.0 | CAREER ARCHITECT | STATUS: ENGINE FINALIZED
import streamlit as st
import json

# --- 1. SYSTEM CONFIG ---
st.set_page_config(page_title="Career Architect 9.5.0", layout="wide")

if 'auth' not in st.session_state:
    st.session_state.auth = False

st.title("Career Architect")

# --- 2. THE SECURITY GATE ---
with st.sidebar:
    st.header("🔐 System Access")
    st.write("---")
    
    with st.form("gate"):
        key_input = st.text_input("Enter Master Key", type="password", help="Case Sensitive")
        
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

# --- 4. CSS BRUTE FORCE (FIXING THE OVERLAP) ---
# Triple-checked: unsafe_allow_html is the correct parameter.
st.markdown("""
    <style>
    [data-testid="stSidebar"] {
        min-width: 450px !important;
        max-width: 450px !important;
    }
    .stTextInput label {
        font-size: 1.2rem !important;
        margin-bottom: 8px !important;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown("---")
st.write("Version 9.5.0 | © 2026 Career Architect")
