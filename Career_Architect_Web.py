import hashlib
import json
import os
import streamlit as st
from datetime import datetime, date

# --- MASTER CONFIG (LOCKED) ---
VERSION = "2.9.7"
APP_NAME = "The Career Architect"
COPYRIGHT = "© 2026 Aash Hindocha"
REGISTRY_FILE = "registry.json"
ADMIN_HASH = "440e0a91370aa89083fe9c7cd83db170587dd53fe73aa58fc70a48cc463dfed7"

# --- PERSISTENCE & SESSION STATE ---
if 'step' not in st.session_state: st.session_state.step = 1
if 'profile' not in st.session_state: st.session_state.profile = {}
if 'jobs' not in st.session_state: st.session_state.jobs = []
if 'edu' not in st.session_state: st.session_state.edu = []
if 'skills' not in st.session_state: st.session_state.skills = []

def load_registry():
    if not os.path.exists(REGISTRY_FILE):
        return {"admin_aash": {"hash": ADMIN_HASH, "level": 3, "usage": 9999, "expiry": "2099-12-31"}}
    with open(REGISTRY_FILE, "r") as f:
        return json.load(f)

def save_registry(data):
    with open(REGISTRY_FILE, "w") as f:
        json.dump(data, f, indent=4)

# --- APP SETUP & LOGIN (OMITTED FOR BREVITY BUT LOCKED IN BLUEPRINT) ---
st.set_page_config(page_title=APP_NAME, layout="wide")
registry = load_registry()

if 'auth' not in st.session_state:
    st.session_state.update({'auth': False, 'user': None, 'level': 0})

# [LOGIN GATE LOGIC GOES HERE - UNCHANGED]
if not st.session_state['auth']:
    st.title(f"🔐 {APP_NAME}")
    u = st.text_input("Username").lower().strip()
    p = st.text_input("Password", type="password")
    if st.button("Unlock System"):
        user_data = registry.get(u)
        if user_data and user_data["hash"] == hashlib.sha256(p.encode()).hexdigest():
            st.session_state.update({'auth': True, 'user': u, 'level': user_data['level']})
            st.rerun()
    st.stop()

# --- SIDEBAR NAV ---
st.sidebar.title(APP_NAME)
st.sidebar.progress(st.session_state.step / 7)
st.sidebar.write(f"**Current Phase:** Step {st.session_state.step} of 7")

# --- MAIN INTERFACE ---
tabs = st.tabs(["Resilience Engine", "CV & Job Search", "Admin Console"] if st.session_state['level'] == 3 else ["Resilience Engine", "CV & Job Search"] if st.session_state['level'] == 2 else ["Resilience Engine"])

with tabs[0]:
    # STEP 1: PERSONAL
    if st.session_state.step == 1:
        st.header("👤 Step 1: Personal Blueprint")
        c1, c2 = st.columns(2)
        st.session_state.profile['name'] = c1.text_input("Full Name", value=st.session_state.profile.get('name', ''))
        st.session_state.profile['mobile'] = c2.text_input("Mobile Number", value=st.session_state.profile.get('mobile', ''))
        st.session_state.profile['email'] = c1.text_input("Email Address", value=st.session_state.profile.get('email', ''))
        if st.button("Next ➡️"): st.session_state.step = 2; st.rerun()

    # STEP 2: SUMMARY (WITH GHOSTWRITER LOGIC)
    elif st.session_state.step == 2:
        st.header("📝 Step 2: Personal Summary")
        summary = st.text_area("Write your summary or leave blank for AI Generation", 
                               value=st.session_state.profile.get('summary', ''),
                               help="Basic: I am a worker... \nProf: Strategic leader with...")
        if not summary:
            st.info("🤖 Ghostwriter Active: If left blank, I will build this once History is complete.")
        st.session_state.profile['summary'] = summary
        c1, c2 = st.columns(2)
        if c1.button("⬅️ Back"): st.session_state.step = 1; st.rerun()
        if c2.button("Next ➡️"): st.session_state.step = 3; st.rerun()

    # STEP 3: SKILLS (10 SLOTS)
    elif st.session_state.step == 3:
        st.header("🛠️ Step 3: Key Skills (Top 10)")
        new_skill = st.text_input("Add Skill", help="e.g., Python, Negotiation, Crisis Management")
        if st.button("➕ Add Skill") and len(st.session_state.skills) < 10:
            st.session_state.skills.append(new_skill)
        st.write(f"Current Skills: {', '.join(st.session_state.skills)}")
        c1, c2 = st.columns(2)
        if c1.button("⬅️ Back"): st.session_state.step = 2; st.rerun()
        if c2.button("Next ➡️"): st.session_state.step = 4; st.rerun()

    # STEP 4: EMPLOYMENT (WITH AUTO-SORT)
    elif st.session_state.step == 4:
        st.header("💼 Step 4: Employment History")
        with st.form("job_form"):
            t = st.text_input("Job Title")
            c = st.text_input("Company")
            sd = st.date_input("Start")
            ed = st.date_input("End")
            res = st.text_area("Responsibilities")
            ach = st.text_area("Achievements")
            if st.form_submit_button("Save & Add Role"):
                st.session_state.jobs.append({"title": t, "comp": c, "start": sd, "end": ed, "res": res, "ach": ach})
                # AUTO-SORT LOGIC: Sort by end date descending
                st.session_state.jobs = sorted(st.session_state.jobs, key=lambda x: x['end'], reverse=True)
                st.rerun()
        
        for j in st.session_state.jobs:
            st.write(f"📍 {j['title']} at {j['comp']} ({j['end']})")
            
        c1, c2 = st.columns(2)
        if c1.button("⬅️ Back"): st.session_state.step = 3; st.rerun()
        if c2.button("Next ➡️"): st.session_state.step = 5; st.rerun()

    # STEP 5: EDUCATION
    elif st.session_state.step == 5:
        st.header("🎓 Step 5: Education & Training")
        with st.form("edu_form"):
            sub = st.text_input("Course/Subject")
            body = st.text_input("Examining Body")
            lvl = st.selectbox("Level", ["GCSE", "A-Level", "Degree", "Masters", "PhD", "Professional Cert"])
            grd = st.text_input("Grade")
            yr = st.number_input("Year Achieved", min_value=1970, max_value=2026, value=2020)
            if st.form_submit_button("Add Qualification"):
                st.session_state.edu.append({"sub": sub, "body": body, "lvl": lvl, "grd": grd, "yr": yr})
                st.rerun()
        c1, c2 = st.columns(2)
        if c1.button("⬅️ Back"): st.session_state.step = 4; st.rerun()
        if c2.button("Next ➡️"): st.session_state.step = 6; st.rerun()

# [ADMIN CONSOLE - LOCKED & UNCHANGED]
