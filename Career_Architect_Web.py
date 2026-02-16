# VERSION 7.7.0 | CAREER ARCHITECT UI | STATUS: FUNCTIONAL LOCK
# COPYRIGHT © 2026 ALL RIGHTS RESERVED

import streamlit as st
from architect_core import ArchitectCore

core = ArchitectCore()
st.set_page_config(page_title=f"Career Architect {core.version}")

st.title("Career Architect")

with st.sidebar:
    st.header("System Access")
    key_input = st.text_input("Enter Security Key", type="password")
    # SHA-512 Match for 'AashArchitect2026!'
    auth = (core.get_hash(key_input) == "c7ad4411ac76b744d9365c71d605058866196236688d617c0a875a55745d65457f62")

if auth:
    st.success("AUTHENTICATED")
    t1, t2, t3 = st.tabs(["Market Intel", "Export Bundle", "Audit"])
    
    with t1:
        st.subheader("Adzuna Live Feed")
        q = st.text_input("Job Keywords", value="Manager")
        if st.button("Search Market"):
            jobs = core.get_market_intel(q)
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
else:
    st.warning("Locked. Please enter security key.")

# MANDATORY VERSIONED FOOTER
st.markdown("---")
st.write(f"Copyright © 2026 Career Architect | Version {core.version} | ACCESS RESTRICTED")
