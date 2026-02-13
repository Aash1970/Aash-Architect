import streamlit as st

# --- MASTER CONFIG ---
VERSION = "4.4.0"
APP_NAME = "The Career Architect"
COPYRIGHT = "© 2026 Aash Hindocha"

st.set_page_config(page_title=APP_NAME, layout="wide")

# --- CSS ARCHITECTURE: THE SURGICAL STRIKE ---
st.markdown(f"""
    <style>
    .stApp {{ background-color: #0E1117; color: white; }}
    
    /* FIX: Completely remove the "Press Enter" overlap from Password fields */
    div[data-testid="stTextInput"] div[data-testid="InputInstructions"] {{
        display: none !important;
    }}
    
    /* FIX: Ensure the Eye Icon is large and clickable */
    div[data-testid="stTextInput"] button {{
        color: #00FF00 !important;
    }}
    
    /* Vertical Symmetry for 'Add Skill' Button */
    div.stButton > button {{
        margin-top: 28px !important;
        height: 42px;
    }}
    
    /* Static Footer */
    .footer-text {{
        position: fixed;
        bottom: 0;
        left: 0;
        width: 100%;
        text-align: center;
        font-size: 12px;
        color: #888;
        padding: 10px 0;
        background-color: #0E1117;
        z-index: 999;
    }}
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
        if u == "unlock" and p == "2026":
            st.session_state.auth = True
            st.rerun()
    st.markdown(f"<div class='footer-text'>{COPYRIGHT} | v{VERSION}</div>", unsafe_allow_html=True)
    st.stop()

# --- MAIN APP (v4.4.0) ---
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
    
    # TERMINOLOGY SYNC: Key Skills / Core Competencies (10 Recommended)
    k = len(st.session_state.data['skills']) + 1
    st.subheader(f"Step 2: Key Skills / Core Competencies (10 Recommended)")
    col_s1, col_s2 = st.columns([4, 1])
    
    # Auto-clearing input field logic
    s_in = col_s1.text_input(f"Enter Skill {k}...", key=f"skill_box_{k}")
    
    if col_s2.button("➕ Add Skill") or (s_in and s_in != st.session_state.get('last_skill')):
        if s_in:
            st.session_state.data['skills'].append(s_in)
            st.session_state.last_skill = s_in
            st.rerun()
            
    if st.session_state.data['skills']:
        s_cols = st.columns(3)
        for idx, s in enumerate(st.session_state.data['skills']):
            s_cols[idx % 3].info(f"{idx+1}. {s}")
    
    if st.button("Continue to Employment History ➡️"): 
        st.session_state.step = 2; st.rerun()

st.markdown(f"<div class='footer-text'>{COPYRIGHT} | v{VERSION}</div>", unsafe_allow_html=True)
