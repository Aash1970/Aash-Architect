# VERSION 7.9.0 | CAREER ARCHITECT UI | STATUS: FORCED FORM LOCK
# COPYRIGHT © 2026 ALL RIGHTS RESERVED

import streamlit as st
from architect_core import ArchitectCore

core = ArchitectCore()
st.set_page_config(page_title=f"Career Architect {core.version}")

st.title("Career Architect")

# Initialize authentication state
if 'auth' not in st.session_state:
    st.session_state.auth = False

with st.sidebar:
    st.header("System Access")
    
    # Using a Form to FORCE the button to work
    with st.form("auth_form"):
        key_input = st.text_input("Enter Security Key", type="password")
        submit_button = st.form_submit_button("Unlock System")
        
        if submit_button:
            # Matches hash for 'AashArchitect2026!'
            if core.get_hash(key_input) == "c7ad4411ac76b744d9365c71d605058866196236688d617c0a875a55745d65457f62":
                st.session_state.auth = True
                st.success("AUTHENTICATED")
            else:
                st.error("Invalid Key")

if st.session_state.auth:
    t1, t2, t3 = st.tabs(["Market Intel", "Export Bundle", "Audit"])
    
    with t1:
        st.subheader("Adzuna Live Feed")
        q = st.text_input("Job Keywords", value="Manager")
        if st.button("Search Market"):
            jobs = core.get_market_intel(q)
            if not jobs:
                st.warning("No results found or API error.")
            for j in jobs:
                st.markdown(f"**{j['title']}** ({j['location']['display_name']})")
                st.write(f"[Link to Job]({j['redirect_url']})")
                st.write("---")

    with t2:
        st.subheader("Export Client Bundle")
        c_name = st.text_input("Client Name")
        c_cv = st.text_area("Paste CV")
        c_rate = st.select_slider("Suitability", options=range(1, 11), value=7)
        if st.button("Generate ZIP"):
            if c_name and c_cv:
                p = core.create_bundle(c_name, c_cv, c_rate)
                with open(p, "rb") as f:
                    st.download_button("Download ZIP", f, file_name=p)
    
    if st.button("Log Out"):
        st.session_state.auth = False
        st.rerun()
else:
    st.warning("SYSTEM LOCKED: Please enter the key in the sidebar and click 'Unlock System'.")

# MANDATORY VERSIONED FOOTER
st.markdown("---")
st.write(f"Copyright © 2026 Career Architect | Version {core.version} | ACCESS RESTRICTED")
