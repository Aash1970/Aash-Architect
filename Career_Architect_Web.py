# CAREER ARCHITECT WEB UI - VERSION 6.5.0
# STATUS: AUDITED & SYNCHRONIZED
# LOG: FIXED SIDEBAR CONTRAST & RESTORED HEADERS

import streamlit as st
from architect_core import ArchitectCore

core = ArchitectCore()
st.set_page_config(page_title="Career Architect", layout="wide")

# THE NUCLEAR CSS (FORCED VISIBILITY)
st.markdown("""
    <style>
    [data-testid="stHeader"], [data-testid="stSidebar"] { background-color: #0A192F !important; }
    
    /* SIDEBAR TEXT: WHITE */
    [data-testid="stSidebar"] p, [data-testid="stSidebar"] label, [data-testid="stSidebar"] h2 {
        color: #FFFFFF !important;
        font-weight: bold !important;
    }

    /* MAIN AREA: BLACK TEXT ON WHITE */
    .stApp { background-color: #FFFFFF !important; }
    .stApp p, .stApp h1, .stApp h2, .stApp h3, .stApp label, .stApp span {
        color: #000000 !important;
        font-weight: 700 !important;
    }

    /* INPUTS & SLIDERS */
    input { background-color: #F0F2F6 !important; color: #000000 !important; border: 2px solid #008080 !important; }
    
    .footer {
        position: fixed; left: 0; bottom: 0; width: 100%;
        background-color: #000000; color: #FFFFFF !important;
        text-align: center; padding: 10px; z-index: 999; font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

st.markdown("<h1 style='color:white; background-color:#0A192F; padding:15px; text-align:center;'>Career Architect</h1>", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("## System Access")
    user_key = st.text_input("Enter Security Key", type="password")
    auth = (core.get_hash(user_key) == "c7ad4411ac76b744d9365c71d605058866196236688d617c0a875a55745d65457f62")
    
    if auth:
        st.success("AUTHENTICATED")
        scale = st.slider("Logo Scale", 0.5, 3.0, 1.0)
        st.image("https://via.placeholder.com/150", width=int(150*scale))

if not auth:
    st.warning("SYSTEM LOCKED: Please authenticate in the sidebar.")
else:
    t1, t2, t3, t4 = st.tabs(["Market Intel", "Export Bundle", "Recovery", "Audit"])
    
    with t2:
        st.subheader("Client Export Bundle")
        name = st.text_input("Full Client Name")
        cv_text = st.text_area("Paste CV Here", height=300)
        # THE 1-10 SLIDER
        rating = st.select_slider("Suitability Rating", options=range(1, 11), value=7)
        
        if st.button("GENERATE ZIP BUNDLE"):
            path = core.create_bundle(name, cv_text)
            with open(path, "rb") as f:
                st.download_button("Download Secure ZIP", f, file_name=path)

st.markdown(f"<div class='footer'>Copyright © 2026 Career Architect | Version {core.version} | ACCESS RESTRICTED</div>", unsafe_allow_html=True)
