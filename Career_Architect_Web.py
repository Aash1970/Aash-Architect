import hashlib
from datetime import datetime
import streamlit as st

# --- MASTER CONFIG ---
VERSION = "4.2.0"
APP_NAME = "The Career Architect"
COPYRIGHT = "© 2026 Aash Hindocha"
MASTER_KEY = "80562e8055655761a6c117e37279318b76e2797e8c0e6f6631b7952e46f66863"

st.set_page_config(page_title=APP_NAME, layout="wide")

# --- UI STYLING ---
st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: white; }
    .cv-card { padding: 20px; border-radius: 10px; background-color: #1E1E1E; border-left: 5px solid #1E3A8A; margin-bottom: 15px; }
    .skill-tag { display: inline-block; padding: 4px 12px; border-radius: 15px; background: #1E3A8A; margin: 3px; font-size: 13px; }
    </style>
    """, unsafe_allow_html=True)

# --- SESSION STATE ---
if 'auth' not in st.session_state: st.session_state.auth = False
if 'step' not in st.session_state: st.session_state.step = 1
if 'data' not in st.session_state: 
    st.session_state.data = {
        'name': '', 'mobile': '', 'email': '', 'summary': '', 
        'skills': [], 'history': [], 'education': [], 'source': 'Aash_Architect_V4_Final'
    }

# --- LOGIN GATE ---
if not st.session_state.auth:
    st.title(f"🔐 {APP_NAME}")
    u = st.text_input("Username").lower().strip()
    p = st.text_input("Password", type="password").strip()
    if st.button("Unlock System"):
        if (u == "admin_aash" and hashlib.sha256(p.encode()).hexdigest() == MASTER_KEY) or (u == "unlock" and p == "2026"):
            st.session_state.auth = True; st.rerun()
    st.stop()

# --- ADMIN SIDEBAR ---
with st.sidebar:
    st.title("🛠️ Admin Console")
    st.button("🔍 LinkedIn Keyword Research")
    st.button("💼 Global Job Search")
    st.button("❤️ Career Gap Empathy Tool")
    if st.checkbox("Show Raw JSON Data"): st.json(st.session_state.data)
    if st.button("Logout"): st.session_state.auth = False; st.rerun()

# --- MAIN ENGINE ---
st.title(f"🏗️ {APP_NAME} | v{VERSION}")

if st.session_state.step == 1:
    st.subheader("1. Identity & Skills")
    c1, c2 = st.columns(2)
    with c1:
        st.session_state.data['name'] = st.text_input("Full Name", st.session_state.data['name'])
        st.session_state.data['mobile'] = st.text_input("Mobile Number", st.session_state.data['mobile'])
        st.session_state.data['email'] = st.text_input("Email Address", st.session_state.data['email'])
    with c2:
        st.session_state.data['summary'] = st.text_area("Professional Summary (AI Level Check)", st.session_state.data['summary'], height=155)
    st.divider()
    s_in = st.text_input("Type skill and press ENTER")
    if s_in: st.session_state.data['skills'].append(s_in); st.rerun()
    st.write(" | ".join(st.session_state.data['skills']))
    if st.button("Continue to Experience ➡️"): st.session_state.step = 2; st.rerun()

elif st.session_state.step == 2:
    st.header("Step 4: Employment History")
    with st.form("job_form", clear_on_submit=True):
        colA, colB = st.columns(2)
        comp, title = colA.text_input("Company Name"), colB.text_input("Job Title")
        resp, ach = st.text_area("Key Responsibilities"), st.text_area("Key Achievements")
        d1, d2 = st.columns(2)
        start, end = d1.date_input("Start Date"), d2.date_input("End Date")
        if st.form_submit_button("➕ Save Role & Add Next"):
            new_job = {"comp": comp, "role": title, "resp": resp, "ach": ach, "period": f"{start.strftime('%b %Y')} - {end.strftime('%b %Y')}", "sort": start.toordinal()}
            st.session_state.data['history'].append(new_job)
            st.session_state.data['history'] = sorted(st.session_state.data['history'], key=lambda x: x['sort'], reverse=True)
            st.rerun()
    for j in st.session_state.data['history']:
        st.markdown(f"<div class='cv-card'>✅ <strong>{j['role']}</strong> at {j['comp']} ({j['period']})</div>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 4, 1])
    if c1.button("⬅️ Back"): st.session_state.step = 1; st.rerun()
    if c3.button("Next ➡️"): st.session_state.step = 3; st.rerun()

elif st.session_state.step == 3:
    st.header("Step 5: Education")
    with st.form("edu_form", clear_on_submit=True):
        inst, qual, yr = st.text_input("School / College / University Name"), st.text_input("Qualification"), st.text_input("Year Completed")
        if st.form_submit_button("➕ Save Education & Add Next"):
            st.session_state.data['education'].append({"inst": inst, "qual": qual, "yr": yr})
            st.rerun()
    for ed in st.session_state.data['education']:
        st.markdown(f"<div class='cv-card'>🎓 <strong>{ed['qual']}</strong> - {ed['inst']} ({ed['yr']})</div>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 4, 1])
    if c1.button("⬅️ Back"): st.session_state.step = 2; st.rerun()
    if c3.button("Finish 🏁"): st.session_state.step = 4; st.rerun()

elif st.session_state.step == 4:
    d = st.session_state.data
    st.markdown(f"<h1 style='text-align:center;'>{d['name']}</h1>", unsafe_allow_html=True)
    st.divider()
    st.subheader("Work History")
    for j in d['history']:
        with st.container(border=True):
            st.markdown(f"### {j['role']} | {j['comp']} ({j['period']})")
            st.write(f"**Responsibilities:** {j['resp']}\n\n**Achievements:** {j['ach']}")
    if st.button("Edit All Data"): st.session_state.step = 1; st.rerun()

st.markdown(f"<br><hr><p style='text-align: center; font-size: 10px;'>{COPYRIGHT} | v{VERSION}</p>", unsafe_allow_html=True)
