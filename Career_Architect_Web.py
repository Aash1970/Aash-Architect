import hashlib
import json
import os
import streamlit as st

# --- MASTER CONFIG ---
VERSION = "3.0.9"
APP_NAME = "The Career Architect"
COPYRIGHT = "© 2026 Aash Hindocha"
MASTER_KEY = "80562e8055655761a6c117e37279318b76e2797e8c0e6f6631b7952e46f66863"

st.set_page_config(page_title=APP_NAME, layout="centered")

# --- UI STYLING ---
st.markdown("""
    <style>
    .stApp { max-width: 800px; margin: 0 auto; }
    .stButton>button { border-radius: 20px; width: 100%; background-color: #1E3A8A; color: white; }
    .skill-box { padding: 10px; border-radius: 10px; background-color: #1E1E1E; color: white; margin: 5px 0; border-left: 5px solid #1E3A8A; }
    </style>
    """, unsafe_allow_html=True)

# --- SESSION STATE ---
if 'auth' not in st.session_state: st.session_state.auth = False
if 'step' not in st.session_state: st.session_state.step = 1
if 'data' not in st.session_state: 
    st.session_state.data = {'name': '', 'mobile': '', 'email': '', 'summary': '', 'skills': []}

# --- THE DOOR (v3.0.9) ---
if not st.session_state.auth:
    st.title(APP_NAME)
    u = st.text_input("Username").lower().strip()
    p = st.text_input("Password", type="password").strip()
    
    if st.button("Unlock System"):
        # PRIMARY LOGIN
        if u == "admin_aash" and hashlib.sha256(p.encode()).hexdigest() == MASTER_KEY:
            st.session_state.auth = True
            st.rerun()
        # EMERGENCY BYPASS (Use this if the above fails)
        elif u == "unlock" and p == "2026":
            st.session_state.auth = True
            st.rerun()
        else:
            st.error("Access Denied. Try the Bypass: unlock / 2026")
    st.stop()

# --- THE WIZARD ---
st.markdown(f"<h1 style='text-align: center; color: #1E3A8A;'>{APP_NAME}</h1>", unsafe_allow_html=True)

# ADMIN SIDEBAR
with st.sidebar:
    st.subheader("Admin Console")
    if st.button("Logout"):
        st.session_state.auth = False
        st.rerun()

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
        summ = st.text_area("Summary:", value=st.session_state.data['summary'], height=200)
        c1, c2 = st.columns(2)
        if c1.button("⬅️ Back"): st.session_state.step = 1; st.rerun()
        if c2.button("Next ➡️"):
            st.session_state.data['summary'] = summ
            st.session_state.step = 3
            st.rerun()

elif st.session_state.step == 3:
    with st.container(border=True):
        st.subheader("Step 3: Key Skills")
        with st.form("skill_form", clear_on_submit=True):
            new_s = st.text_input("Add Skill:")
            if st.form_submit_button("➕ Add Skill"):
                if new_s and len(st.session_state.data['skills']) < 10:
                    st.session_state.data['skills'].append(new_s)
                    st.rerun()
        for i, s in enumerate(st.session_state.data['skills']):
            st.markdown(f"<div class='skill-box'>{i+1}. {s}</div>", unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        if c1.button("⬅️ Back"): st.session_state.step = 2; st.rerun()
        if c2.button("Next ➡️"):
            st.write("Ready for Step 4")

st.markdown(f"<br><hr><p style='text-align: center; font-size: 10px;'>{COPYRIGHT} | v{VERSION}</p>", unsafe_allow_html=True)
