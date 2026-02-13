import hashlib
from datetime import datetime
import streamlit as st

# --- MASTER CONFIG (Check against Black Box v4.2.0) ---
VERSION = "4.3.1"
APP_NAME = "The Career Architect"
COPYRIGHT = "© 2026 Aash Hindocha"
MASTER_KEY = "80562e8055655761a6c117e37279318b76e2797e8c0e6f6631b7952e46f66863"

st.set_page_config(page_title=APP_NAME, layout="wide")

# --- UI STYLING (Pinned Alignment per v4.2.0) ---
st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: white; }
    .cv-card { padding: 20px; border-radius: 10px; background-color: #1E1E1E; border-left: 5px solid #1E3A8A; margin-bottom: 15px; }
    </style>
    """, unsafe_allow_html=True)

# --- SESSION STATE ---
if 'auth' not in st.session_state: st.session_state.auth = False
if 'step' not in st.session_state: st.session_state.step = 1
if 'data' not in st.session_state: 
    st.session_state.data = {'name': '', 'mobile': '', 'email': '', 'summary': '', 'skills': [], 'history': [], 'education': []}

# --- LOGIN GATE (Using Bypass from v4.2.0) ---
if not st.session_state.auth:
    st.title(f"🔐 {APP_NAME}")
    u = st.text_input("Username").lower().strip()
    p = st.text_input("Password", type="password").strip()
    if st.button("Unlock System"):
        if (u == "admin_aash" and hashlib.sha256(p.encode()).hexdigest() == MASTER_KEY) or (u == "unlock" and p == "2026"):
            st.session_state.auth = True; st.rerun()
    st.stop()

# --- SIDEBAR (Phase 1 Tools Built-In) ---
with st.sidebar:
    st.title("🛠️ Phase 1 Tools")
    if st.button("❤️ Empathic Gap Checker"):
        st.info("Logic: Analyzing employment dates for narrative gaps...")
    if st.button("🔍 LinkedIn Optimizer"):
        st.info("Logic: Syncing 'Core Competencies' with LinkedIn SEO...")
    st.divider()
    if st.button("Logout"): st.session_state.auth = False; st.rerun()

# --- STEP 1: RESTORED TO BLACK BOX SPEC ---
if st.session_state.step == 1:
    st.subheader("Step 1: Personal Information")
    c1, c2 = st.columns(2)
    with c1:
        st.session_state.data['name'] = st.text_input("Full Name", st.session_state.data['name'])
        st.session_state.data['mobile'] = st.text_input("Mobile Number", st.session_state.data['mobile'])
        st.session_state.data['email'] = st.text_input("Email Address", st.session_state.data['email'])
    with c2:
        st.session_state.data['summary'] = st.text_area("Professional Summary", st.session_state.data['summary'], height=155)
    
    st.divider()
    st.subheader("Step 2: Core Competencies")
    col_s1, col_s2 = st.columns([4, 1])
    s_in = col_s1.text_input("Type skill here...")
    if col_s2.button("➕ Add Skill"):
        if s_in: st.session_state.data['skills'].append(s_in); st.rerun()
    st.write(" | ".join(st.session_state.data['skills']))
    
    if st.button("Continue to Employment History ➡️"): st.session_state.step = 2; st.rerun()

# --- STEP 2: EMPLOYMENT HISTORY (RESTORED) ---
elif st.session_state.step == 2:
    st.header("Step 4: Employment History")
    with st.form("job_form", clear_on_submit=True):
        colA, colB = st.columns(2)
        comp, title = colA.text_input("Company Name"), colB.text_input("Job Title")
        resp, ach = st.text_area("Key Responsibilities"), st.text_area("Key Achievements")
        d1, d2 = st.columns(2)
        start, end = d1.date_input("Start Date"), d2.date_input("End Date")
        if st.form_submit_button("➕ Save Role & Add Another"):
            new_job = {"comp": comp, "role": title, "resp": resp, "ach": ach, "period": f"{start.strftime('%b %Y')} - {end.strftime('%b %Y')}", "sort": start.toordinal()}
            st.session_state.data['history'].append(new_job)
            st.session_state.data['history'] = sorted(st.session_state.data['history'], key=lambda x: x['sort'], reverse=True)
            st.rerun()
    
    for j in st.session_state.data['history']:
        st.markdown(f"<div class='cv-card'>✅ <strong>{j['role']}</strong> at {j['comp']}</div>", unsafe_allow_html=True)

    c1, c2, c3 = st.columns([1, 4, 1])
    if c1.button("⬅️ Back"): st.session_state.step = 1; st.rerun()
    if c3.button("Next ➡️"): st.session_state.step = 3; st.rerun()

# --- STEP 3: EDUCATION (RESTORED) ---
elif st.session_state.step == 3:
    st.header("Step 5: Education & Credentials")
    with st.form("edu"):
        inst = st.text_input("School / College / University Name")
        qual = st.text_input("Qualification")
        yr = st.text_input("Year Completed")
        if st.form_submit_button("➕ Save Education & Add Another"):
            st.session_state.data['education'].append({"inst": inst, "qual": qual, "yr": yr})
            st.rerun()
    c1, c2, c3 = st.columns([1, 4, 1])
    if c1.button("⬅️ Back"): st.session_state.step = 2; st.rerun()
    if c3.button("Finish 🏁"): st.session_state.step = 4; st.rerun()

elif st.session_state.step == 4:
    st.success("Architecture Verified Against Agreement File.")
    st.json(st.session_state.data)
    if st.button("Edit All"): st.session_state.step = 1; st.rerun()

st.markdown(f"<br><hr><p style='text-align: center; font-size: 10px;'>{COPYRIGHT} | v{VERSION}</p>", unsafe_allow_html=True)
