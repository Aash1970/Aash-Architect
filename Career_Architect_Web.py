import streamlit as st
from architect_core import ArchitectCore

# 1. INITIALIZE CORE (Contains the version v6.0.0)
core = ArchitectCore()
st.set_page_config(page_title="Career Architect", layout="wide")

# 2. THE NUCLEAR CSS OVERRIDE (FORCING VISIBILITY)
st.markdown("""
    <style>
    /* Force Navy Sidebar with BOLD WHITE TEXT */
    [data-testid="stSidebar"], [data-testid="stHeader"] {
        background-color: #0A192F !important;
    }
    [data-testid="stSidebar"] p, [data-testid="stSidebar"] label, [data-testid="stSidebar"] h2 {
        color: #FFFFFF !important;
        font-weight: bold !important;
    }

    /* Force Pure White Main Area with PURE BLACK TEXT */
    .stApp {
        background-color: #FFFFFF !important;
    }
    .stApp p, .stApp h1, .stApp h2, .stApp h3, .stApp label, .stApp span {
        color: #000000 !important;
        font-weight: 600 !important;
    }

    /* Force Password Box to be Visible */
    input {
        background-color: #F0F2F6 !important;
        color: #000000 !important;
        border: 2px solid #008080 !important;
    }

    /* The Header Title Bar */
    .header-box {
        background-color: #0A192F;
        padding: 20px;
        text-align: center;
        border-bottom: 5px solid #008080;
    }
    .header-box h1 {
        color: #FFFFFF !important;
    }

    /* THE MANDATORY FOOTER (Restored Versioning) */
    .footer {
        position: fixed;
        left: 0;
        bottom: 0;
        width: 100%;
        background-color: #000000;
        color: #FFFFFF !important;
        text-align: center;
        padding: 10px;
        font-weight: bold;
        z-index: 999;
    }
    </style>
    """, unsafe_allow_html=True)

# 3. RENDER UI
st.markdown("<div class='header-box'><h1>Career Architect</h1></div>", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("## System Access")
    # This label WILL be white and visible now
    user_key = st.text_input("Enter Security Key", type="password")
    
    # Validation against the hash
    auth = (core.get_hash(user_key) == "c7ad4411ac76b744d9365c71d605058866196236688d617c0a875a55745d65457f62")
    
    if auth:
        st.success("AUTHENTICATED")
        scale = st.slider("Logo Scale", 0.5, 3.0, 1.0)
        st.image("https://via.placeholder.com/150", width=int(150*scale))

if not auth:
    st.warning("SYSTEM LOCKED: Please authenticate via the sidebar to access the Architect.")
else:
    # Authenticated Tabs
    t1, t2, t3, t4 = st.tabs(["Market Intel", "Export Bundle", "Recovery", "Audit"])
    
    with t2:
        st.subheader("Client Export Bundle")
        name = st.text_input("Full Client Name")
        cv_text = st.text_area("Paste CV Here", height=300)
        # Rating Slider 1-10
        rating = st.select_slider("Suitability Rating", options=range(1, 11), value=7)
        
        if st.button("GENERATE ZIP BUNDLE"):
            path = core.create_bundle(name, cv_text)
            with open(path, "rb") as f:
                st.download_button("Download Secure ZIP", f, file_name=path)

# 4. RESTORED VERSIONED FOOTER
st.markdown(f"<div class='footer'>Copyright © 2026 Career Architect | Version {core.version} | ACCESS RESTRICTED</div>", unsafe_allow_html=True)
