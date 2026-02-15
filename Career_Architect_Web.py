"""
PROJECT: Aash Career Architect
VERSION: 5.4.0-STABLE (PHASE 5: UI EXPORT)
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
    st.header("Admin Portal")
    user_pass = st.text_input("Admin Password", type="password")
    unlocked = st.button("Unlock System")

if unlocked:
    tab1, tab2, tab3 = st.tabs(["Job Search", "CV Architect", "Recovery (CARF)"])
    
    with tab1:
        st.header("Job Intelligence")
        job_title = st.text_input("Title")
        if st.button("Search"):
            jobs = core.fetch_adzuna_jobs(job_title)
            for j in jobs[:3]: st.write(f"**{j['title']}**")

    with tab2:
        st.header("Finalize & Export")
        c_name = st.text_input("Client Name")
        c_cv = st.text_area("CV Content")
        if st.button("Generate ZIP Bundle"):
            zip_file = core.create_zip_bundle(c_name, c_cv)
            with open(zip_file, "rb") as f:
                st.download_button("Download ZIP (PDF + .CARF)", f, file_name=zip_file)
            st.warning("Manifest Item 7: This data will be purged from the system in 30 days. Save the .CARF file safely.")

    with tab3:
        st.header("Returning Client Recovery")
        uploaded_file = st.file_uploader("Upload .CARF File", type=["carf"])
        if uploaded_file:
            data = uploaded_file.read().decode("utf-8")
            st.success("Client Data Recovered. Resuming Architect...")
            st.json(data)
