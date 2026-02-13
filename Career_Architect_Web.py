import streamlit as st
from datetime import date

# --- MASTER CONFIG ---
# Version 4.6.1: The Absolute Restoration Build. 
# This version serves as the "Ground Truth" for all project requirements.
VERSION = "4.6.1"
APP_NAME = "The Career Architect"
COPYRIGHT = "© 2026 Aash Hindocha"

# Set layout to wide for the side-by-side symmetry required in Step 1
st.set_page_config(page_title=APP_NAME, layout="wide")

# --- CSS ARCHITECTURE: PIXEL-PERFECT SYMMETRY ---
st.markdown(f"""
    <style>
    /* 1. Background and Text Colors */
    .stApp {{ background-color: #0E1117; color: white; }}
    
    /* 2. Fix for the 'Press Enter' overlap on Password/Text inputs */
    div[data-testid="stTextInput"] div[data-testid="InputInstructions"] {{ display: none !important; }}
    
    /* 3. Vertical alignment for 'Add' buttons to match input boxes perfectly */
    div.stButton > button {{ margin-top: 28px !important; height: 42px; width: 100%; }}
    
    /* 4. Bright Green styling for the Password Eye Icon */
    div[data-testid="stTextInput"] button {{ color: #00FF00 !important; }}
    
    /* 5. Static, centered footer for branding and versioning */
    .footer-text {{ 
        position: fixed; bottom: 0; left: 0; width: 100%; 
        text-align: center; font-size: 12px; color: #888; 
        padding: 10px 0; background-color: #0E1117; 
        z-index: 999; border-top: 1px solid #333; 
    }}
    </style>
    """, unsafe_allow_html=True)

# --- SESSION STATE: THE BLACK BOX MEMORY ---
# We initialize all data structures here so no progress is ever lost during navigation
if 'auth' not in st.session_state: st.session_state.auth = False
if 'step' not in st.session_state: st.session_state.step = 1
if 'data' not in st.session_state: 
    st.session_state.data = {
        'name': '', 'mobile': '', 'email': '', 'summary': '', 
        'skills': [], 'history': [], 'education': [], 'interests': []
    }

# --- LOGIN GATE: SECURE ACCESS ---
if not st.session_state.auth:
    st.title(f"🔐 {APP_NAME} Access")
    u_input = st.text_input("Username").lower().strip()
    p_input = st.text_input("Password", type="password").strip()
    if st.button("Unlock System"):
        if u_input == "unlock" and p_input == "2026":
            st.session_state.auth = True
            st.rerun()
    # Footer visible even on login screen
    st.markdown(f"<div class='footer-text' style='color:#00FF00;'>{COPYRIGHT} | v{VERSION}</div>", unsafe_allow_html=True)
    st.stop()

# --- STEP 1: PERSONAL PROFILE & SKILLS ---
if st.session_state.step == 1:
    st.header("Step 1: Personal Profile")
    # Columns create the symmetry between contact info and the summary
    col_left, col_right = st.columns(2)
    
    with col_left:
        # Restore "?" help tooltips for all fields
        st.session_state.data['name'] = st.text_input("Full Name", st.session_state.data['name'], help="Your full professional name for the CV header.")
        st.session_state.data['mobile'] = st.text_input("Mobile Number", st.session_state.data['mobile'], help="UK Format: +44 7... (Required for contact section).")
        st.session_state.data['email'] = st.text_input("Email Address", st.session_state.data['email'], help="Professional email (e.g., name@example.com).")
    
    with col_right:
        # Height 230 matches the combined height of the 3 fields on the left
        st.session_state.data['summary'] = st.text_area("Professional Summary", st.session_state.data['summary'], height=230, help="A 3-5 sentence overview of your career and value.")

    st.divider()
    
    # STEP 2: SKILLS (Integrated into Step 1 for workflow flow)
    st.subheader("Step 2: Key Skills / Core Competencies (10 Recommended)")
    s_col1, s_col2 = st.columns([4, 1])
    skill_count = len(st.session_state.data['skills']) + 1
    # Dynamic key ensures the input box clears automatically when a skill is added
    skill_val = s_col1.text_input(f"Enter Skill {skill_count}", key=f"skill_box_{skill_count}", help="Type a skill and click 'Add Skill' or press Enter.")
    
    if s_col2.button("➕ Add Skill"):
        if skill_val:
            st.session_state.data['skills'].append(skill_val)
            st.rerun()
            
    # Display added skills in a clean, 3-column grid
    if st.session_state.data['skills']:
        s_display = st.columns(3)
        for idx, skill in enumerate(st.session_state.data['skills']):
            s_display[idx % 3].info(f"{idx+1}. {skill}")

    if st.button("Continue to Employment History ➡️"):
        st.session_state.step = 2
        st.rerun()

