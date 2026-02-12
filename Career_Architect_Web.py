import hashlib
import json
import os
import re
import streamlit as st
from datetime import datetime, date

# --- MASTER CONFIG (LOCKED) ---
VERSION = "2.9.9"
APP_NAME = "The Career Architect"
COPYRIGHT = "© 2026 Aash Hindocha"
REGISTRY_FILE = "registry.json"
ADMIN_HASH = "440e0a91370aa89083fe9c7cd83db170587dd53fe73aa58fc70a48cc463dfed7"

# --- UI STYLING ---
st.markdown("""
    <style>
    .stApp { max-width: 800px; margin: 0 auto; }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
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

def save_registry(data):
    with open(REGISTRY_FILE, "w") as f: json.dump(data, f, indent=4)

# --- SESSION STATE ---
registry = load_registry()
if 'auth' not in st.session_state: st.session_state.update({'auth': False, 'user': None, 'level': 0})
if 'step' not in st.session_state: st.session_state.step = 1
if 'profile' not in st.session_state: st.session_state.profile = {'name':'', 'mobile':'', 'email':''}

# --- BRANDING ---
st.markdown(f"<h1 style='text-align: center; color: #1E3A8A;'>{APP_NAME}</h1>", unsafe_allow_html=True)

# --- LOGIN GATE (RESTORED & STABILIZED) ---
if not st.session_state['auth']:
    u_input = st.text_input("Username").lower().strip()
    p_input = st.text_input("Password", type="password")
    
    if st.button("Unlock System"):
        user_data = registry.get(u_input)
        if user_data and user_data["hash"] == hashlib.sha256(p_input.encode()).hexdigest():
            st.session_state.update({'auth': True, 'user': u_input, 'level': user_data['level']})
            st.rerun()
        else:
            st.error("Access Denied: Invalid Credentials.")
    st.stop()

# --- STEP 1: PERSONAL INFORMATION ---
if st.session_state.step == 1:
    st.subheader("Step 1: Personal Information")
    name = st.text_input("Full Name", value=st.session_state.profile['name'])
    mobile = st.text_input("Mobile Number", value=st.session_state.profile['mobile'])
    email = st.text_input("Email Address", value=st.session_state.profile['email'])
    
    if st.button("Next ➡️"):
        # Admin Bypass for testing
        if st.session_state['user'] == "admin_aash":
            st.session_state.step = 2
            st.rerun()
        # User Validation
        elif not name or not validate_mobile(mobile) or not validate_email(email):
            st.error("Please ensure Name, valid Mobile, and valid Email are provided.")
        else:
            st.session_state.profile.update({'name': name, 'mobile': mobile, 'email': email})
            st.session_state.step = 2
            st.rerun()

# --- ADMIN OVERRIDE (SIDEBAR ONLY FOR YOU) ---
if st.session_state['level'] == 3:
    with st.sidebar:
        st.subheader("Admin Command Center")
        if st.button("Reset To Step 1"):
            st.session_state.step = 1
            st.rerun()
        if st.button("Logout"):
            st.session_state.update({'auth': False, 'user': None, 'level': 0})
            st.rerun()

# --- COPYRIGHT ---
st.markdown(f"<br><hr><p style='text-align: center; font-size: 12px; color: gray;'>{COPYRIGHT} | v{VERSION}</p>", unsafe_allow_html=True)
