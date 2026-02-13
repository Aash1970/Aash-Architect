import hashlib
import streamlit as st

# --- MASTER CONFIG (Referencing Black Box v4.2.0) ---
VERSION = "4.3.6"
APP_NAME = "The Career Architect"
COPYRIGHT = "© 2026 Aash Hindocha"
MASTER_KEY = "80562e8055655761a6c117e37279318b76e2797e8c0e6f6631b7952e46f66863"

st.set_page_config(page_title=APP_NAME, layout="wide")

# --- CSS ARCHITECTURE ---
st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: white; }
    [data-testid="column"] { display: flex; flex-direction: column; justify-content: flex-end; }
    .cv-card { padding: 15px; border-radius: 8px; background-color: #1E1E1E; border-left: 5px solid #1E3A8A; margin-bottom: 10px; }
    div.stButton > button { margin-top: 28px !important; height: 45px; width: 100%; }
    .footer-text { position: fixed; bottom: 10px; width: 100%; text-align: center; font-size: 12px; color: #555; background-color: #0E1117; padding: 5px 0; z-index: 999; }
    </style>
    """, unsafe_allow_html=True)

# --- SESSION STATE ---
if 'auth' not in st.session_state: st.session_state.auth = False
if 'step' not in st.session_state: st.session_state.step = 1
if 'data' not in st.session_state: 
    st.session_state.data = {'name': '', 'mobile': '', 'email': '', 'summary': '', 'skills': [], 'history': [], 'education': []}

# --- LOGIN GATE ---
if not st.session_state.auth:
    st.title(f"🔐 {APP_NAME}")
    u = st.text_input("Username").lower().strip()
    p = st.text_input("Password", type="password").strip()
    if st.button("Unlock System"):
        if (u == "unlock" and p == "2026"):
            st.session_state.auth = True; st.rerun()
    # MANDATORY FOOTER ON LOGIN
    st.markdown(f"<div class='footer-text'>{COPYRIGHT} | v{VERSION}</div>", unsafe_allow_html=True)
    st.stop()

# --- MAIN APP BODY ---
st.title(f"🏗️ {APP_NAME} | v{VERSION}")

# STEP 1: PERSONAL & SKILLS
if st.session_state.step == 1:
    st.subheader("Step 1: Personal Information")
    c1, c2 = st.columns(2)
    with c1:
        st.session_state.data['name'] = st.text_input("Full Name", st.session_state.data['name'])
        st.session_state.data['mobile'] = st.text_input("Mobile Number", st.session_state.data['mobile'])
        st.session_state.data['email'] = st.text_input("Email Address", st.session_state.data['email'])
    with c2:
        st.session_state.data['summary'] = st.text_area("Professional Summary", st.session_state.data['summary'], height=235)
    
    st.divider()
    k = len(st.session_state.data['skills']) + 1
    st.subheader(f"Step 2: Key Skills / Core Competencies (10 Recommended)")
    col_s1, col_s2 = st.columns([4, 1])
    s_in = col_s1.text_input(f"Enter Skill {k}...", key=f"skill_input_{k}")
    if col_s2.button("➕ Add Skill"):
        if s_in: 
            st.session_state.data['skills'].append(s_in)
            st.rerun()
            
    if st.session_state.data['skills']:
        s_cols = st.columns(3)
        for idx, s in enumerate(st.session_state.data['skills']):
            s_cols[idx % 3].markdown(f"<div class='cv-card'>{idx+1}. {s}</div>", unsafe_allow_html=True)
    
    if st.button("Continue to Employment History ➡️"): st.session_state.step = 2; st.rerun()

# STEP 2: EMPLOYMENT HISTORY
elif st.session_state.step == 2:
    st.header("Step 4: Employment History")
    with st.form("job_form", clear_on_submit=True):
        cA, cB = st.columns(2)
        comp = cA.text_input("Company Name")
        title = cB.text_input("Job Title")
        resp = st.text_area("Responsibilities & Achievements")
        d1, d2 = st.columns(2)
        start = d1.date_input("Start Date")
        end = d2.date_input("End Date")
        if st.form_submit_button("➕ Save Work Experience"):
            new_job = {"comp": comp, "role": title, "resp": resp, "period": f"{start.strftime('%b %Y')} - {end.strftime('%b %Y')}", "sort": start.toordinal()}
            st.session_state.data['history'].append(new_job)
            st.session_state.data['history'] = sorted(st.session_state.data['history'], key=lambda x: x['sort'], reverse=True)
            st.rerun()
    
    for j in st.session_state.data['history']:
        st.markdown(f"<div class='cv-card'><strong>{j['role']}</strong> at {j['comp']} ({j['period']})</div>", unsafe_allow_html=True)

    c_nav1, c_nav2 = st.columns([1, 1])
    if c_nav1.button("⬅️ Back"): st.session_state.step = 1; st.rerun()
    if c_nav2.button("Next to Education ➡️"): st.session_state.step = 3; st.rerun()

# STEP 3: EDUCATION
elif st.session_state.step == 3:
    st.header("Step 5: Education & Credentials")
    with st.form("edu_form", clear_on_submit=True):
        inst = st.text_input("School / College / University Name")
        qual = st.text_input("Qualification Earned")
        yr = st.text_input("Year Completed")
        if st.form_submit_button("➕ Save Education"):
            st.session_state.data['education'].append({"inst": inst, "qual": qual, "yr": yr})
            st.rerun()
            
    for e in st.session_state.data['education']:
        st.markdown(f"<div class='cv-card'>🎓 {e['qual']} - {e['inst']} ({e['yr']})</div>", unsafe_allow_html=True)
        
    if st.button("⬅️ Back"): st.session_state.step = 2; st.rerun()

# --- MANDATORY FOOTER (RENDERED LAST ON ALL AUTHENTICATED SCREENS) ---
st.markdown(f"<div class='footer-text'>{COPYRIGHT} | v{VERSION}</div>", unsafe_allow_html=True)
