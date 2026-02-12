import streamlit as st
import hashlib

# --- ARCHITECT MANIFEST ---
VERSION = "2.4.0-WEB"
ADMIN_H = "f67341885542f741697275817d3d0f04e0e5671a5390c54170366164d1421696"

st.set_page_config(page_title="Career Architect Secure Portal", layout="wide")

# --- AUTHENTICATION ---
if 'auth' not in st.session_state:
    st.session_state['auth'] = False

if not st.session_state['auth']:
    st.title("🔐 Secure Access Portal")
    pw = st.text_input("Enter Access Key", type="password")
    if st.button("Unlock Suite"):
        if hashlib.sha256(pw.encode()).hexdigest() == ADMIN_H:
            st.session_state['auth'] = True
            st.rerun()
        else:
            st.error("Access Denied.")
else:
    st.title("🏗️ Career Architect: Web-Link v2.4.0")
    
    tab1, tab2 = st.tabs(["Resilience ROI", "LinkedIn Sauce"])
    
    with tab1:
        st.header("Human Resilience Engine")
        st.write("Translating life experience into 2026 UK Professional ROI.")
        scenario = st.selectbox("Select Life Scenario:", ["Bereavement/Estate", "Health Recovery", "Sandwich Care", "Divorce/Relocation", "Childbirth/Early Years"])
        st.info("Strategy: Frame the gap as an intentional project of crisis management.")
        
    with tab2:
        st.header("LinkedIn 'About' Sauce")
        st.text_area("Copy-Paste Field:", "Ready for generation...")
        st.button("Generate for LinkedIn")

    if st.sidebar.button("Logout"):
        st.session_state['auth'] = False
        st.rerun()