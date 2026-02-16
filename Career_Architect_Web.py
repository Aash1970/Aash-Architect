import streamlit as st
from architect_core import ArchitectCore

# Initialize
core = ArchitectCore()
st.set_page_config(page_title="Career Architect", layout="wide")

# FORCED VISUAL OVERRIDE - THE "NUCLEAR" CSS FIX
st.markdown("""
    <style>
    /* 1. Header & Sidebar - Deep Navy */
    [data-testid="stHeader"], [data-testid="stSidebar"], .st-emotion-cache-6qob1r {
        background-color: #0A192F !important;
    }
    
    /* 2. FORCE WHITE TEXT IN SIDEBAR (So you can see the password label) */
    [data-testid="stSidebar"] p, [data-testid="stSidebar"] label, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {
        color: #FFFFFF !important;
        font-weight: bold !important;
    }

    /* 3. MAIN WORK AREA - Pure White Background */
    .stApp {
        background-color: #FFFFFF !important;
    }
    
    /* 4. FORCE BLACK TEXT IN MAIN AREA (So you can see the messages) */
    .stApp p, .stApp h1, .stApp h2, .stApp h3, .stApp label, .stApp span, .stApp div {
        color: #000000 !important;
    }

    /* 5. THE HEADER TITLE - Forced White on Navy */
    .main-header {
        background-color: #0A192F !important;
        padding: 20px;
        border-bottom: 3px solid #008080;
    }
    .main-header h1 {
        color: #FFFFFF !important;
        margin: 0;
        text-align: center;
    }

    /* 6. PASSWORD INPUT - Force Visibility */
    input {
        background-color: #FFFFFF !important;
        color: #000000 !important;
        border: 2px solid #008080 !important;
    }

    /* 7. FOOTER - Fixed Bottom Black */
    .footer {
        position: fixed;
        left: 0;
        bottom: 0;
        width: 100%;
        background-color: #000000 !important;
        color: #FFFFFF !important;
        text-align: center;
        padding: 10px;
        z-index: 999;
    }
    </style>
    """, unsafe_allow_html=True)

# Custom Header
st.markdown("<div class='main-header'><h1>Career Architect</h1></div>", unsafe_allow_html=True)

# Sidebar Access Control
with st.sidebar:
    st.markdown("## System Access")
    # THE PASSCODE INPUT
    pass_input = st.text_input("Enter Security Key", type="password")
    
    # Secure Hash Check
    auth = (core.get_hash(pass_input) == "c7ad4411ac76b744d9365c71d605058866196236688d617c0a875a55745d65457f62")
    
    if auth:
        st.success("ACCESS GRANTED")
        logo_scale = st.slider("Logo Scale", 0.5, 3.0, 1.0)
        st.image("https://via.placeholder.com/150", width=int(150 * logo_scale))

# Main Logic
if not auth:
    st.warning("SYSTEM LOCKED: Please enter the security key in the sidebar to proceed.")
else:
    tabs = st.tabs(["Market Intel", "Export Bundle", "Client Recovery", "Audit"])
    
    with tabs[1]:
        st.subheader("Secure Client Export")
        c_name = st.text_input("Client Full Name")
        c_cv = st.text_area("Paste CV Text Content", height=300)
        # 1-10 Rating Slider as requested
        suit_rating = st.select_slider("Suitability Rating", options=range(1, 11), value=7)
        
        if st.button("Generate Protected ZIP"):
            if c_name and c_cv:
                zip_path = core.create_bundle(c_name, c_cv)
                with open(zip_path, "rb") as f:
                    st.download_button("Download ZIP Bundle", f, file_name=zip_path)
            else:
                st.error("Please provide both Name and CV.")

# Mandatory Footer
st.markdown(f"<div class='footer'>Copyright © 2026 Career Architect | Version {core.version} | All Rights Reserved</div>", unsafe_allow_html=True)
