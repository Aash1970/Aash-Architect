import streamlit as st
from architect_core import ArchitectCore

core = ArchitectCore()
st.set_page_config(page_title="Career Architect", layout="wide")

# THE "AASH SAUCE" VISUAL LOCK - FORCING CONTRAST
st.markdown("""
    <style>
    /* 1. Header & Sidebar - MUST BE NAVY WITH WHITE TEXT */
    [data-testid="stHeader"], [data-testid="stSidebar"] {
        background-color: #0A192F !important;
    }
    
    /* Force all text in sidebar to be WHITE */
    [data-testid="stSidebar"] * {
        color: #FFFFFF !important;
    }

    /* 2. Main Title - WHITE FONT ON NAVY */
    .main-title {
        background-color: #0A192F;
        color: #FFFFFF !important;
        padding: 20px;
        text-align: center;
        border-bottom: 3px solid #008080;
        font-family: 'Arial Black';
    }

    /* 3. Work Area - WHITE BACKGROUND WITH BLACK TEXT */
    .stApp {
        background-color: #FFFFFF !important;
    }
    
    .stApp p, .stApp h2, .stApp h3, .stApp label, .stApp span {
        color: #000000 !important;
    }

    /* 4. Input Boxes - Must be visible */
    input {
        background-color: #F0F2F6 !important;
        color: #000000 !important;
    }

    /* 5. The Footer - BLACK WITH WHITE TEXT */
    .footer {
        position: fixed;
        left: 0;
        bottom: 0;
        width: 100%;
        background-color: #000000;
        color: #FFFFFF;
        text-align: center;
        padding: 8px;
        z-index: 999;
    }
    </style>
    """, unsafe_allow_html=True)

st.markdown("<div class='main-title'><h1>Career Architect</h1></div>", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("### System Access")
    # THE PASSCODE IS ENTERED HERE
    pw = st.text_input("Enter Security Key", type="password")
    auth = (core.get_hash(pw) == "c7ad4411ac76b744d9365c71d605058866196236688d617c0a875a55745d65457f62")
    
    if auth:
        st.success("AUTHENTICATED")
        scale = st.slider("Logo Scale", 0.5, 3.0, 1.0)
        st.image("https://via.placeholder.com/150", width=int(150*scale))

if not auth:
    st.error("SYSTEM LOCKED: PLEASE AUTHENTICATE VIA SIDEBAR")
else:
    # REST OF THE PROGRAM TRIGGERS ONLY AFTER AUTH
    tabs = st.tabs(["Market Intel", "Export Bundle", "Recovery", "Audit"])
    
    with tabs[1]:
        st.subheader("Secure Export Bundle")
        # 1-10 Rating Slider as requested
        rating = st.select_slider("Suitability Rating", options=range(1, 11), value=5)
        name = st.text_input("Client Name")
        cv = st.text_area("Paste CV Text", height=300)
        
        if st.button("GENERATE PROTECTED ZIP"):
            file_path = core.create_bundle(name, cv)
            with open(file_path, "rb") as f:
                st.download_button("DOWNLOAD ZIP", f, file_name=file_path)

st.markdown(f"<div class='footer'>Copyright © 2026 Career Architect | Version {core.version}</div>", unsafe_allow_html=True)
