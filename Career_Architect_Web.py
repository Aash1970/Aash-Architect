"""
PROJECT: Career Architect
VERSION: 5.7.4-STABLE (EXACT VISUAL MATCH)
RELEASE DATE: 2026-02-15
"""

import streamlit as st
from architect_core import ArchitectCore

core = ArchitectCore()
st.set_page_config(page_title=f"Career Architect {core.version}", layout="wide")

# CSS: Navy Sidebar/Header, White Body, Black Text
st.markdown("""
    <style>
    /* Sidebar: Deep Navy from Screenshot */
    [data-testid="stSidebar"] {
        background-color: #0A192F;
        color: #FFFFFF;
    }
    
    /* Main Body: Pure White */
    .stApp {
        background-color: #FFFFFF;
        color: #000000;
    }
    
    /* Headers in White on Blue (for Sidebar/Top) */
    .sidebar-text { color: #FFFFFF !important; }
    
    /* Black Text for the Work Area */
    h1, h2, h3, p, label {
        color: #000000 !important;
    }

    /* Footer: Black bar at the bottom */
    .footer {
        position: fixed;
        left: 0;
        bottom: 0;
        width: 100%;
        background-color: #000000;
        color: #FFFFFF;
        text-align: center;
        padding: 5px;
        font-size: 11px;
        z-index: 999;
    }
    </style>
    """, unsafe_allow_html=True)

# SIDEBAR GATE
with st.sidebar:
    st.markdown("<h2 class='sidebar-text'>System Access</h2>", unsafe_allow_html=True)
    admin_pass = st.text_input("Enter Security Key", type="password")
    
    # Check Password (Manifest Item 5)
    is_unlocked = (core.get_hash(admin_pass) == "c7ad4411ac76b744d9365c71d605058866196236688d617c0a875a55745d65457f62")

    if is_unlocked:
        st.success("Admin Verified")
        st.divider()
        # Manifest Item 4: ONLY show logo sliders AFTER login
        logo_size = st.slider("Adjust Logo Scale", 0.5, 3.0, 1.0)
        st.image("https://via.placeholder.com/150", width=int(150 * logo_size))
    else:
        st.warning("Please enter key to reveal Admin Tools.")

# MAIN WORK AREA
st.title("Career Architect")

if is_unlocked:
    tabs = st.tabs(["Market Intel", "Export Bundle", "Recovery Portal", "System Audit"])
    
    with tabs[0]:
        st.header("Live Job Search")
        title = st.text_input("Target Role")
        if st.button("Search"):
            jobs = core.fetch_adzuna_jobs(title)
            for j in jobs[:3]: st.write(f"**{j['title']}** - {j['company']['display_name']}")

    with tabs[1]:
        st.header("Generate Secure Bundle")
        name = st.text_input("Client Name")
        cv = st.text_area("Paste CV Content")
        if st.button("Build ZIP"):
            z = core.create_zip_bundle(name, cv)
            with open(z, "rb") as f: st.download_button("Download", f, file_name=z)

else:
    # This is what the user sees BEFORE logging in
    st.info("Welcome to Career Architect. Please use the sidebar to authenticate and begin.")

# FOOTER (Manifest Item 6)
st.markdown(f"""
    <div class="footer">
        Copyright © 2026 Career Architect | Version {core.version} | All Rights Reserved
    </div>
    """, unsafe_allow_html=True)
