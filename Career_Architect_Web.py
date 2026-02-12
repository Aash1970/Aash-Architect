import streamlit as st
import hashlib
import json
import os
from datetime import datetime, timedelta

# --- ARCHITECT MASTER CONFIG ---
VERSION = "2.5.0-MASTER"
REGISTRY_FILE = "registry.json"

# These are your "Founding" Hashes
FOUNDING_DATA = {
    "admin": "369a4869c3795b54630a9163e03947477383790e54308553f6057c7c32729792",
    "supervisor": "1706da5412e68d1acc4a8b10a56a65670477ec6d13f742158b7515183e98b92e",
    "user": "e41ec8a383f616bc4c5c9b59587616adfa6c6e15f4992048b861abbf67a2935f"
}

# --- REGISTRY ENGINE ---
def load_registry():
    if not os.path.exists(REGISTRY_FILE):
        # Initialize with Founding Accounts
        initial_data = {
            "admin_aash": {"hash": FOUNDING_DATA["admin"], "level": 3, "usage": 999, "expiry": "2099-12-31"},
            "test_super": {"hash": FOUNDING_DATA["supervisor"], "level": 2, "usage": 10, "expiry": "2026-12-31"},
            "test_user": {"hash": FOUNDING_DATA["user"], "level": 1, "usage": 5, "expiry": "2026-12-31"}
        }
        save_registry(initial_data)
        return initial_data
    with open(REGISTRY_FILE, "r") as f:
        return json.load(f)

def save_registry(data):
    with open(REGISTRY_FILE, "w") as f:
        json.dump(data, f, indent=4)

# --- APP SETUP ---
st.set_page_config(page_title="Career Architect Master Portal", layout="wide")
registry = load_registry()

if 'auth' not in st.session_state:
    st.session_state.update({'auth': False, 'user': None, 'level': 0})

# --- LOGIN GATE ---
if not st.session_state['auth']:
    st.title("🔐 Career Architect: Secure Access")
    user_input = st.text_input("Username")
    pass_input = st.text_input("Password", type="password")
    
    if st.button("Unlock Vessel"):
        h = hashlib.sha256(pass_input.encode()).hexdigest()
        if user_input in registry and registry[user_input]["hash"] == h:
            st.session_state.update({'auth': True, 'user': user_input, 'level': registry[user_input]["level"]})
            st.success(f"Access Granted: Level {st.session_state['level']}")
            st.rerun()
        else:
            st.error("Invalid Credentials.")
    st.stop()

# --- THE VESSEL (POST-LOGIN) ---
st.sidebar.title(f"Level {st.session_state['level']} Access")
st.sidebar.info(f"User: {st.session_state['user']}")

if st.sidebar.button("Logout"):
    st.session_state.update({'auth': False, 'user': None, 'level': 0})
    st.rerun()

# --- TIERED CONTENT LOGIC ---
tabs = ["Resilience Engine"]
if st.session_state['level'] >= 2: tabs.append("CV Builder & Job Search")
if st.session_state['level'] >= 3: tabs.append("Admin Console")

active_tab = st.tabs(tabs)

with active_tab[0]:
    st.header("🛡️ Resilience Engine (Level 1+)")
    st.write("Core data and ROI metrics live here.")

if "CV Builder & Job Search" in tabs:
    with active_tab[1]:
        st.header("📄 CV Builder & 🔍 Job Search (Level 2+)")
        st.write("Level 2 tools for Supervisors and Volunteers.")

if "Admin Console" in tabs:
    with active_tab[-1]:
        st.header("🎮 Architect Command Center (Level 3 ONLY)")
        
        # Admin: Add New User
        with st.expander("Add New Licensed User"):
            new_u = st.text_input("New Username")
            new_p = st.text_input("New Password", type="password")
            new_l = st.selectbox("Tier Level", [1, 2])
            new_usage = st.number_input("Usage Credits", min_value=1, value=5)
            if st.button("Create License"):
                new_h = hashlib.sha256(new_p.encode()).hexdigest()
                registry[new_u] = {"hash": new_h, "level": new_l, "usage": new_usage, "expiry": "2026-12-31"}
                save_registry(registry)
                st.success(f"User {new_u} added to Registry.")

        st.write("### Current User Registry")
        st.table(registry)
