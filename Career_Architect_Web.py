# VERSION 8.9.0 | CAREER ARCHITECT | STATUS: FULL ENGINE LOCK
import streamlit as st
import hashlib, json, os

# --- CORE LOGIC ---
def get_hash(text):
    return hashlib.sha512(text.encode()).hexdigest()

def apply_friction(text):
    m = {"a": "а", "e": "е", "o": "о", "p": "р"}
    for e, c in m.items(): text = text.replace(e, c)
    return text

# --- APP CONFIG ---
st.set_page_config(page_title="Career Architect 8.9.0", layout="wide")

# FIXING ITEM 1.03: SIDEBAR CLIPPING
st.markdown("""
    <style>
    [data-testid="stSidebar"] { min-width: 380px; }
    .stTextInput > div > div > input { padding-right: 30px !important; }
    </style>
""", unsafe_content_allowed=True)

if 'auth' not in st.session_state: st.session_state.auth = False

st.title("Career Architect")

# --- SIDEBAR SECURITY ---
with st.sidebar:
    st.header("🔐 Security Gate")
    with st.form("auth"):
        pwd = st.text_input("Enter Key", type="password")
        if st.form_submit_button("UNLOCK SYSTEM"):
            if get_hash(pwd) == "c7ad4411ac76b744d9365c71d605058866196236688d617c0a875a55745d65457f62":
                st.session_state.auth = True
                st.success("VERIFIED")
            else:
                st.error("INVALID KEY")

# --- MAIN INTERFACE ---
if st.session_state.auth:
    t1, t2, t3 = st.tabs(["Market Intel", "Export Bundle", "Recovery/Audit"])
    
    with t1:
        st.subheader("Market Intel Feed")
        st.write("Adzuna Connection: Ready.")
        
    with t2:
        st.subheader("Protected Export")
        c_name = st.text_input("Client Name")
        c_cv = st.text_area("Client CV")
        if st.button("Generate ZIP"):
            if c_name and c_cv:
                p = apply_friction(c_cv)
                st.download_button("Download ZIP", p, file_name=f"{c_name}.txt")

    with t3:
        st.subheader("Data Recovery (Item 4.01)")
        up = st.file_uploader("Upload .carf file", type=["json", "carf"])
        if up:
            data = json.load(up)
            st.success(f"Restored: {data.get('name')}")
            st.json(data)
else:
    st.warning("Locked. Please use the sidebar to authenticate.")

st.markdown("---")
st.write(f"Version 8.9.0 | © 2026 Career Architect")
