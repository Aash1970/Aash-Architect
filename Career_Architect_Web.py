import streamlit as st
import hashlib
from datetime import date

# --- MASTER CONFIG ---
VERSION = "4.8.0"
APP_NAME = "The Career Architect"
COPYRIGHT = "© 2026 Aash Hindocha"
# SHA-256 Hash from your Career_Architect_Web.py
ADMIN_H = "f67341885542f741697275817d3d0f04e0e5671a5390c54170366164d1421696"

st.set_page_config(page_title=f"{APP_NAME} Secure Portal", layout="wide")

# --- CSS ARCHITECTURE: THE INTEGRATED DNA ---
st.markdown(f"""
    <style>
    .stApp {{ background-color: #0E1117; color: white; }}
    
    /* BLUE ACCENTS: Tooltips and Info Boxes */
    div[data-testid="stTooltipIcon"] {{ color: #1E90FF !important; }}
    .stAlert {{ background-color: rgba(30, 144, 255, 0.1); border: 1px solid #1E90FF; }}

    /* GREEN ACCENTS: Security & Footer Branding */
    .footer-text {{ 
        position: fixed; bottom: 0; left: 0; width: 100%; 
        text-align: center; font-size: 13px; color: #00FF00; 
        padding: 10px 0; background-color: #0E1117; 
        z-index: 999; border-top: 1px solid #333; 
    }}
    
    /* Eye Icon & Input instruction removal */
    div[data-testid="stTextInput"] button {{ color: #00FF00 !important; }}
    div[data-testid="stTextInput"] div[data-testid="InputInstructions"] {{ display: none !important; }}
    
    /* Global Button Alignment (28px) */
    div.stButton > button {{ margin-top: 28px !important; height: 42px; width: 100%; }}
    </style>
    """, unsafe_allow_html=True)

# --- SESSION STATE INITIALIZATION ---
if 'auth' not in st.session_state: st.session_state.auth = False
if 'page' not in st.session_state: st.session_state.page = "Dashboard"
if 'step' not in st.session_state: st.session_state.step = 1
if 'data' not in st.session_state: 
    st.session_state.data = {
        'name': '', 'mobile': '', 'email': '', 'summary': '', 
        'skills': [], 'history': [], 'education': [], 'interests': []
    }

# --- LOGIN GATE (Using your SHA-256 Key) ---
if not st.session_state.auth:
    st.title(f"🔐 {APP_NAME} Secure Access")
    pw = st.text_input("Enter Access Key", type="password", help="Your master encryption key.")
    if st.button("Unlock Suite"):
        if hashlib.sha256(pw.encode()).hexdigest() == ADMIN_H:
            st.session_state.auth = True
            st.rerun()
        else:
            st.error("Access Denied. Incorrect Key.")
    st.markdown(f"<div class='footer-text'>{COPYRIGHT} | v{VERSION}</div>", unsafe_allow_html=True)
    st.stop()

# --- SIDEBAR NAVIGATION (The Master Menu) ---
with st.sidebar:
    st.title("🏗️ Navigation")
    if st.button("📊 User Dashboard"): st.session_state.page = "Dashboard"; st.rerun()
    if st.button("📝 CV Architect"): st.session_state.page = "CV"; st.rerun()
    if st.button("🧪 Resilience Engine (Aash Sauce)"): st.session_state.page = "Sauce"; st.rerun()
    st.divider()
    if st.button("🚪 Logout"):
        st.session_state.auth = False
        st.rerun()

# --- BRANDING HEADER ---
st.title(f"🏗️ {APP_NAME}")
st.caption(f"Status: Secure Portal Active | Build {VERSION}")

# --- MODULE 1: DASHBOARD ---
if st.session_state.page == "Dashboard":
    st.header("Welcome to the Career Architect")
    st.info("You have active credits for: CV Generation (20) | AI Analysis (50)") # From Aash_Deployer.py
    st.write("This portal is your 101% integrated command center. Use the sidebar to begin.")

