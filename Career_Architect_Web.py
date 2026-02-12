import hashlib
import json
import os
import re
import streamlit as st
from datetime import datetime, date

# --- MASTER CONFIG (LOCKED) ---
VERSION = "3.0.3"
APP_NAME = "The Career Architect"
COPYRIGHT = "© 2026 Aash Hindocha"
REGISTRY_FILE = "registry.json"
# Confirmed hash for 'architect2026'
ADMIN_HASH = "80562e8055655761a6c117e37279318b76e2797e8c0e6f6631b7952e46f66863"

# --- UI STYLING ---
st.markdown("""
    <style>
    .stApp { max-width: 800px; margin: 0 auto; }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stButton>button { border-radius: 20px; height: 3em; background-color: #1E3A8A; color: white; }
    </style>
    """, unsafe_allow_html=True)

# --- UTILITIES ---
def validate_email(email):
    return re.match(r"[^@]+@[^@]+\.[^@]+", email)

def validate_mobile(mobile):
    return len(re.sub(r'\D', '', mobile)) >= 10

def load_registry():
    if not os.path.exists(REGISTRY_FILE):
        return {"admin_aash": {"hash": ADMIN_HASH, "level": 3, "usage": 9999, "expiry": "2099-12-31"}}
    with open(REGISTRY_FILE, "r") as f: return json.load(f)

# --- SESSION STATE ---
registry = load_registry()
if 'auth' not in st.session_state: st.session_state.update({'auth': False, 'user': None, 'level': 0})
if 'step' not in st.session_state: st.session_state.step = 1
if 'data' not in st.session_state: 
    st.session_state.data = {'name': '', 'mobile': '', 'email': '', 'summary': '', 'skills': []}

# --- BRANDING ---
st.markdown(f"<h1 style='text-align: center; color: #1E3A8A;'>{APP_NAME}</h1>", unsafe_allow_html=True)

# --- LOGIN GATE ---
if not st.session_state.auth:
    with st.container(border=True):
        u = st.text_input("Username").lower().strip()
        p = st.text_input("Password", type="password")
        if st.button("Unlock System"):
            user_data = registry.get(u)
            if user_data and hashlib.sha256(p.encode()).hexdigest() == user_data['hash']:
                st.session_state.update({'auth': True, 'user': u, 'level': user_data['level']})
                st.rerun()
            else:
                st.error("Access Denied.")
    st.stop()

# --- STEP 1: PERSONAL INFORMATION ---
if st.session_state.step == 1:
    with st.container(border=True):
        st.subheader("Step 1: Personal Information")
        name = st.text_input("Full Name", value=st.session_state.data['name'])
        mobile = st.text_input("Mobile Number", value=st.session_state.data['mobile'])
        email = st.text_input("Email Address", value=st.session_state.data['email'])
        
        if st.button("Next ➡️"):
            if st.session_state.user == "admin_aash" or (name and validate_mobile(mobile) and validate_email(email)):
                st.session_state.data.update({'name': name, 'mobile': mobile, 'email': email})
                st.session_state.step = 2
                st.rerun()
            else:
                st.error("Please provide valid Name, Mobile, and Email.")

# --- STEP 2: PERSONAL SUMMARY ---
elif st.session_state.step == 2:
    with st.container(border=True):
        st.subheader("Step 2: Personal Summary")
        help_txt = "**Examples:**\n- *Basic:* Motivated professional...\n- *Intermediate:* Proven track record in...\n- *Prof:* Strategic architect of corporate growth..."
        summary = st.text_area("Sell yourself (or leave blank for AI Ghostwriting)", 
                               value=st.session_state.data['summary'], help=help_txt, height=200)
        
        if not summary:
            st.info("🤖 Ghostwriter Mode: I'll draft this using your job history later.")
        
        c1, c2 = st.columns(2)
        if c1.button("⬅️ Back"): st.session_state.step = 1; st.rerun()
        if c2.button("Next ➡️"):
            st.session_state.data['summary'] = summary
            st.session_state.step = 3
            st.rerun()

# --- STEP 3: KEY SKILLS ---
elif st.session_state.step == 3:
    with st.container(border=True):
        st.subheader("Step 3: Key Skills (Max 10)")
        new_skill = st.text_input("Enter a skill (e.g. Project Management)", help="Enter your top competencies.")
        if st.button("➕ Add Skill") and len(st.session_state.data['skills']) < 10 and new_skill:
            st.session_state.data['skills'].append(new_skill)
            st.rerun()
        
        st.write("---")
        for i, s in enumerate(st.session_state.data['skills']):
            st.write(f"{i+1}. {s}")
            
        c1, c2 = st.columns(2)
        if c1.button("⬅️ Back"): st.session_state.step = 2; st.rerun()
        if c2.button("Next ➡️"): st.session_state.step = 4; st.rerun()

# --- ADMIN OVERRIDE ---
if st.session_state.level == 3:
    with st.sidebar:
        st.subheader("Admin Console")
        if st.button("Logout"):
            st.session_state.auth = False
            st.rerun()

# --- FOOTER ---
st.markdown(f"<br><hr><p style='text-align: center; font-size: 10px;'>{COPYRIGHT}</p>", unsafe_allow_html=True)
