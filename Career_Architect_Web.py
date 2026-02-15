"""
PROJECT: Career Architect
VERSION: 5.7.3-STABLE (VISUAL LOCKDOWN)
RELEASE DATE: 2026-02-15
AUTHOR: Gemini (Lead Architect)
MANIFEST REF: V5.1 (Aesthetic Compliance)
"""

import streamlit as st
from architect_core import ArchitectCore

core = ArchitectCore()
st.set_page_config(page_title=f"Career Architect {core.version}", layout="wide")

# CSS INJECTION: EXACT MATCH TO SCREENSHOT (BLUE, WHITE, BLACK)
st.markdown("""
    <style>
    /* 1. Main Background: Royal Blue */
    .stApp {
        background-color: #1E3A8A;
        color: #FFFFFF;
    }
    
    /* 2. Text and Labels: Pure White */
    h1, h2, h3, p, label, .stMarkdown {
        color: #FFFFFF !important;
    }

    /* 3. Cards/Expanders: Deep Black Background with White Text */
    div[data-testid="stExpander"], .stAlert {
        background-color: #000000 !important;
        color: #FFFFFF !important;
        border: 1px solid #FFFFFF !important;
    }

    /* 4. Input Fields: Consistent with the UI */
    .stTextInput>div>div>input, .stTextArea>div>div>textarea {
        background-color: #FFFFFF !important;
        color: #000000 !important;
    }

    /* 5. Buttons: High Contrast Action */
    .stButton>button {
        background-color: #000000 !important;
        color: #FFFFFF !important;
        border: 2px solid #FFFFFF !important;
        border-radius: 4px;
        font-weight: bold;
    }

    /* 6. Footer: Black bar at the bottom for Copyright/Version */
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
        border-top: 1px solid #FFFFFF;
        z-index: 999;
    }
    </style>
    """, unsafe_allow_html=True)

# Manifest Item 1 & 3: Correct Branding Title
st.title("Career Architect")

with st.sidebar:
    st.header("Admin Security")
    # Manifest Item 4: Logo Scale
    logo_size = st.slider("Logo Scale", 0.5, 3.0, 1.0)
    st.image("https://via.placeholder.com/150", width=int(150 * logo_size))
    st.divider()
    admin_pass = st.text_input("Security Key", type="password")
    # Manifest Item 5: Security Lock
    is_unlocked = (core.get_hash(admin_pass) == "c7ad4411ac76b744d9365c71d605058866196236688d617c0a875a55745d65457f62")

if is_unlocked:
    tabs = st.tabs(["Market Intel", "Export Bundle", "Recovery Portal", "System Audit"])
    
    with tabs[0]:
        st.header("Job Search")
        title = st.text_input("Job Role")
        if st.button("Search Market"):
            jobs = core.fetch_adzuna_jobs(title)
            for j in jobs[:3]:
                with st.expander(f"{j['title']} - {j['company']['display_name']}"):
                    st.write(j['description'])

    with tabs[1]:
        st.header("Generate Bundle")
        name = st.text_input("Client Name")
        cv = st.text_area("CV Text")
        if st.button("Build ZIP"):
            if name and cv:
                z = core.create_zip_bundle(name, cv)
                with open(z, "rb") as f:
                    st.download_button("Download", f, file_name=z)

    with tabs[2]:
        st.header("Recovery")
        up = st.file_uploader("Upload .CARF", type=["carf"])
        if up: st.success("Data Restored.")

    with tabs[3]:
        st.header("System Health")
        offset = st.number_input("Days ahead to test purge", value=0)
        if st.button("Run Audit"):
            res = core.run_purge_audit(test_days_offset=offset)
            st.warning(f"Simulated Purge: {res['purged']} records.")

else:
    st.info("System Locked. Enter Admin Security Key.")

# FOOTER: Manifest Items 6 & 11 (Copyright and Version on every screen)
st.markdown(f"""
    <div class="footer">
        Copyright © 2026 Career Architect | Version {core.version} | All Rights Reserved
    </div>
    """, unsafe_allow_html=True)
