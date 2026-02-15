"""
PROJECT: Aash Career Architect
VERSION: 5.6.0-STABLE (UI LAYER)
RELEASE DATE: 2026-02-15
"""

import streamlit as st
from architect_core import ArchitectCore
import os

core = ArchitectCore()
st.set_page_config(page_title=f"Aash Career Architect {core.version}", layout="wide")

st.markdown(f"""
    <style>
    .stApp {{ background-color: #1E3A8A; color: white; }}
    .stButton>button {{ background-color: #008080 !important; color: white !important; }}
    </style>
    """, unsafe_allow_html=True)

st.title("Aash Career Architect")

with st.sidebar:
    st.header("Admin Access")
    user_pass = st.text_input("Password", type="password")
    unlocked = st.button("Unlock System")

if unlocked:
    tab1, tab2, tab3, tab4 = st.tabs(["Job Search", "Secure Export", "Recovery", "Manuals"])
    
    with tab1:
        st.header("Adzuna Live Search")
        title = st.text_input("Job Role")
        if st.button("Search"):
            jobs = core.fetch_adzuna_jobs(title)
            for j in jobs[:3]: st.write(f"**{j['title']}**")

    with tab2:
        st.header("Generate Protected Bundle")
        name = st.text_input("Client Name")
        cv = st.text_area("Paste CV Text Here")
        if st.button("Build ZIP"):
            zip_file = core.create_zip_bundle(name, cv)
            with open(zip_file, "rb") as f:
                st.download_button("Download Secure ZIP", f, file_name=zip_file)
            st.success("Manifest Item 16: Client Manual included in ZIP bundle.")

    with tab3:
        st.header("Restore from .CARF")
        up = st.file_uploader("Upload Recovery File", type=["carf"])
        if up: st.json(up.read().decode("utf-8"))

    with tab4:
        st.header("System Documentation")
        role_select = st.selectbox("Select Manual Type", ["Admin", "Supervisor", "Client"])
        manual_text = core.generate_system_manual(role_select)
        st.text_area("Manual Content", manual_text, height=200)
        st.download_button(f"Download {role_select} Manual", manual_text, file_name=f"{role_select}_Manual.txt")
