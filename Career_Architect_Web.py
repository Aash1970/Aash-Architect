import hashlib
from datetime import datetime
import streamlit as st

# --- MASTER CONFIG ---
VERSION = "3.3.0"
APP_NAME = "The Career Architect"
COPYRIGHT = "© 2026 Aash Hindocha"
MASTER_KEY = "80562e8055655761a6c117e37279318b76e2797e8c0e6f6631b7952e46f66863"

st.set_page_config(page_title=APP_NAME, layout="centered")

# --- UI STYLING ---
st.markdown("""
    <style>
    .stApp { max-width: 800px; margin: 0 auto; background-color: #0E1117; }
    .stButton>button { border-radius: 10px; width: 100%; background-color: #1E3A8A; color: white; height: 3em; font-weight: bold; }
    .cv-card { padding: 20px; border-radius: 10px; background-color: #1E1E1E; border-left: 5px solid #1E3A8A; margin-bottom: 15px; }
    .cv-header { text-align: center; border-bottom: 2px solid #1E3A8A; padding-bottom: 20px; margin-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

# --- SESSION STATE ---
if 'auth' not in st.session_state: st.session_state.auth = False
if 'step' not in st.session_state: st.session_state.step = 1
if 'data' not in st.session_state: 
    st.session_state.data = {'name': '', 'mobile': '', 'email': '', 'summary': '', 'skills': [], 'history': [], 'education': []}

# --- LOGIN ---
if not st.session_state.auth:
    st.title(f"🔐 {APP_NAME}")
    u = st.text_input("Username").lower().strip()
    p = st.text_input("Password", type="password").strip()
    if st.button("Unlock System"):
        if (u == "admin_aash" and hashlib.sha256(p.encode()).hexdigest() == MASTER_KEY) or (u == "unlock" and p == "2026"):
            st.session_state.auth = True; st.rerun()
        else: st.error("Access Denied.")
    st.stop()

# --- STEP 1: CONTACT ---
if st.session_state.step == 1:
    st.header("Step 1: Contact Details")
    st.session_state.data['name'] = st.text_input("Full Name", st.session_state.data['name'])
    st.session_state.data['mobile'] = st.text_input("Mobile", st.session_state.data['mobile'])
    st.session_state.data['email'] = st.text_input("Email", st.session_state.data['email'])
    if st.button("Continue ➡️"): st.session_state.step = 2; st.rerun()

# --- STEP 2: SUMMARY ---
elif st.session_state.step == 2:
    st.header("Step 2: Professional Summary")
    st.session_state.data['summary'] = st.text_area("Profile Introduction", st.session_state.data['summary'], height=200)
    c1, c2 = st.columns(2); 
    if c1.button("⬅️ Back"): st.session_state.step = 1; st.rerun()
    if c2.button("Continue ➡️"): st.session_state.step = 3; st.rerun()

# --- STEP 3: SKILLS ---
elif st.session_state.step == 3:
    st.header("Step 3: Core Competencies")
    with st.form("s_form", clear_on_submit=True):
        s_in = st.text_input("Add Skill:")
        if st.form_submit_button("Add Skill ➕"):
            if s_in: st.session_state.data['skills'].append(s_in); st.rerun()
    st.write(f"**Current Skills:** {', '.join(st.session_state.data['skills'])}")
    c1, c2 = st.columns(2);
    if c1.button("⬅️ Back"): st.session_state.step = 2; st.rerun()
    if c2.button("Continue ➡️"): st.session_state.step = 4; st.rerun()

# --- STEP 4: EMPLOYMENT ---
elif st.session_state.step == 4:
    st.header("Step 4: Experience")
    st.info("Enter roles in Reverse Chronological Order.")
    with st.form("j_form", clear_on_submit=True):
        c, r = st.text_input("Company"), st.text_input("Job Title")
        s, e = st.date_input("Start"), st.date_input("End")
        if st.form_submit_button("Save Work Experience 💾"):
            job = {"comp": c, "role": r, "date": f"{s.strftime('%b %Y')} - {e.strftime('%b %Y')}", "sort": s.toordinal()}
            st.session_state.data['history'].append(job)
            st.session_state.data['history'] = sorted(st.session_state.data['history'], key=lambda x: x['sort'], reverse=True)
            st.rerun()
    for j in st.session_state.data['history']:
        st.write(f"✅ **{j['role']}** at {j['comp']} ({j['date']})")
    c1, c2 = st.columns(2);
    if c1.button("⬅️ Back"): st.session_state.step = 3; st.rerun()
    if c2.button("Continue ➡️"): st.session_state.step = 5; st.rerun()

# --- STEP 5: EDUCATION ---
elif st.session_state.step == 5:
    st.header("Step 5: Education")
    with st.form("e_form", clear_on_submit=True):
        inst, qual, yr = st.text_input("Institution"), st.text_input("Qualification"), st.text_input("Year")
        if st.form_submit_button("Save Education 💾"):
            st.session_state.data['education'].append({"inst": inst, "qual": qual, "yr": yr})
            st.rerun()
    for ed in st.session_state.data['education']:
        st.write(f"🎓 **{ed['qual']}** - {ed['inst']} ({ed['yr']})")
    c1, c2 = st.columns(2);
    if c1.button("⬅️ Back"): st.session_state.step = 4; st.rerun()
    if c2.button("Generate Final Profile 🏁"): st.session_state.step = 6; st.rerun()

# --- STEP 6: FINAL PREVIEW ---
elif st.session_state.step == 6:
    d = st.session_state.data
    st.markdown(f"""
        <div class='cv-header'>
            <h1>{d['name']}</h1>
            <p>{d['mobile']} | {d['email']}</p>
        </div>
        <h3>Professional Summary</h3>
        <p>{d['summary']}</p>
        <h3>Core Skills</h3>
        <p>{', '.join(d['skills'])}</p>
        <h3>Professional Experience</h3>
    """, unsafe_allow_html=True)
    
    for j in d['history']:
        st.markdown(f"<div class='cv-card'><strong>{j['role']}</strong><br>{j['comp']} | {j['date']}</div>", unsafe_allow_html=True)
    
    st.markdown("<h3>Education & Credentials</h3>", unsafe_allow_html=True)
    for ed in d['education']:
        st.markdown(f"<div class='cv-card'><strong>{ed['qual']}</strong><br>{ed['inst']} ({ed['yr']})</div>", unsafe_allow_html=True)
    
    if st.button("Start New Architect Session"):
        st.session_state.data = {'name': '', 'mobile': '', 'email': '', 'summary': '', 'skills': [], 'history': [], 'education': []}
        st.session_state.step = 1; st.rerun()

st.markdown(f"<br><hr><p style='text-align: center; font-size: 10px;'>{COPYRIGHT} | v{VERSION}</p>", unsafe_allow_html=True)
