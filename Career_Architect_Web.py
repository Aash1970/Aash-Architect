import streamlit as st
from datetime import date

# --- MASTER CONFIG ---
VERSION = "4.6.4"
APP_NAME = "The Career Architect"
COPYRIGHT = "© 2026 Aash Hindocha"

st.set_page_config(page_title=APP_NAME, layout="wide")

# --- CSS ARCHITECTURE: THE BLUE & GREEN SYNERGY ---
st.markdown(f"""
    <style>
    .stApp {{ background-color: #0E1117; color: white; }}
    
    /* BLUE ACCENTS: Overriding default info box styles to our agreed Blue */
    .stAlert {{ background-color: rgba(30, 144, 255, 0.2); border-left: 5px solid #1E90FF; }}
    
    /* TOOLTIP COLOR: Making the '?' icons Blue */
    div[data-testid="stTooltipIcon"] {{ color: #1E90FF !important; }}

    /* BUTTONS: Blue hover state */
    div.stButton > button:hover {{ border-color: #1E90FF; color: #1E90FF; }}

    /* GREEN ACCENTS: Security & Footer only */
    div[data-testid="stTextInput"] button {{ color: #00FF00 !important; }}
    div[data-testid="stTextInput"] div[data-testid="InputInstructions"] {{ display: none !important; }}
    
    .footer-text {{ 
        position: fixed; bottom: 0; left: 0; width: 100%; 
        text-align: center; font-size: 12px; color: #00FF00; 
        padding: 10px 0; background-color: #0E1117; 
        z-index: 999; border-top: 1px solid #333; 
    }}
    
    div.stButton > button {{ margin-top: 28px !important; height: 42px; width: 100%; }}
    </style>
    """, unsafe_allow_html=True)

# --- SESSION STATE ---
if 'auth' not in st.session_state: st.session_state.auth = False
if 'step' not in st.session_state: st.session_state.step = 1
if 'data' not in st.session_state: 
    st.session_state.data = {'name': '', 'mobile': '', 'email': '', 'summary': '', 'skills': [], 'history': [], 'education': [], 'interests': []}

# --- LOGIN GATE ---
if not st.session_state.auth:
    st.title(f"🔐 {APP_NAME} Login")
    u_f = st.text_input("Username").lower().strip()
    p_f = st.text_input("Password", type="password").strip()
    if st.button("Unlock System"):
        if u_f == "unlock" and p_f == "2026":
            st.session_state.auth = True
            st.rerun()
    st.markdown(f"<div class='footer-text'>{COPYRIGHT} | v{VERSION}</div>", unsafe_allow_html=True)
    st.stop()

# --- STEP 1: PROFILE & SKILLS ---
if st.session_state.step == 1:
    st.header("Step 1: Personal Profile")
    cl, cr = st.columns(2)
    with cl:
        st.session_state.data['name'] = st.text_input("Full Name", st.session_state.data['name'], help="Full professional name.")
        st.session_state.data['mobile'] = st.text_input("Mobile Number", st.session_state.data['mobile'], help="UK format: +44...")
        st.session_state.data['email'] = st.text_input("Email Address", st.session_state.data['email'], help="Professional email.")
    with cr:
        st.session_state.data['summary'] = st.text_area("Professional Summary", st.session_state.data['summary'], height=230, help="Career overview.")

    st.divider()
    st.subheader("Step 2: Key Skills (10 Recommended)")
    sc1, sc2 = st.columns([4, 1])
    sk_n = len(st.session_state.data['skills']) + 1
    sk_v = sc1.text_input(f"Enter Skill {sk_n}", key=f"sb_{sk_n}", help="Add top skills.")
    if sc2.button("➕ Add Skill"):
        if sk_v:
            st.session_state.data['skills'].append(sk_v)
            st.rerun()
    if st.session_state.data['skills']:
        rows = st.columns(3)
        for i, s in enumerate(st.session_state.data['skills']):
            rows[i % 3].info(f"{i+1}. {s}") # This will now be Blue via CSS

    if st.button("Continue to Employment History ➡️"): st.session_state.step = 2; st.rerun()

# --- STEP 2: EMPLOYMENT (FLIP LOGIC) ---
elif st.session_state.step == 2:
    st.header("Step 3: Employment History")
    st.info("💡 Reverse Chronological: Entries sort by date automatically.")
    
    with st.form("job_form", clear_on_submit=True):
        f1, f2 = st.columns(2)
        company = f1.text_input("Company Name", help="Employer name.")
        job_title = f2.text_input("Job Title", help="Position held.")
        
        # ASK RESPONSIBILITIES THEN ACHIEVEMENTS
        resp_val = st.text_area("KEY Responsibilities", help="Day-to-day duties.")
        ach_val = st.text_area("KEY Achievements", help="Wins and impact.")
        
        d1, d2, d3 = st.columns([2, 2, 1])
        start_dt = d1.date_input("Start Date", min_value=date(1960, 1, 1), format="DD/MM/YYYY")
        is_now = d3.checkbox("Currently Work Here?")
        end_dt = d2.date_input("End Date", format="DD/MM/YYYY") if not is_now else date.today()
        
        if st.form_submit_button("➕ Add Work Experience"):
            pd = f"{start_dt.strftime('%d/%m/%Y')} - {'Present' if is_now else end_dt.strftime('%d/%m/%Y')}"
            st.session_state.data['history'].append({"comp": company, "role": job_title, "ach": ach_val, "resp": resp_val, "period": pd, "sort": start_dt.toordinal()})
            st.session_state.data['history'] = sorted(st.session_state.data['history'], key=lambda x: x['sort'], reverse=True)
            st.rerun()

    # DISPLAY ACHIEVEMENTS BEFORE RESPONSIBILITIES
    for j in st.session_state.data['history']:
        with st.expander(f"🏢 {j['role']} at {j['comp']} ({j['period']})", expanded=True):
            st.markdown(f"**KEY Achievements:**\n{j['ach']}")
            st.markdown(f"**KEY Responsibilities:**\n{j['resp']}")

    b1, b2 = st.columns(2)
    if b1.button("⬅️ Back"): st.session_state.step = 1; st.rerun()
    if b2.button("Continue to Education ➡️"): st.session_state.step = 3; st.rerun()

# --- STEP 3: EDUCATION & INTERESTS ---
elif st.session_state.step == 3:
    st.header("Step 4: Education & Interests")
    with st.form("edu_form", clear_on_submit=True):
        e1, e2 = st.columns(2)
        inst = e1.text_input("Institution", help="School/College/University.")
        qual = e2.text_input("Qualification", help="e.g. BSc, NVQ.")
        if st.form_submit_button("➕ Add Education"):
            st.session_state.data['education'].append(f"{qual} - {inst}")
            st.rerun()
    for e in st.session_state.data['education']: st.info(e)
    
    st.divider()
    i1, i2 = st.columns([4, 1])
    h_v = i1.text_input("Add Hobby", help="Personal interests.")
    if i2.button("➕ Add Hobby"):
        if h_v:
            st.session_state.data['interests'].append(h_v)
            st.rerun()
    for h in st.session_state.data['interests']: st.warning(h)

    if st.button("⬅️ Back to History"): st.session_state.step = 2; st.rerun()

st.markdown(f"<div class='footer-text'>{COPYRIGHT} | v{VERSION}</div>", unsafe_allow_html=True)
