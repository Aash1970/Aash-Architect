import streamlit as st

# --- MASTER CONFIG (Reference: Black Box v4.2.0) ---
VERSION = "4.3.8"
APP_NAME = "The Career Architect"
COPYRIGHT = "© 2026 Aash Hindocha"

st.set_page_config(page_title=APP_NAME, layout="wide")

# --- CSS ARCHITECTURE: FIXING THE OVERLAP & ALIGNMENT ---
st.markdown(f"""
    <style>
    .stApp {{ background-color: #0E1117; color: white; }}
    
    /* FIX 1: Cleaning up the Password Eye Icon overlap */
    div[data-testid="stTextInput"] label + div {{
        overflow: visible !important;
    }}
    
    /* FIX 2: Vertical Symmetry for Step 1 */
    div.stButton > button {{
        margin-top: 28px !important;
        height: 42px;
        width: 100%;
    }}
    
    /* FIX 3: Forced Footer Positioning */
    .footer-text {{
        position: fixed;
        bottom: 0;
        left: 0;
        width: 100%;
        text-align: center;
        font-size: 12px;
        color: #888;
        background-color: #0E1117;
        padding: 15px 0;
        z-index: 99999;
        border-top: 1px solid #333;
    }}
    </style>
    """, unsafe_allow_html=True)

# --- FORCED FOOTER (This renders REGARDLESS of login status) ---
st.markdown(f"<div class='footer-text'>{COPYRIGHT} | v{VERSION}</div>", unsafe_allow_html=True)

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
        if u == "unlock" and p == "2026":
            st.session_state.auth = True
            st.rerun()
    st.stop()

# --- MAIN APP BODY (v4.3.8) ---
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
        # Professional Summary box height tuned for symmetry
        st.session_state.data['summary'] = st.text_area("Professional Summary", st.session_state.data['summary'], height=230)
    
    st.divider()
    
    # FIXED WORDING: Key Skills / Core Competencies (10 Recommended)
    k = len(st.session_state.data['skills']) + 1
    st.subheader(f"Step 2: Key Skills / Core Competencies (10 Recommended)")
    col_s1, col_s2 = st.columns([4, 1])
    
    # Unique key for every input forces the box to clear after clicking "Add"
    s_in = col_s1.text_input(f"Enter Skill {k}...", key=f"skill_box_{k}")
    
    if col_s2.button("➕ Add Skill"):
        if s_in:
            st.session_state.data['skills'].append(s_in)
            st.rerun()
            
    if st.session_state.data['skills']:
        s_cols = st.columns(3)
        for idx, s in enumerate(st.session_state.data['skills']):
            s_cols[idx % 3].markdown(f"<div style='padding:10px; border-left:4px solid #1E3A8A; background:#1E1E1E; margin-bottom:5px;'>{idx+1}. {s}</div>", unsafe_allow_html=True)
    
    if st.button("Continue to Employment History ➡️"): 
        st.session_state.step = 2; st.rerun()

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
        st.write(f"**{j['role']}** at {j['comp']} ({j['period']})")
    
    if st.button("⬅️ Back"): st.session_state.step = 1; st.rerun()
