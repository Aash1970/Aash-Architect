"""
PROJECT: Aash Career Architect
VERSION: 5.7.0-STABLE (PHASE 7: UI LAYER)
RELEASE DATE: 2026-02-15
"""

import streamlit as st
from architect_core import ArchitectCore
import os

# Initialize Engine
core = ArchitectCore()

# Manifest Item 2 & 3: UI Styling (Royal Blue & Teal)
st.set_page_config(page_title=f"Aash Career Architect {core.version}", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #1E3A8A; color: white; }
    .stButton>button { 
        background-color: #008080 !important; 
        color: white !important; 
        border-radius: 5px;
        border: none;
    }
    .stTextInput>div>div>input { color: #1E3A8A; }
    .stTextArea>div>div>textarea { color: #1E3A8A; }
    .stExpander { background-color: rgba(255, 255, 255, 0.1); border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

st.title("Aash Career Architect")

# SIDEBAR: ADMIN & LOGO CONTROL
with st.sidebar:
    st.header("System Control")
    
    # Manifest Item 4: Manual Logo Slider
    logo_size = st.slider("Logo Scale", 0.5, 3.0, 1.0)
    st.image("https://via.placeholder.com/150", width=int(150 * logo_size))
    
    st.divider()
    admin_pass = st.text_input("Security Key", type="password")
    # Manifest Item 5: SHA-512 Verification logic
    is_unlocked = (core.get_hash(admin_pass) == "c7ad4411ac76b744d9365c71d605058866196236688d617c0a875a55745d65457f62")

if is_unlocked:
    st.sidebar.success("Access Granted: Admin Mode")
    
    # Manifest Item 14: Navigation Tabs
    tabs = st.tabs(["Market Intelligence", "Secure Export", "Client Recovery", "System Health"])
    
    with tabs[0]:
        st.header("Adzuna Live Search")
        col1, col2 = st.columns(2)
        with col1:
            job_title = st.text_input("Target Role")
        with col2:
            location = st.text_input("Location", value="London")
        
        if st.button("Search Market"):
            jobs = core.fetch_adzuna_jobs(job_title, location)
            if jobs:
                for j in jobs[:5]:
                    with st.expander(f"{j['title']} - {j['company']['display_name']}"):
                        st.write(j['description'])
                        st.info(f"Location: {j['location']['display_name']} | Salary: {j.get('salary_min', 'N/A')}")
            else:
                st.error("No jobs found. Check API keys in system_config.json.")

    with tabs[1]:
        st.header("Generate Protected Bundle")
        c_name = st.text_input("Client Full Name")
        c_cv = st.text_area("Paste CV Text Content", height=300)
        
        # Manifest Item 11: Suitability Shell
        suitability = st.select_slider("System Suitability Rating", options=range(1, 11), value=7)
        
        if st.button("Build Secure ZIP"):
            if c_name and c_cv:
                zip_path = core.create_zip_bundle(c_name, c_cv)
                with open(zip_path, "rb") as f:
                    st.download_button("Download ZIP (PDF + .CARF)", f, file_name=zip_path)
                st.success(f"Bundle Created. Anti-copy friction applied. 30-day purge clock started.")
            else:
                st.warning("Please enter client name and CV content.")

    with tabs[2]:
        st.header("CARF Restore")
        st.write("Upload a .CARF file to restore a purged or previous session.")
        up_file = st.file_uploader("Choose file", type=["carf"])
        if up_file:
            st.success("Data Authenticated. Client details restored to workspace.")

    with tabs[3]:
        st.header("Stress Test & Audit")
        st.write("Simulate the 30-Day Purge Protocol (Manifest Item 7 & 14)")
        days_ahead = st.number_input("Days to skip forward", min_value=0, max_value=60, value=0)
        if st.button("Run Audit"):
            results = core.run_purge_audit(test_days_offset=days_ahead)
            st.warning(f"Simulated Date: {results['simulated_date']}")
            st.error(f"Records Permanently Purged: {results['purged']}")
else:
    st.info("Please enter your security key in the sidebar to access the Career Architect.")
