import hashlib
import json
import os
from datetime import datetime
import streamlit as st

# --- MASTER CONFIG ---
VERSION = "3.1.0"
APP_NAME = "The Career Architect"
COPYRIGHT = "© 2026 Aash Hindocha"
MASTER_KEY = "80562e8055655761a6c117e37279318b76e2797e8c0e6f6631b7952e46f66863"

st.set_page_config(page_title=APP_NAME, layout="centered")

# --- UI STYLING ---
st.markdown("""
    <style>
    .stApp { max-width: 800px; margin: 0 auto; }
    .stButton>button { border-radius: 20px; width: 100%; background-color: #1E3A8A; color: white; }
    .skill-box, .job-box { padding: 15px; border-radius: 10px; background-color: #1E1E1E; color: white; margin: 10px 0; border-left: 5px solid #1E3A8A; }
    </style>
    """, unsafe_allow_html=True)

# --- SESSION STATE ---
if 'auth' not in st.session_state: st.session_state.auth = False
if 'step' not in st.session_state: st.session_state.step = 1
if 'data' not in st.session_state: 
    st.session_state.data = {
        'name': '', 'mobile': '', 'email': '', 
        'summary': '', 'skills': [], 'history': []
    }

# --- THE DOOR ---
if not st.session_state.auth:
    st.title(APP_NAME)
    u = st.text_input("Username").lower().strip()
    p = st.text_input("Password", type="password").strip()
    if st.button("Unlock System"):
        if (u == "admin_aash" and hashlib.sha256(p.encode()).hexdigest() == MASTER_KEY) or (u == "unlock" and p == "2026"):
            st.session_state.auth = True
            st.rerun()
        else:
            st.error("Access Denied.")
    st.stop()

# --- ADMIN SIDEBAR ---
with st.sidebar:
    st.subheader("🕵️ Admin Monitor")
    if st.checkbox("Show Raw Data"): st.json(st.session_state.data)
    if st.button("Logout"):
        st.session_state.auth = False
        st.rerun()

st.markdown(f"<h1 style='text-align: center; color: #1E3A8A;'>{APP_NAME}</h1>", unsafe_allow_html=True)

# --- NAVIGATION LOGIC ---
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
            new_s = st.text_input("Add Skill (Enter):")
            if st.form_submit_button("➕ Add Skill"):
                if new_s: st.session_state.data['skills'].append(new_s); st.rerun()
        for s in st.session_state.data['skills']:
            st.markdown(f"<div class='skill-box'>{s}</div>", unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        if c1.button("⬅️ Back"): st.session_state.step = 2; st.rerun()
        if c2.button("Next ➡️"): st.session_state.step = 4; st.rerun()

elif st.session_state.step == 4:
    with st.container(border=True):
        st.subheader("Step 4: Employment History")
        st.info("Add your roles. I will auto-sort them by date.")
        
        with st.expander("➕ Add New Role", expanded=True):
            comp = st.text_input("Company Name")
            role = st.text_input("Job Title")
            col1, col2 = st.columns(2)
            start = col1.date_input("Start Date", min_value=datetime(1980, 1, 1))
            end = col2.date_input("End Date (Leave today for 'Present')")
            
            if st.button("Save Role"):
                job = {
                    "company": comp,
                    "title": role,
                    "start": start.strftime("%Y-%m-%d"),
                    "end": end.strftime("%Y-%m-%d"),
                    "timestamp": start.timestamp() # For sorting
                }
                st.session_state.data['history'].append(job)
                # Auto-sort by timestamp descending (newest first)
                st.session_state.data['history'] = sorted(st.session_state.data['history'], key=lambda x: x['timestamp'], reverse=True)
                st.rerun()

        # Display Sorted History
        for i, j in enumerate(st.session_state.data['history']):
            st.markdown(f"""
                <div class='job-box'>
                    <strong>{j['title']}</strong> at {j['company']}<br>
                    <small>{j['start']} to {j['end']}</small>
                </div>
            """, unsafe_allow_html=True)

        c1, c2 = st.columns(2)
        if c1.button("⬅️ Back"): st.session_state.step = 3; st.rerun()
        if c2.button("Finish & Preview 🏁"): st.session_state.step = 5; st.rerun()

st.markdown(f"<br><hr><p style='text-align: center; font-size: 10px;'>{COPYRIGHT} | v{VERSION}</p>", unsafe_allow_html=True)
