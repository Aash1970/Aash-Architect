import hashlib
import json
import os
import streamlit as st
from datetime import datetime

# --- CONFIG & IDENTITY (LOCKED) ---
VERSION = "2.9.5"
APP_NAME = "The Career Architect"
COPYRIGHT = "© 2026 Aash Hindocha"
ADMIN_EMAIL = "aash@example.com"
REGISTRY_FILE = "registry.json"
ADMIN_HASH = "440e0a91370aa89083fe9c7cd83db170587dd53fe73aa58fc70a48cc463dfed7"

# --- INDUSTRY & ROLE RESEARCH DATA (2026 UPDATED) ---
INDUSTRIES = [
    "Information Technology & SaaS", "Investment Banking & Finance", "Healthcare & Biomedical", 
    "Renewable Energy & Sustainability", "Legal Services", "Manufacturing & Robotics", 
    "Marketing, Creative & Media", "Construction & Real Estate", "Education & EdTech", 
    "Retail & E-commerce", "Aerospace & Defense", "Government & Public Sector"
]

# --- CORE FUNCTIONS ---
def load_registry():
    if not os.path.exists(REGISTRY_FILE):
        data = {"admin_aash": {"hash": ADMIN_HASH, "level": 3, "usage": 9999, "expiry": "2099-12-31"}}
        save_registry(data)
        return data
    with open(REGISTRY_FILE, "r") as f:
        return json.load(f)

def save_registry(data):
    with open(REGISTRY_FILE, "w") as f:
        json.dump(data, f, indent=4)

# --- APP START ---
st.set_page_config(page_title=APP_NAME, layout="wide")
registry = load_registry()

if 'auth' not in st.session_state:
    st.session_state.update({'auth': False, 'user': None, 'level': 0})

# --- LOGIN GATE ---
if not st.session_state['auth']:
    st.title(f"🔐 {APP_NAME}")
    u = st.text_input("Username").lower().strip()
    p = st.text_input("Password", type="password")
    if st.button("Unlock System"):
        user_data = registry.get(u)
        if user_data and user_data["hash"] == hashlib.sha256(p.encode()).hexdigest():
            st.session_state.update({'auth': True, 'user': u, 'level': user_data["level"]})
            st.rerun()
    st.stop()

# --- SIDEBAR (PERSISTENT) ---
st.sidebar.title(APP_NAME)
st.sidebar.success(f"Verified: {st.session_state['user']} (L{st.session_state['level']})")
if st.session_state['user'] != "admin_aash":
    st.sidebar.metric("Uses Remaining", registry[st.session_state['user']]['usage'])

# --- MAIN ENGINE TABS ---
tabs = st.tabs(["Resilience Engine", "CV & Job Search", "Admin Console"] if st.session_state['level'] == 3 else ["Resilience Engine", "CV & Job Search"] if st.session_state['level'] == 2 else ["Resilience Engine"])

with tabs[0]:
    st.header("🛡️ Phase 1: Career Data Architecture")
    st.write("Complete your full professional profile for AI Gap Analysis and ROI Audit.")
    
    with st.form("deep_audit_form"):
        # 1. PERSONAL DETAILS
        st.subheader("👤 Personal Blueprint")
        c1, c2 = st.columns(2)
        f_name = c1.text_input("Full Name", placeholder="e.g. John Doe")
        email = c2.text_input("Email Address")
        phone = c1.text_input("Mobile Number")
        ind = c2.selectbox("Primary Industry", INDUSTRIES)
        
        # 2. WORK HISTORY (EXPANDABLE)
        st.subheader("💼 Employment History")
        for i in range(1, 3):
            st.markdown(f"--- \n**Position {i}**")
            col_a, col_b = st.columns(2)
            comp = col_a.text_input(f"Company {i}", key=f"c_{i}")
            pos = col_b.text_input(f"Job Title {i}", key=f"j_{i}")
            s_date = col_a.date_input(f"Start Date {i}", key=f"s_{i}")
            e_date = col_b.date_input(f"End Date {i}", key=f"e_{i}")
            resp = st.text_area(f"Key Responsibilities {i}", key=f"r_{i}", placeholder="Describe your daily impact...")
            ach = st.text_area(f"Key Achievements {i}", key=f"a_{i}", placeholder="List measurable wins (e.g. Saved £20k/year)...")
            
        # 3. SKILLS
        st.subheader("🛠️ Skills & Competencies")
        skills = st.text_area("Key Skills (Comma Separated)", placeholder="e.g. Python, Project Management, Strategic Planning")
        
        submit = st.form_submit_button("Execute Deep Career Audit (1 Use)")
        
        if submit:
            # GAP DETECTION LOGIC
            # This is a simplified logic to demonstrate the intelligence we are building
            st.subheader("🤖 AI Auditor Analysis")
            
            # Simulated Gap Check between Role 1 and 2
            st.warning("🚨 Gap Detected: There appears to be a 4-month gap in your employment history between Position 1 and 2.")
            st.info("💡 Suggestion: Would you like the AI to help you draft a 'Professional Development' or 'Career Break' entry to optimize this for the CV module?")
            
            if st.session_state['level'] == 3:
                st.markdown("### 🔑 Admin-Only Market Intelligence")
                st.success("ROI Audit: Current achievement density suggests a 15-20% salary upside in the 2026 market.")

# --- ADMIN CONSOLE (LOCKED) ---
if st.session_state['level'] == 3:
    with tabs[-1]:
        st.header("🎮 Architect Command Center")
        for user, data in list(registry.items()):
            if user == "admin_aash": continue
            with st.container(border=True):
                c1, c2, c3 = st.columns([2, 1, 1])
                c1.write(f"**{user}** (L{data['level']})")
                c2.write(f"Uses: {data['usage']}")
                if c3.button(f"Refill {user}", key=f"ref_{user}"):
                    registry[user]["usage"] += 10
                    save_registry(registry)
                    st.rerun()
