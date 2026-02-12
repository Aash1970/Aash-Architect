import hashlib
from datetime import datetime
import streamlit as st

# --- MASTER CONFIG ---
VERSION = "3.2.0"
APP_NAME = "The Career Architect"
COPYRIGHT = "© 2026 Aash Hindocha"
MASTER_KEY = "80562e8055655761a6c117e37279318b76e2797e8c0e6f6631b7952e46f66863"

st.set_page_config(page_title=APP_NAME, layout="centered")

# --- UI STYLING ---
st.markdown("""
    <style>
    .stApp { max-width: 800px; margin: 0 auto; }
    .stButton>button { border-radius: 20px; width: 100%; background-color: #1E3A8A; color: white; font-weight: bold; }
    .job-box, .edu-box { padding: 15px; border-radius: 10px; background-color: #1E1E1E; color: white; margin: 10px 0; border-left: 5px solid #1E3A8A; }
    </style>
    """, unsafe_allow_html=True)

# --- SESSION STATE INITIALIZATION ---
if 'auth' not in st.session_state: st.session_state.auth = False
if 'step' not in st.session_state: st.session_state.step = 1
if 'data' not in st.session_state: 
    st.session_state.data = {
        'name': '', 'mobile': '', 'email': '', 
        'summary': '', 'skills': [], 'history': [], 'education': []
    }

# --- LOGIN GATE ---
if not st.session_state.auth:
    st.title(f"🔐 {APP_NAME} Login")
    u = st.text_input("Username").lower().strip()
    p = st.text_input("Password", type="password").strip()
    if st.button("Unlock System"):
        if (u == "admin_aash" and hashlib.sha256(p.encode()).hexdigest() == MASTER_KEY) or (u == "unlock" and p == "2026"):
            st.session_state.auth = True
            st.rerun()
        else: st.error("Access Denied.")
    st.stop()

# --- HEADER ---
st.markdown(f"<h1 style='text-align: center; color: #1E3A8A;'>{APP_NAME}</h1>", unsafe_allow_html=True)

# --- STEP 1: PERSONAL INFO ---
if st.session_state.step == 1:
    with st.container(border=True):
        st.subheader("Step 1: Personal Information")
        st.session_state.data['name'] = st.text_input("Full Name", value=st.session_state.data['name'])
        st.session_state.data['mobile'] = st.text_input("Mobile Number", value=st.session_state.data['mobile'])
        st.session_state.data['email'] = st.text_input("Email Address", value=st.session_state.data['email'])
        if st.button("Next ➡️"):
            st.session_state.step = 2
            st.rerun()

# --- STEP 2: SUMMARY ---
elif st.session_state.step == 2:
    with st.container(border=True):
        st.subheader("Step 2: Personal Summary")
        st.session_state.data['summary'] = st.text_area("Sell yourself:", value=st.session_state.data['summary'], height=200)
        c1, c2 = st.columns(2)
        if c1.button("⬅️ Back"): st.session_state.step = 1; st.rerun()
        if c2.button("Next ➡️"): st.session_state.step = 3; st.rerun()

# --- STEP 3: SKILLS ---
elif st.session_state.step == 3:
    with st.container(border=True):
        st.subheader("Step 3: Key Skills")
        with st.form("skill_form", clear_on_submit=True):
            new_s = st.text_input("Add Skill:")
            if st.form_submit_button("➕ Add"):
                if new_s: st.session_state.data['skills'].append(new_s); st.rerun()
        st.write(f"Skills Added: {', '.join(st.session_state.data['skills'])}")
        c1, c2 = st.columns(2)
        if c1.button("⬅️ Back"): st.session_state.step = 2; st.rerun()
        if c2.button("Next ➡️"): st.session_state.step = 4; st.rerun()

# --- STEP 4: EMPLOYMENT (REVERSE CHRONO) ---
elif st.session_state.step == 4:
    with st.container(border=True):
        st.subheader("Step 4: Employment History")
        st.write("**Please enter your previous employment in Reverse Chronological Order.**")
        
        with st.expander("➕ Add Role", expanded=True):
            with st.form("job_form", clear_on_submit=True):
                comp = st.text_input("Company")
                role = st.text_input("Title")
                start = st.date_input("Start Date", value=datetime(2022,1,1))
                end = st.date_input("End Date")
                if st.form_submit_button("Save Role"):
                    job = {"comp": comp, "role": role, "period": f"{start.strftime('%b %Y')} - {end.strftime('%b %Y')}", "sort": start.toordinal()}
                    st.session_state.data['history'].append(job)
                    st.session_state.data['history'] = sorted(st.session_state.data['history'], key=lambda x: x['sort'], reverse=True)
                    st.rerun()
        
        for j in st.session_state.data['history']:
            st.markdown(f"<div class='job-box'><strong>{j['role']}</strong> | {j['comp']}<br>{j['period']}</div>", unsafe_allow_html=True)
            
        c1, c2 = st.columns(2)
        if c1.button("⬅️ Back"): st.session_state.step = 3; st.rerun()
        if c2.button("Next ➡️"): st.session_state.step = 5; st.rerun()

# --- STEP 5: EDUCATION ---
elif st.session_state.step == 5:
    with st.container(border=True):
        st.subheader("Step 5: Education & Certs")
        with st.expander("➕ Add Education"):
            with st.form("edu_form", clear_on_submit=True):
                inst = st.text_input("Institution")
                qual = st.text_input("Qualification")
                year = st.text_input("Year Completed")
                if st.form_submit_button("Save Education"):
                    st.session_state.data['education'].append({"inst": inst, "qual": qual, "year": year})
                    st.rerun()
        
        for e in st.session_state.data['education']:
            st.markdown(f"<div class='edu-box'><strong>{e['qual']}</strong><br>{e['inst']} ({e['year']})</div>", unsafe_allow_html=True)

        c1, c2 = st.columns(2)
        if c1.button("⬅️ Back"): st.session_state.step = 4; st.rerun()
        if c2.button("Preview Finished CV 🏁"): st.session_state.step = 6; st.rerun()

# --- STEP 6: PREVIEW ---
elif st.session_state.step == 6:
    st.success("Review your Professional Profile")
    st.write(f"### {st.session_state.data['name']}")
    st.write(f"📞 {st.session_state.data['mobile']} | 📧 {st.session_state.data['email']}")
    st.write("---")
    st.write("#### Summary")
    st.write(st.session_state.data['summary'])
    if st.button("⬅️ Start Over"):
        st.session_state.step = 1
        st.rerun()

st.markdown(f"<br><hr><p style='text-align: center; font-size: 10px;'>{COPYRIGHT} | v{VERSION}</p>", unsafe_allow_html=True)
