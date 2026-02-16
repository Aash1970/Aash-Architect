# CAREER ARCHITECT WEB UI - VERSION 6.2.0
# LAST UPDATED: 2026-02-16

import streamlit as st
from architect_core import ArchitectCore

core = ArchitectCore()
st.set_page_config(page_title="Career Architect", layout="wide")

# FORCED VISUAL DNA (AASH SAUCE)
st.markdown("""
    <style>
    /* 1. Header & Sidebar: Deep Navy */
    [data-testid="stHeader"], [data-testid="stSidebar"] {
        background-color: #0A192F !important;
    }
    
    /* 2. SIDEBAR TEXT: Force Bold White */
    [data-testid="stSidebar"] p, [data-testid="stSidebar"] label, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {
        color: #FFFFFF !important;
        font-weight: bold !important;
        font-size: 1.1rem !important;
    }

    /* 3. MAIN WORK AREA: Pure White */
    .stApp {
        background-color: #FFFFFF !important;
    }

    /* 4. MAIN AREA TEXT: Force Pure Black */
    .stApp p, .stApp h1, .stApp h2, .stApp h3, .stApp label, .stApp span, .stApp div {
        color: #000000 !important;
        font-weight: 600 !important;
    }

    /* 5. INPUT BOXES: Force Visibility with Border */
    input {
        background-color: #F0F2F6 !important;
        color: #000000 !important;
        border: 2px solid #008080 !important;
    }

    /* 6. BUTTONS: Teal with White Text */
    .stButton>button {
        background-color: #008080 !important;
        color: #FFFFFF !important;
        border: 2px solid #000000 !important;
        font-weight: bold;
    }

    /* 7. THE HEADER TITLE BAR */
    .header-box {
        background-color: #0A192F;
        padding: 20px;
        text-align: center;
        border-bottom: 5px solid #008080;
    }
    .header-box h1 {
        color: #FFFFFF !important;
        margin: 0;
    }

    /* 8. FOOTER: Black/White */
    .footer {
        position: fixed;
        left: 0;
        bottom: 0;
        width: 100%;
        background-color: #000000;
        color: #FFFFFF !important;
        text-align: center;
        padding: 10px;
        z-index: 999;
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

# Custom Header
st.markdown("<div class='header-box'><h1>Career Architect</h1></div>", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("## System Access")
    # THE PASSCODE INPUT (Label now forced White)
    user_key = st.text_input("Enter Security Key", type="password")
    auth = (core.get_hash(user_key) == "c7ad4411ac76b744d9365c71d605058866196236688d617c0a875a55745d65457f62")
    
    if auth:
        st.success("AUTHENTICATED")
        scale = st.slider("Logo Scale", 0.5, 3.0, 1.0)
        st.image("https://via.placeholder.com/150", width=int(150*scale))

if not auth:
    st.warning("SYSTEM LOCKED: Please enter the security key in the sidebar.")
else:
    tabs = st.tabs(["Market Intel", "Export Bundle", "Recovery", "Audit"])
    
    with tabs[1]:
        st.subheader("Secure Client Export")
        c_name = st.text_input("Client Full Name")
        c_cv = st.text_area("Paste CV Text", height=300)
        # 1-10 Slider as requested
        rating = st.select_slider("Suitability Rating", options=range(1, 11), value=7)
        
        if st.button("Generate ZIP Bundle"):
            path = core.create_bundle(c_name, c_cv)
            with open(path, "rb") as f:
                st.download_button("Download ZIP", f, file_name=path)

# MANDATORY VERSIONED FOOTER
st.markdown(f"<div class='footer'>Copyright © 2026 Career Architect | Version {core.version} | ACCESS RESTRICTED</div>", unsafe_allow_html=True)
