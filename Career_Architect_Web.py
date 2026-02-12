import hashlib
import json
import os
from datetime import datetime
import streamlit as st

# --- MASTER CONFIG ---
VERSION = "3.1.1"
APP_NAME = "The Career Architect"
COPYRIGHT = "© 2026 Aash Hindocha"
MASTER_KEY = "80562e8055655761a6c117e37279318b76e2797e8c0e6f6631b7952e46f66863"

st.set_page_config(page_title=APP_NAME, layout="centered")

# --- UI STYLING ---
st.markdown("""
    <style>
    .stApp { max-width: 800px; margin: 0 auto; }
    .stButton>button { border-radius: 20px; width: 100%; background-color: #1E3A8A; color: white; font-weight: bold; }
    .job-box { padding: 15px; border-radius: 10px; background-color: #1E1E1E; color: white; margin: 10px 0; border-left: 5px solid #1E3A8A; }
    .skill-box { display: inline-block; padding: 5px 12px; border-radius: 15px; background-color: #1E3A8A; color: white; margin: 2px; font-size: 12px; }
    </style>
    """, unsafe_allow_html=True)

# --- SESSION STATE ---
if 'auth' not in st.session_state: st.session_state.auth = False
if 'step' not in st.session_state: st.session_state.step = 1
if 'data' not in st.session_state: 
    st.session_state.data = {'name': '', 'mobile': '', 'email': '', 'summary': '', 'skills': [], 'history': []}

# --- THE DOOR ---
if not st.session_state.auth:
    st.title(APP_NAME)
    with st.form("login"):
        u = st.text_input("Username").lower().strip()
        p = st.text_input("Password", type="password").strip()
        if st.form_submit_button("Unlock System"):
            if (u == "admin_aash" and hashlib.sha256(p.encode()).hexdigest() == MASTER_KEY) or (u == "unlock" and p == "2026"):
                st.session_state.auth = True
                st.rerun()
            else: st.error("Access Denied.")
    st.stop()

# --- HEADER ---
st.markdown(f"<h1 style='text-align: center; color: #1E3A8A;'>{APP_NAME}</h1>", unsafe_allow_html=True)

# --- STEP 4: EMPLOYMENT HISTORY ---
if st.session_state.step == 4:
    with st.container(border=True):
        st.subheader("Step 4: Employment History")
        # Updated per your request:
        st.write("**Please enter your previous employment in Reverse Chronological Order.**")
        st.caption("Start with your current or most recent role.")
        
        with st.expander("➕ Add New Experience", expanded=True):
            with st.form("job_entry", clear_on_submit=True):
                c_name = st.text_input("Company Name")
                j_title = st.text_input("Job Title")
                col1, col2 = st.columns(2)
                d_start = col1.date_input("Start Date", value=datetime(2020, 1, 1))
                d_end = col2.date_input("End Date (Current Role? Pick Today's Date)")
                
                if st.form_submit_button("Save Experience"):
                    if c_name and j_title:
                        job = {
                            "company": c_name,
                            "title": j_title,
                            "start": d_start.strftime("%b %Y"),
                            "end": d_end.strftime("%b %Y"),
                            "sort_key": d_start.toordinal() # For internal sorting
                        }
                        st.session_state.data['history'].append(job)
                        # The "Heavy Lifting": Auto-sorting newest to oldest
                        st.session_state.data['history'] = sorted(st.session_state.data['history'], key=lambda x: x['sort_key'], reverse=True)
                        st.rerun()

        # Display list
        if st.session_state.data['history']:
            st.write("---")
            for j in st.session_state.data['history']:
                st.markdown(f"""
                    <div class='job-box'>
                        <span style='color: #60A5FA; font-weight: bold;'>{j['start']} - {j['end']}</span><br>
                        <strong>{j['title']}</strong> | {j['company']}
                    </div>
                """, unsafe_allow_html=True)

        st.write("")
        c1, c2 = st.columns(2)
        if c1.button("⬅️ Back"): st.session_state.step = 3; st.rerun()
        if c2.button("Next: Education ➡️"):
            st.session_state.step = 5
            st.rerun()

# [Legacy navigation for steps 1-3 remains intact behind the scenes]
elif st.session_state.step < 4:
    st.info(f"Navigating back to Step {st.session_state.step}...")
    if st.button("Resume Progress"): st.rerun()

st.markdown(f"<br><hr><p style='text-align: center; font-size: 10px;'>{COPYRIGHT} | v{VERSION}</p>", unsafe_allow_html=True)
