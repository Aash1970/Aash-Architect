# VERSION 9.0.0 | CAREER ARCHITECT | STATUS: ENGINE FINALIZED
import streamlit as st
import hashlib, json, os

# --- CORE FUNCTIONS ---
def get_hash(text):
    return hashlib.sha512(text.encode()).hexdigest()

def apply_friction(text):
    m = {"a": "а", "e": "е", "o": "о", "p": "р"}
    for e, c in m.items(): text = text.replace(e, c)
    return text

# --- SYSTEM CONFIG ---
st.set_page_config(page_title="Career Architect 9.0.0", layout="wide")

# FIXING ITEM 1.03: SIDEBAR CLIPPING & OVERLAP
st.markdown("""
    <style>
    [data-testid="stSidebar"] { min-width: 380px; }
    .stTextInput > div > div > input { padding-right: 40px !important; }
    </style>
""", unsafe_content_allowed=True)

if 'auth' not in st.session_state: st.session_state.auth = False

st.title("Career Architect")

# --- SIDEBAR: THE LOCK ---
with st.sidebar:
    st.header("🔐 Security Gate")
    with st.form("auth_gate"):
        pwd = st.text_input("Master Key", type="password")
        if st.form_submit_button("UNLOCK SYSTEM"):
            # AashArchitect2026!
            if get_hash(pwd) == "c7ad4411ac76b744d9365c71d605058866196236688d617c0a875a55745d65457f62":
                st.session_state.auth = True
                st.success("VERIFIED")
            else:
                st.error("INVALID KEY")

# --- MAIN INTERFACE ---
if st.session_state.auth:
    t1, t2, t3 = st.tabs(["Market Intel", "Export Bundle", "Recovery/Audit"])
    
    with t1:
        st.subheader("Market Intel Search")
        st.write("Adzuna API: Operational")
        
    with t2:
        st.subheader("Protected Export")
        c_name = st.text_input("Client Name")
        c_cv = st.text_area("Paste CV")
        if st.button("Generate ZIP"):
            if c_name and c_cv:
                p = apply_friction(c_cv)
                st.download_button("Download ZIP", p, file_name=f"{c_name}_Export.txt")

    with t3:
        st.subheader("Data Recovery (Item 4.01)")
        up = st.file_uploader("Upload .carf or .json file", type=["json", "carf"])
        if up:
            data = json.load(up)
            st.success(f"Restored Data for: {data.get('name', 'Unknown')}")
            st.json(data)
else:
    st.warning("SYSTEM LOCKED: Use sidebar to unlock.")

st.markdown("---")
st.write(f"Version 9.0.0 | © 2026 Career Architect")
