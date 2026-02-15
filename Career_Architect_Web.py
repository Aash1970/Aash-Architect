"""
PROJECT: Aash Career Architect
VERSION: 5.2.0-STABLE (PHASE 3: UI LAYER)
RELEASE DATE: 2026-02-15
"""

import streamlit as st
from architect_core import ArchitectCore

core = ArchitectCore()

# Manifest Item 8: Branding - Solid Royal Blue Protocol
st.set_page_config(page_title=f"Aash Career Architect {core.version}", layout="wide")

st.markdown(f"""
    <style>
    .stApp {{ background-color: #1E3A8A; color: white; }}
    .stButton>button {{ background-color: #008080 !important; color: white !important; }}
    .version-tag {{ position: fixed; bottom: 10px; right: 10px; font-size: 0.8em; color: rgba(255,255,255,0.5); }}
    </style>
    <div class="version-tag">Build v{core.version}</div>
    """, unsafe_allow_html=True)

st.title("Aash Career Architect")

# SIDEBAR: ADMIN GATEWAY & LOGO CONTROL
with st.sidebar:
    st.header("Security & Branding")
    logo_size = st.slider("Logo Scale (Manifest Item 4)", 0.5, 2.0, 1.0)
    st.image("https://via.placeholder.com/150", width=int(150 * logo_size))
    
    user_pass = st.text_input("Admin Password", type="password")
    unlocked = st.button("Unlock System")

if unlocked:
    st.success(core.run_purge_audit())
    
    # PHASE 3: THE AASH SAUCE INTERFACE
    st.header("Live Job Intelligence (Adzuna)")
    col1, col2 = st.columns(2)
    with col1:
        job_title = st.text_input("Job Title", value="Software Engineer")
    with col2:
        location = st.text_input("Location", value="London")
        
    if st.button("Search Live Jobs"):
        jobs = core.fetch_adzuna_jobs(job_title, location)
        for job in jobs[:5]: # Show top 5
            with st.expander(f"{job['title']} - {job['company']['display_name']}"):
                st.write(job['description'])
                st.info(f"Salary: {job.get('salary_min', 'N/A')} | Location: {job['location']['display_name']}")