# --- MODULE 2: CV ARCHITECT (STEPS 1-4) ---
elif st.session_state.page == "CV":
    if st.session_state.step == 1:
        st.subheader("Step 1: Personal Profile")
        cl, cr = st.columns(2)
        with cl:
            st.session_state.data['name'] = st.text_input("Full Name", st.session_state.data['name'], help="Enter your full name as it should appear at the top of your CV.")
            st.session_state.data['mobile'] = st.text_input("Mobile Number", st.session_state.data['mobile'], help="UK format (+44) is preferred for professional layouts.")
            st.session_state.data['email'] = st.text_input("Email Address", st.session_state.data['email'], help="Use a professional email address (e.g., name@email.com).")
        with cr:
            st.session_state.data['summary'] = st.text_area("Professional Summary", st.session_state.data['summary'], height=230, help="A 3-5 sentence 'elevator pitch' of your career value.")
        
        st.divider()
        st.subheader("Step 2: Key Skills")
        sc1, sc2 = st.columns([4, 1])
        sk_idx = len(st.session_state.data['skills']) + 1
        sk_v = sc1.text_input(f"Enter Skill {sk_idx}", key=f"sk_{sk_idx}", help="Enter a skill and press 'Enter' or click 'Add'.")
        if sc2.button("➕ Add Skill") or (sk_v and sk_v.strip() != ""):
            if sk_v and sk_v.strip() not in st.session_state.data['skills']:
                st.session_state.data['skills'].append(sk_v.strip())
                st.rerun()
        if st.session_state.data['skills']:
            rows = st.columns(3)
            for i, s in enumerate(st.session_state.data['skills']): rows[i % 3].info(f"{i+1}. {s}")
        if st.button("Next: Employment History ➡️"): st.session_state.step = 2; st.rerun()

    elif st.session_state.step == 2:
        st.subheader("Step 3: Employment History")
        with st.form("job_form", clear_on_submit=True):
            f1, f2 = st.columns(2)
            c, t = f1.text_input("Company Name"), f2.text_input("Job Title")
            r = st.text_area("KEY Responsibilities") # ASK FIRST
            a = st.text_area("KEY Achievements")    # ASK SECOND
            d1, d2, d3 = st.columns([2, 2, 1])
            sd = d1.date_input("Start Date", min_value=date(1960, 1, 1))
            is_p = d3.checkbox("Current?")
            ed = d2.date_input("End Date") if not is_p else date.today()
            if st.form_submit_button("➕ Add Job"):
                pd = f"{sd.strftime('%d/%m/%Y')} - {'Present' if is_p else ed.strftime('%d/%m/%Y')}"
                st.session_state.data['history'].append({"comp": c, "role": t, "ach": a, "resp": r, "period": pd, "sort": sd.toordinal()})
                st.session_state.data['history'] = sorted(st.session_state.data['history'], key=lambda x: x['sort'], reverse=True)
                st.rerun()
        for j in st.session_state.data['history']:
            with st.expander(f"🏢 {j['role']} at {j['comp']}"):
                st.markdown(f"**KEY Achievements:**\n{j['ach']}") # DISPLAY FIRST
                st.markdown(f"**KEY Responsibilities:**\n{j['resp']}") # DISPLAY SECOND
        if st.button("⬅️ Back"): st.session_state.step = 1; st.rerun()
        if st.button("Next: Education ➡️"): st.session_state.step = 3; st.rerun()

    elif st.session_state.step == 3:
        st.subheader("Step 4: Education & Interests")
        with st.form("edu"):
            e1, e2 = st.columns(2)
            inst, qual = e1.text_input("Institution"), e2.text_input("Qualification")
            if st.form_submit_button("➕ Add Education"):
                st.session_state.data['education'].append(f"{qual} - {inst}"); st.rerun()
        for ed in st.session_state.data['education']: st.info(ed)
        
        st.divider()
        i1, i2 = st.columns([4, 1])
        h_v = i1.text_input("Add Hobby", key="hb_in", help="Enter a hobby and press 'Enter'.")
        if i2.button("➕ Add Hobby") or (h_v and h_v.strip() != ""):
            if h_v and h_v.strip() not in st.session_state.data['interests']:
                st.session_state.data['interests'].append(h_v.strip()); st.rerun()
        for hb in st.session_state.data['interests']: st.warning(hb)
        
        if st.button("⬅️ Back"): st.session_state.step = 2; st.rerun()
        if st.button("Finish & Review CV ➡️"): st.session_state.step = 4; st.rerun()

# --- MODULE 3: RESILIENCE ENGINE (Aash Sauce Integration) ---
elif st.session_state.page == "Sauce":
    st.header("🧪 Human Resilience ROI Engine")
    st.write("Translating life crisis into professional strategy.")
    
    # Scenarios pulled from your Career_Architect_User.py
    sauce_data = {
        "Bereavement/Estate": "Strategic professional returning to the workforce after a period dedicated to complex estate management and crisis leadership...",
        "Health Recovery": "Resilient specialist returning to work with a renewed focus on personal optimization and healthcare navigation...",
        "Sandwich Care": "Expert in multi-generational logistics and resource allocation, demonstrating extreme multitasking in high-pressure environments..."
    }
    
    selected_scenario = st.selectbox("Select Resilience Scenario:", list(sauce_data.keys()))
    
    if st.button("Generate LinkedIn Sauce"):
        st.subheader("Your Generated LinkedIn 'About' Content:")
        st.info(sauce_data[selected_scenario])
        st.caption("💡 Copy this into your LinkedIn 'About' section to frame your career gap as a project.")

# --- FOOTER ---
st.markdown(f"<div class='footer-text'>{COPYRIGHT} | v{VERSION}</div>", unsafe_allow_html=True)
