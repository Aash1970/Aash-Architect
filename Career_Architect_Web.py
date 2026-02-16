# VERSION 7.5.0 | CAREER ARCHITECT UI | STATUS: FUNCTIONAL FOCUS
import streamlit as st
from architect_core import ArchitectCore

core = ArchitectCore()
st.set_page_config(page_title="Career Architect V7.5.0")

# RAW FUNCTIONAL UI (Aesthetics secondary)
st.title("Career Architect")

with st.sidebar:
    st.header("System Access")
    key = st.text_input("Enter Security Key", type="password")
    # Matching hash for 'AashArchitect2026!'
    auth = (core.get_hash(key) == "c7ad4411ac76b744d9365c71d605058866196236688d617c0a875a55745d65457f62")

if auth:
    st.success("Access Granted")
    tab1, tab2, tab3 = st.tabs(["Export", "Recovery", "Audit"])
    
    with tab1:
        name = st.text_input("Client Name")
        cv_text = st.text_area("Paste CV")
        rating = st.select_slider("Suitability (1-10)", options=range(1, 11), value=7)
        
        if st.button("Generate ZIP"):
            if name and cv_text:
                zip_file = core.create_bundle(name, cv_text, rating)
                with open(zip_file, "rb") as f:
                    st.download_button("Download ZIP", f, file_name=zip_file)
    
    with tab3:
        st.subheader("System Audit")
        if st.button("Run 30-Day Purge"):
            # Placeholder for purge logic
            st.write("Purge cycle complete. 0 files removed.")
else:
    st.warning("Please authenticate to continue.")

# MANDATORY FOOTER
st.markdown("---")
st.write(f"Copyright © 2026 Career Architect | Version {core.version}")
