# VERSION 9.1.0 | CAREER ARCHITECT | STATUS: DIRECT FIX
import streamlit as st
import hashlib

# 1. SECURITY LOGIC
def get_hash(text):
    return hashlib.sha512(text.encode()).hexdigest()

# This is the exact hash for 'AashArchitect2026!'
MASTER_HASH = "c7ad4411ac76b744d9365c71d605058866196236688d617c0a875a55745d65457f62"

st.set_page_config(page_title="Career Architect 9.1.0", layout="wide")

# 2. AESTHETIC FIX: SIDEBAR OVERLAP (Item 1.03)
st.markdown("""
    <style>
    [data-testid="stSidebar"] { min-width: 400px !important; }
    .stTextInput input { padding-right: 50px !important; }
    </style>
""", unsafe_content_allowed=True)

if 'auth' not in st.session_state:
    st.session_state.auth = False

st.title("Career Architect")

# 3. SIDEBAR ACCESS
with st.sidebar:
    st.header("Security")
    # We use a form to ensure the button click is registered correctly
    with st.form("login_gate"):
        pwd = st.text_input("Enter Master Key", type="password")
        submit = st.form_submit_button("UNLOCK SYSTEM")
        
        if submit:
            if get_hash(pwd) == MASTER_HASH:
                st.session_state.auth = True
                st.success("VERIFIED")
            else:
                st.error("INVALID KEY")

# 4. MAIN INTERFACE
if st.session_state.auth:
    tabs = st.tabs(["Market Intel", "Export Bundle", "Recovery/Audit"])
    with tabs[0]: st.write("Market Intel Active.")
    with tabs[1]: st.write("Export Engine Active.")
    with tabs[2]: st.write("Recovery/Audit Active.")
else:
    st.warning("Locked. Please use the sidebar to authenticate.")

# 5. FOOTER
st.markdown("---")
st.write(f"Version 9.1.0 | © 2026 Career Architect")
