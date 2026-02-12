import hashlib
import json
import os
import re
import streamlit as st

# --- MASTER CONFIG (LOCKED) ---
VERSION = "3.0.6"
APP_NAME = "The Career Architect"
COPYRIGHT = "© 2026 Aash Hindocha"
REGISTRY_FILE = "registry.json"
# This is the iron-clad hash for 'architect2026'
MASTER_KEY = "80562e8055655761a6c117e37279318b76e2797e8c0e6f6631b7952e46f66863"

# --- UI STYLING ---
st.set_page_config(page_title=APP_NAME, layout="centered")
st.markdown("""
    <style>
    .stApp { max-width: 800px; margin: 0 auto; }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stButton>button { border-radius: 20px; width: 100%; height: 3em; background-color: #1E3A8A; color: white; }
    .skill-box { padding: 12px; border-radius: 10px; background-color: #1E1E1E; color: white; margin: 5px 0; border-left: 5px solid #1E3A8A; }
    </style>
    """, unsafe_allow_html=True)

# --- SESSION STATE ---
if 'auth' not in st.session_state: st.session_state.update({'auth': False, 'user': None, 'level': 0})
if 'step' not in st.session_state: st.session_state.step = 1
if 'data' not in st.session_state: 
    st.session_state.data = {'name': '', 'mobile': '', 'email': '', 'summary': '', 'skills': []}

# --- LOGIN GATE (HARD-CODED OVERRIDE) ---
if not st.session_state.auth:
    st.markdown(f"<h1 style='text-align: center; color: #1E3A8A;'>{APP_NAME}</h1>", unsafe_allow_html=True)
    with st.container(border=True):
        u_in = st.text_input("Username").lower().strip()
        p_in = st.text_input("Password", type="password").strip()
        
        if st.button("Unlock System"):
            # Check Master Key directly first
            if u_in == "admin_aash" and hashlib.sha256(p_in.encode()).hexdigest() == MASTER_KEY:
                st.session_state.update({'auth': True, 'user': u_in, 'level': 3})
                st.rerun()
            else:
                # Fallback to registry for other users
                if os.path.exists(REGISTRY_FILE):
                    with open(REGISTRY_FILE, "r") as f:
                        reg = json.load(f)
                    user_data = reg.get(u_in)
                    if user_data and hashlib.sha256(p_in.encode()).hexdigest() == user_data['hash']:
                        st.session_state.update({'auth': True, 'user': u_in, 'level': user_data['level']})
                        st.rerun()
                st.error("Access Denied: Check credentials.")
    st.stop()

# --- ADMIN AUDITOR ---
if st.session_state.level == 3:
    with st.sidebar:
        st.subheader("🕵️ Admin Monitor")
        if st.checkbox("Show Live Data"): st.json(st.session_state.data)
        if st.button("Reset Session"):
            st.session_state.step = 1
            st.session_state.data = {'name': '', 'mobile': '', 'email': '', 'summary': '', 'skills': []}
            st.rerun()
        if st.button("Logout"):
            st.session_state.auth = False
            st.rerun()

# --- THE WIZARD ---
st.markdown(f"<h1 style='text-align: center; color: #1E3A8A;'>{APP_NAME}</h1>", unsafe_allow_html=True)

if st.session_state.step == 1:
    with st.container(border=True):
        st.subheader("Step 1: Personal Information")
        n = st.text_input("Full Name", value=st.session_state.data['name'])
        m = st.text_input("Mobile Number", value=st.session_state.data['mobile'])
        e = st.text_input("Email Address", value=st.session_state.data['email'])
        if st.button("Next ➡️"):
            st.session_state.data.update({'name': n, 'mobile': m, 'email': e})
            st.session_state.step = 2
            st.rerun()

elif st.session_state.step == 2:
    with st.container(border=True):
        st.subheader("Step 2: Personal Summary")
        st.caption("AI Guidance: Basic | Intermediate | Professional")
        summ = st.text_area("Summary:", value=st.session_state.data['summary'], height=200)
        c1, c2 = st.columns(2)
        if c1.button("⬅️ Back"): st.session_state.step = 1; st.rerun()
        if c2.button("Next ➡️"):
            st.session_state.data['summary'] = summ
            st.session_state.step = 3
            st.rerun()

elif st.session_state.step == 3:
    with st.container(border=True):
        st.subheader("Step 3: Key Skills (Max 10)")
        with st.form("skill_form", clear_on_submit=True):
            new_s = st.text_input("Add Skill (Press Enter):")
            if st.form_submit_button("➕ Add Skill"):
                if new_s and len(st.session_state.data['skills']) < 10:
                    st.session_state.data['skills'].append(new_s)
                    st.rerun()
        
        for i, s in enumerate(st.session_state.data['skills']):
            st.markdown(f"<div class='skill-box'>{i+1}. {s}</div>", unsafe_allow_html=True)
            
        c1, c2 = st.columns(2)
        if c1.button("⬅️ Back"): st.session_state.step = 2; st.rerun()
        if c2.button("Next ➡️"): st.session_state.step = 4; st.rerun()

st.markdown(f"<br><hr><p style='text-align: center; font-size: 10px;'>{COPYRIGHT} | v{VERSION}</p>", unsafe_allow_html=True)
