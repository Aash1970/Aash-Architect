# VERSION 7.6.0 | CAREER ARCHITECT UI | STATUS: FUNCTIONAL LOCK
import streamlit as st
from architect_core import ArchitectCore

core = ArchitectCore()
st.set_page_config(page_title="Career Architect V7.6.0")

# PLACEHOLDER HEADER (Basic styling for functionality)
st.title("Career Architect")

with st.sidebar:
    st.header("System Access")
    key_input = st.text_input("Enter Security Key", type="password")
    # SHA-512 check for 'AashArchitect2026!'
    auth = (core.get_hash(key_input) == "c7ad4411ac76b744d9365c71d605058866196236688d617c0a875a55745d65457f62")

if auth:
    st.success("AUTHENTICATED")
    tab1, tab2, tab3, tab4 = st.tabs(["Market Intel", "Export Bundle", "Recovery", "Audit"])
    
    with tab1:
        st.subheader("Live Market Intel (Adzuna)")
        query = st.text_input("Search Keywords (e.g. Project Manager London)")
        if st.button("Fetch Market Data"):
            jobs = core.get_market_intel(query)
            for job in jobs:
                st.markdown(f"**{job['title']}** | {job['location']['display_name']}")
                st.write(f"Salary: £{job.get('salary_min', 'N/A')} - URL: {job['redirect_url']}")
                st.write("---")

    with tab2:
        st.subheader("Client Export")
        c_name = st.text_input("Client Name")
        c_cv = st.text_area("Paste CV")
        c_rating = st.select_slider("Suitability Rating", options=range(1, 11), value=7)
        
        if st.button("Generate Protected ZIP"):
            if c_name and c_cv:
                zip_path = core.create_bundle(c_name, c_cv, c_rating)
                with open(zip_path, "rb") as f:
                    st.download_button("Download ZIP", f, file_name=zip_path)

    with tab4:
        st.subheader("System Audit")
        if st.button("Run 30-Day Purge"):
            purged = core.run_purge_audit()
            st.info(f"Purge complete. {purged} records older than 30 days removed.")

else:
    st.warning("Locked. Please authenticate via sidebar.")

# VERSIONED FOOTER
st.markdown("---")
st.write(f"Copyright © 2026 Career Architect | Version {core.version}")
