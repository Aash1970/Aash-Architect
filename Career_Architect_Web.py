import hashlib
import json
import os
import re
import streamlit as st
from datetime import datetime, date

# --- MASTER CONFIG (LOCKED) ---
VERSION = "2.9.8"
APP_NAME = "The Career Architect"
COPYRIGHT = "© 2026 Aash Hindocha"
REGISTRY_FILE = "registry.json"
ADMIN_HASH = "440e0a91370aa89083fe9c7cd83db170587dd53fe73aa58fc70a48cc463dfed7"

# --- UI STYLING (The "Aesthetic" Fix) ---
st.markdown("""
    <style>
    .reportview-container .main .block-container{ max-width: 800px; padding-top: 2rem; }
    .stButton>button { width: 100%; border-radius: 20px; }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# --- UTILITIES ---
def validate_email(email):
    return re.match(r"[^@]+@[^@]+\.[^@]+", email)

def validate_mobile(mobile):
    # Basic check for 10+ digits
    return len(re.sub(r'\D', '', mobile)) >= 10

# --- SESSION STATE ---
if 'step' not in st.session_state: st.session_state.step = 1
if 'profile' not in st.session_state: st.session_state.profile = {'name':'', 'mobile':'', 'email':''}
if 'auth' not in st.session_state: st.session_state.update({'auth': False, 'user': None, 'level': 0})

# --- PERSISTENCE ---
def load_registry():
    if not os.path.exists(REGISTRY_FILE):
        return {"admin_aash": {"hash": ADMIN_HASH, "level": 3, "usage": 9999, "expiry": "2099-12-31"}}
    with open(REGISTRY_FILE, "r") as f: return json.load(f)

registry = load_registry()

# --- TOP BRANDING ---
st.markdown(f"<h1 style='text-align: center; color: #1E3A8A;'>{APP_NAME}</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; font-style: italic;'>Precision Career Engineering</p>", unsafe_allow_html=True)

# --- LOGIN GATE ---
if not st.session_state['auth']:
    with st.container(border=True):
        u = st.text_input("Username").lower().strip()
        p = st.text_input("Password", type="password")
        if st.button("Unlock System"):
            user_data = registry.get(u)
            if user_data and user_data["hash"] == hashlib.sha256(p.encode()).hexdigest():
                st.session_state.update({'auth': True, 'user': u, 'level': user_data['level']})
                st.rerun()
    st.stop()

# --- STEP 1: PERSONAL INFORMATION ---
if st.session_state.step == 1:
    with st.container(border=True):
        st.subheader("Step 1: Personal Information")
        name = st.text_input("Full Name", value=st.session_state.profile['name'])
        mobile = st.text_input("Mobile Number", value=st.session_state.profile['mobile'], help="Please enter your full contact number.")
        email = st.text_input("Email Address", value=st.session_state.profile['email'])
        
        # Validation Logic
        if st.button("Next ➡️"):
            if not name:
                st.error("Name is required.")
            elif not validate_mobile(mobile):
                st.error("Please enter a valid mobile number.")
            elif not validate_email(email):
                st.error("Please enter a valid email address.")
            else:
                st.session_state.profile.update({'name': name, 'mobile': mobile, 'email': email})
                st.session_state.step = 2
                st.rerun()

# --- BOTTOM COPYRIGHT ---
st.markdown(f"<br><hr><p style='text-align: center; font-size: 12px; color: gray;'>{COPYRIGHT} | Build {VERSION}</p>", unsafe_allow_html=True)

# --- ADMIN CONSOLE (HIDDEN FROM USERS) ---
if st.session_state['level'] == 3:
    with st.sidebar:
        if st.checkbox("Show Admin Tools"):
            st.write("---")
            st.subheader("Command Center")
            # Refill logic would go here
