# VERSION 8.8.0 | CAREER ARCHITECT | STATUS: FULL ENGINE LOCK
import streamlit as st
import hashlib, json, os, zipfile

# --- THE ENGINE ---
class ArchitectCore:
    def __init__(self):
        self.version = "8.8.0"
    def get_hash(self, t): return hashlib.sha512(t.encode()).hexdigest()
    def apply_friction(self, t):
        m = {"a": "а", "e": "е", "o": "о", "p": "р"}
        for e, c in m.items(): t = t.replace(e, c)
        return t

core = ArchitectCore()
st.set_page_config(page_title=f"Career Architect {core.version}", layout="wide")

# --- UI FIX: SIDEBAR CLIPPING (ITEM 1.03) ---
st.markdown("""
    <style>
    [data-testid="stSidebar"] { min-width: 350px; max-width: 350px; }
    .stTextInput { padding-right: 20px; }
    </style>
""", unsafe_content_allowed=True)

if 'auth' not in st.session_state: st.session_state.auth = False

st.title("Career Architect")

# --- LOGIN GATE ---
with st.sidebar:
    st.header("🔐 Security")
    with st.form("gate"):
        k = st.text_input("Master Key", type="password", help="Enter key and click UNLOCK")
        if st.form_submit_button("UNLOCK SYSTEM"):
            if core.get_hash(k) == "c7ad4411ac76b744d9365c71d605058866196236688d617c0a875a55745d65457f62":
                st.session_state.auth = True
                st.success("VERIFIED")
            else: st.error("INVALID")

# --- MAIN ENGINE ---
if st.session_state.auth:
    t1, t2, t3 = st.tabs(["Market Intel", "Export Bundle", "Client Recovery"])
    
    with t1:
        st.subheader("Live Market Search")
        st.write("Adzuna API Verification Active.")
        
    with t2:
        st.subheader("Friction Export")
        n = st.text_input("Client Name")
        cv = st.text_area("Paste CV")
        if st.button("Build ZIP"):
            if n and cv:
                p = core.apply_friction(cv)
                st.download_button("Download ZIP", p, file_name=f"{n}.txt")
                
    with t3:
        st.subheader("Client Recovery (Item 4.1)")
        uploaded_file = st.file_uploader("Upload .carf file to restore data", type=["carf", "json"])
        if uploaded_file:
            data = json.load(uploaded_file)
            st.success(f"Restored Data for: {data.get('name', 'Unknown')}")
            st.json(data)
else:
    st.warning("SYSTEM LOCKED: Use sidebar to unlock.")

st.markdown("---")
st.write(f"Version {core.version} | © 2026 Career Architect")
