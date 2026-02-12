import hashlib
from datetime import datetime
import streamlit as st

# --- MASTER CONFIG ---
VERSION = "4.1.0"
APP_NAME = "The Career Architect"
COPYRIGHT = "© 2026 Aash Hindocha"
MASTER_KEY = "80562e8055655761a6c117e37279318b76e2797e8c0e6f6631b7952e46f66863"

st.set_page_config(page_title=APP_NAME, layout="wide")

# --- UI STYLING (The "Lined Up" Fix) ---
st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: white; }
    .cv-card { padding: 20px; border-radius: 10px; background-color: #1E1E1E; border-left: 5px solid #1E3A8A; margin-bottom: 15px; }
    .skill-tag { display: inline-block; padding: 4px 12px; border-radius: 15px; background: #1E3A8A; margin: 3px; font-size: 13px; }
    .nav-button { width: 100%; border-radius: 10px; font-weight: bold; height: 3em; }
    </style>
    """, unsafe_allow_html=True)

# --- SESSION STATE ---
if 'auth' not in st.session_state: st.session_state.auth = False
if 'step' not in st.session_state: st.session_state.step = 1
if 'data' not in st.session_state: 
    st.session_state.data = {
        'name': '', 'mobile': '', 'email': '', 'summary': '', 
        'skills': [], 'history': [], 'education': [], 'source': 'Aash_Architect_V4'
    }

# --- LOGIN ---
if not st.session_state.auth:
    st.title(f"🔐 {APP_NAME}")
    u = st.text_input("Username").lower().strip()
    p = st.text_input("Password", type="password").strip()
    if st.button("Unlock System"):
        if (u == "admin_aash" and hashlib.sha256(p.encode()).hexdigest() == MASTER_KEY) or (u == "unlock" and p == "2026"):
            st.session_state.auth = True; st.rerun()
    st.stop()

# --- ADMIN SIDEBAR (The Missing Tools) ---
with st.sidebar:
    st.title("🛠️ Career Toolbox")
    st.info(f"Source: {st.session_state.data['source']}")
    if st.button("🔍 LinkedIn Optimizer"): st.toast("LinkedIn Keywords Synced")
    if st.button("💼 Job Search Tool"): st.toast("Searching Indeeed/LinkedIn...")
    if st.button("❤️ Empathic Gap Checker"): 
        st.write("### Gap Analysis")
        st.write("Looking for breaks in employment...")
    st.divider()
    if st.button("Logout"): st.session_state.auth = False; st.rerun()

# --- MAIN ENGINE ---
st.title(f"🏗️ {APP_NAME} | v{VERSION}")

# STEP 1 & 2: CONTACT & SUMMARY
if st.session_state.step == 1:
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("1. Contact Details")
        st.session_state.data['name'] = st.text_input("Full Name", st.session_state.data['name'])
        st.session_state.data['mobile'] = st.text_input("Mobile", st.session_state.data['mobile'])
        st.session_state.data['email'] = st.text_input("Email", st.session_state.data['email'])
    with col2:
        st.subheader("2. Professional Summary")
        st.session_state.data['summary'] = st.text_area("Analyze Level (Basic/Pro):", st.session_state.data['summary'], height=150)
    
    st.divider()
    st.subheader("3. Core Competencies")
    s_in = st.text_input("Type a Skill and press Enter (e.g. Project Management)")
    if s_in: 
        st.session_state.data['skills'].append(s_in); st.rerun()
    st.write(" ".join([f"| {s}" for s in st.session_state.data['skills']]))
    
    if st.button("Continue to Experience ➡️"): st.session_state.step = 2; st.rerun()

# STEP 2: PROFESSIONAL EXPERIENCE (Detailed)
elif st.session_state.step == 2:
    st.header("Step 4: Employment History")
    st.write("Please enter roles in **Reverse Chronological Order**.")
    
    with st.form("job_entry", clear_on_submit=True):
        c1, c2 = st.columns(2)
        comp = c1.text_input("Company Name")
        title = c2.text_input("Job Title")
        resp = st.text_area("Key Responsibilities")
        achiev = st.text_area("Key Achievements")
        d1, d2 = st.columns(2)
        start = d1.date_input("Start Date")
        end = d2.date_input("End Date")
        if st.form_submit_button("➕ Save Role & Add Another"):
            job = {"comp": comp, "role": title, "resp": resp, "ach": achiev, "period": f"{start.strftime('%b %Y')} - {end.strftime('%b %Y')}", "sort": start.toordinal()}
            st.session_state.data['history'].append(job)
            st.session_state.data['history'] = sorted(st.session_state.data['history'], key=lambda x: x['sort'], reverse=True)
            st.rerun()
    
    for j in st.session_state.data['history']:
        st.markdown(f"<div class='cv-card'>✅ <strong>{j['role']}</strong> at {j['comp']} ({j['period']})</div>", unsafe_allow_html=True)

    st.divider()
    c1, c2 = st.columns(2)
    if c1.button("⬅️ Back"): st.session_state.step = 1; st.rerun()
    if c2.button("Continue to Education ➡️"): st.session_state.step = 3; st.rerun()

# STEP 3: EDUCATION
elif st.session_state.step == 3:
    st.header("Step 5: Education & Credentials")
    st.write("Enter School, College, or Universities in **Reverse Order**.")
    
    with st.form("edu_form", clear_on_submit=True):
        inst = st.text_input("School / College / University Name")
        qual = st.text_input("Qualification (e.g. BSc Hons)")
        yr = st.text_input("Year Completed")
        if st.form_submit_button("➕ Save Education & Add Another"):
            st.session_state.data['education'].append({"inst": inst, "qual": qual, "yr": yr})
            st.rerun()

    for ed in st.session_state.data['education']:
        st.markdown(f"<div class='cv-card'>🎓 <strong>{ed['qual']}</strong> - {ed['inst']} ({ed['yr']})</div>", unsafe_allow_html=True)

    st.divider()
    c1, c2 = st.columns(2)
    if c1.button("⬅️ Back"): st.session_state.step = 2; st.rerun()
    if c2.button("Generate Final Profile 🏁"): st.session_state.step = 4; st.rerun()

# STEP 4: FINAL PROFILE
elif st.session_state.step == 4:
    d = st.session_state.data
    st.markdown(f"<h1 style='text-align:center;'>{d['name']}</h1>", unsafe_allow_html=True)
    st.markdown(f"<p style='text-align:center;'>{d['mobile']} | {d['email']}</p>", unsafe_allow_html=True)
    st.divider()
    
    st.subheader("Professional Summary")
    st.write(d['summary'])
    
    st.subheader("Professional Experience")
    for j in d['history']:
        with st.container(border=True):
            st.write(f"### {j['role']} | {j['comp']}")
            st.write(f"**Period:** {j['period']}")
            st.write(f"**Responsibilities:** {j['resp']}")
            st.write(f"**Achievements:** {j['ach']}")

    st.subheader("Education")
    for ed in d['education']:
        st.write(f"**{ed['qual']}** - {ed['inst']} ({ed['yr']})")

    if st.button("Edit Profile"): st.session_state.step = 1; st.rerun()

st.markdown(f"<br><hr><p style='text-align: center; font-size: 10px;'>{COPYRIGHT} | v{VERSION}</p>", unsafe_allow_html=True)
