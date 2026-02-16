import streamlit as st
from architect_core import ArchitectCore

core = ArchitectCore()
st.set_page_config(page_title="Career Architect", layout="wide")

st.markdown("""
    <style>
    [data-testid="stHeader"] { background-color: #0A192F; }
    [data-testid="stSidebar"] { background-color: #0A192F; color: white; }
    .stApp { background-color: #FFFFFF; color: #000000; }
    h1, h2, h3, p, label, .stMarkdown { color: #000000 !important; }
    .sidebar-text { color: #FFFFFF !important; }
    .footer { position: fixed; left: 0; bottom: 0; width: 100%; background-color: #000000; color: #FFFFFF; text-align: center; padding: 10px; font-size: 12px; z-index: 999; }
    </style>
    """, unsafe_allow_html=True)

st.markdown("<h1 style='color:white; background-color:#0A192F; padding:15px;'>Career Architect</h1>", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("<h2 class='sidebar-text'>System Access</h2>", unsafe_allow_html=True)
    pw = st.text_input("Enter Security Key", type="password")
    auth = (core.get_hash(pw) == "c7ad4411ac76b744d9365c71d605058866196236688d617c0a875a55745d65457f62")
    if auth:
        st.success("Admin Verified")
        logo_sz = st.slider("Logo Scale", 0.5, 3.0, 1.0)
        st.image("https://via.placeholder.com/150", width=int(150*logo_sz))

if auth:
    tabs = st.tabs(["Market Intel", "Export Bundle", "Recovery", "Audit"])
    with tabs[1]:
        st.subheader("Secure Client Export")
        name = st.text_input("Client Name")
        cv_text = st.text_area("CV Content", height=300)
        rating = st.select_slider("Suitability", options=range(1, 11), value=8)
        if st.button("Generate ZIP"):
            path = core.create_bundle(name, cv_text)
            with open(path, "rb") as f: st.download_button("Download Bundle", f, file_name=path)
else:
    st.info("Authentication Required.")

st.markdown(f"<div class='footer'>Copyright © 2026 Career Architect | Version {core.version}</div>", unsafe_allow_html=True)