# --- STEP 3: EMPLOYMENT HISTORY ---
elif st.session_state.step == 2:
    st.header("Step 3: Employment History")
    st.info("💡 Reverse Chronological: List your most recent experience. We recommend the last 15 years.")
    
    with st.form("employment_form", clear_on_submit=True):
        f1, f2 = st.columns(2)
        company = f1.text_input("Company Name", help="The organization you worked for.")
        job_title = f2.text_input("Job Title", help="Your official role/position.")
        
        # ACHIEVEMENTS FIRST: Locked-in agreement based on user reasoning
        ach = st.text_area("KEY Achievements", help="Focus on results and impact. These appear first on the CV.")
        resp = st.text_area("KEY Responsibilities", help="Describe your primary duties and scope of work.")
        
        d1, d2, d3 = st.columns([2, 2, 1])
        # Start Date back to 1960 for full career accessibility
        start_d = d1.date_input("Start Date", min_value=date(1960, 1, 1), format="DD/MM/YYYY", help="UK Format: Day/Month/Year.")
        is_current_job = d3.checkbox("Currently Work Here?", help="Check this to show 'Present' instead of an end date.")
        # End Date only appears/matters if not current
        end_d = d2.date_input("End Date", format="DD/MM/YYYY", help="When you left this position.") if not is_current_job else date.today()
        
        if st.form_submit_button("➕ Add Work Experience"):
            # Format the period string for the CV
            period_str = f"{start_d.strftime('%d/%m/%Y')} - {'Present' if is_current_job else end_d.strftime('%d/%m/%Y')}"
            # Store with 'sort' key to maintain reverse chronological order
            st.session_state.data['history'].append({
                "company": company, "role": job_title, "achievements": ach, "responsibilities": resp, "period": period_str, "sort": start_d.toordinal()
            })
            # Re-sort list every time a new job is added
            st.session_state.data['history'] = sorted(st.session_state.data['history'], key=lambda x: x['sort'], reverse=True)
            st.rerun()

    # Display saved history
    for job in st.session_state.data['history']:
        st.success(f"**{job['role']}** at {job['company']} ({job['period']})")

    b_col1, b_col2 = st.columns(2)
    if b_col1.button("⬅️ Back to Personal Info"): st.session_state.step = 1; st.rerun()
    if b_col2.button("Continue to Education ➡️"): st.session_state.step = 3; st.rerun()

# --- STEP 4: EDUCATION & INTERESTS ---
elif st.session_state.step == 3:
    st.header("Step 4: Education & Personal Interests")
    
    # 1. EDUCATION SECTION
    st.subheader("School / College / University")
    with st.form("education_form", clear_on_submit=True):
        e1, e2 = st.columns(2)
        institute = e1.text_input("Institution", help="Name of the school, university, or training provider.")
        qualification = e2.text_input("Qualification", help="e.g., BSc Business, Level 3 NVQ, Prince2.")
        if st.form_submit_button("➕ Add Education"):
            st.session_state.data['education'].append(f"{qualification} - {institute}")
            st.rerun()
    
    for edu in st.session_state.data['education']: st.info(edu)
    
    st.divider()
    
    # 2. INTERESTS SECTION
    st.subheader("Personal Interests & Hobbies")
    i1, i2 = st.columns([4, 1])
    interest_val = i1.text_input("Add Interest", help="Briefly list hobbies or interests (e.g., Mentoring, Photography).")
    if i2.button("➕ Add Interest"):
        if interest_val:
            st.session_state.data['interests'].append(interest_val)
            st.rerun()
            
    for hobby in st.session_state.data['interests']: st.warning(hobby)

    if st.button("⬅️ Back to Employment"): st.session_state.step = 2; st.rerun()

# GLOBAL STATIC FOOTER
st.markdown(f"<div class='footer-text'>{COPYRIGHT} | v{VERSION}</div>", unsafe_allow_html=True)
