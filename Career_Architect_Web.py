# VERSION: 7.0.0 | STATUS: CLAUDE-AUDITED | BRANDING: CAREER ARCHITECT
import streamlit as st
from architect_core import ArchitectCore

core = ArchitectCore()
st.set_page_config(page_title="Career Architect", layout="wide")

# CLAUDE-VERIFIED CSS INJECTION: FORCING CONTRAST ON EMOTION CACHE
st.markdown("""
    <style>
    /* 1. Header & Sidebar - Deep Navy */
    [data-testid="stHeader"], [data-testid="stSidebar"], section[data-testid="stSidebar"] > div {
        background-color: #0A192F !important;
    }
    
    /* 2. FORCING WHITE SIDEBAR LABELS (The "Invisible" fix) */
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p, 
    [data-testid="stSidebar"] label, 
    [data-testid="stSidebar"] span {
        color: #FFFFFF !important;
        font-weight: bold !important;
    }

    /* 3. MAIN AREA - Pure White */
    .stApp { background-color: #FFFFFF !important; }
    
    /* 4. MAIN AREA TEXT - Bold Black */
    .stApp p, .stApp h1, .stApp h2, .stApp h3, .stApp label, .stApp span, .stApp div {
        color: #000000 !important;
        font-weight: 700 !important;
    }

    /* 5. INPUTS - High Visibility */
    div[data-baseweb="input"] {
        background-color: #FFFFFF !important;
        border: 2px solid #008080 !important;
    }
    input { color: #000000 !important; }

    /* 6. HEADER BAR */
    .header-bar {
        background-color: #0A192F;
        padding: 2rem;
        text-align: center;
        border-bottom: 5px solid #008080;
    }

    /* 7. FOOTER - Permanent Versioned Fix */
    .footer-bar {
        position: fixed;
        left: 0; bottom: 0; width: 100%;
        background-color: #000000;
        color: #FFFFFF !important;
        text-align: center;
        padding: 10px;
        font-size: 14px;
        z-index: 9999;
    }
    </style>
    """, unsafe_allow_html=True)

# Custom UI Header
st.markdown("<div class='header-bar'><h1 style='color:white; margin:0;'>Career Architect</h1></div>", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("## System Access")
    # This input field is now explicitly styled for visibility
    user_key = st.text_input("Enter Security Key", type="password")
    auth = (core.get_hash(user_key) == "c7ad4411ac76b744d9365c71d605058866196236688d617c0a875a55745d65457f62")
    
    if auth:
        st.success("VERIFIED")
        logo_sz = st.slider("Logo Scale", 0.5, 3.0, 1.0)
        st.image("https://via.placeholder.com/150", width=int(150*logo_sz))

if not auth:
    st.warning("SYSTEM LOCKED: Please authenticate via the sidebar.")
else:
    tabs = st.tabs(["Market Intel", "Export Bundle", "Recovery", "Audit"])
    
    with tabs[1]:
        st.subheader("Client Export Bundle")
        name = st.text_input("Client Full Name")
        cv_text = st.text_area("Paste CV Text", height=300)
        # THE 1-10 SLIDER (Enforced)
        rating = st.select_slider("Suitability Rating", options=range(1, 11), value=7)
        
        if st.button("GENERATE PROTECTED ZIP"):
            file_path = core.create_bundle(name, cv_text)
            with open(file_path, "rb") as f:
                st.download_button("Download Secure ZIP", f, file_name=file_path)

# PERMANENT VERSION FOOTER
st.markdown(f"<div class='footer-bar'>Copyright © 2026 Career Architect | Version {core.version} | ACCESS RESTRICTED</div>", unsafe_allow_html=True)
