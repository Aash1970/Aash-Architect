import streamlit as st
import hashlib
import json
import os
from datetime import datetime

# --- ARCHITECT MASTER CONFIG ---
VERSION = "2.8.0"
REGISTRY_FILE = "registry.json"

# Your Terminal-Verified Admin Hash (The new one you just created)
ADMIN_HASH = "440e0a91370aa89083fe9c7cd83db170587dd53fe73aa58fc70a48cc463dfed7"

def load_registry():
    if not os.path.exists(REGISTRY_FILE):
        # Create the initial database if it doesn't exist
        data = {"admin_aash": {"hash": ADMIN_HASH, "level": 3, "usage": 9999, "expiry": "2099-12-31"}}
        save_registry(data)
        return data
    try:
        with open(REGISTRY_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_registry(data):
    with open(REGISTRY_FILE, "w") as f:
        json.dump(data, f, indent=4)

# --- PAGE SETUP ---
st.set_page_config(page_title=f"Career Architect {VERSION}", layout="wide")
registry = load_registry()

if 'auth' not in st.session_state:
    st.session_state.update({'auth': False, 'user': None, 'level': 0})

# --- LOGIN GATE ---
if not st.session_state['auth']:
    st.title("🔐 Career Architect: Secure Access")
    u = st.text_input("Username").strip().lower()
    p = st.text_input("Password", type="password").strip()
    
    if st.button("Unlock Vessel"):
        input_hash = hashlib.sha256(p.encode()).hexdigest()
        
        # Check against Admin directly or the Registry file
        if u == "admin_aash" and input_hash == ADMIN_HASH:
            st.session_state.update({'auth': True, 'user': u, 'level': 3})
            st.rerun()
        elif u in registry and registry[u]["hash"] == input_hash:
            st.session_state.update({'auth': True, 'user': u, 'level': registry[u]["level"]})
            st.rerun()
        else:
            st.error("Invalid Credentials. Check spelling and capitalization.")
    st.stop()

# --- SIDEBAR (With Versioning) ---
st.sidebar.title(f"Vessel {VERSION}")
st.sidebar.success(f"Verified: {st.session_state['user']} (L{st.session_state['level']})")
if st.sidebar.button("Logout"):
    st.session_state.update({'auth': False, 'user': None, 'level': 0})
    st.rerun()

# --- THE MAIN INTERFACE ---
tabs = ["Resilience Engine"]
if st.session_state['level'] >= 2: tabs.append("CV & Job Search")
if st.session_state['level'] >= 3: tabs.append("Admin Console")

active_tabs = st.tabs(tabs)

with active_tabs[0]:
    st.header("🛡️ Resilience Engine")
    st.info("Core application functionality for Level 1, 2, and 3.")

if "Admin Console" in tabs:
    with active_tabs[-1]:
        st.header("🎮 Architect Command Center (Level 3 ONLY)")
        
        # 1. CREATE USER FORM
        with st.expander("➕ Create New Licensed User", expanded=True):
            col_a, col_b = st.columns(2)
            with col_a:
                new_u = st.text_input("New Username").strip().lower()
                new_p = st.text_input("New Password", type="password").strip()
            with col_b:
                new_l = st.selectbox("Assign Tier Level", [1, 2])
                new_usage = st.number_input("Starting Usage Credits", min_value=1, value=10)
            
            if st.button("Generate License"):
                if new_u and new_p:
                    new_h = hashlib.sha256(new_p.encode()).hexdigest()
                    registry[new_u] = {"hash": new_h, "level": new_l, "usage": new_usage, "expiry": "2026-12-31"}
                    save_registry(registry)
                    st.success(f"License created for {new_u}!")
                    st.rerun()

        # 2. MANAGEMENT LIST
        st.subheader("📋 Active License Registry")
        for user, details in list(registry.items()):
            if user == "admin_aash": continue
            with st.container(border=True):
                c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
                c1.write(f"**{user}** (Tier {details['level']})")
                c2.write(f"Credits: {details['usage']}")
                if c3.button(f"Add 5 Credits", key=f"add_{user}"):
                    registry[user]["usage"] += 5
                    save_registry(registry)
                    st.rerun()
                if c4.button(f"Revoke", key=f"del_{user}"):
                    del registry[user]
                    save_registry(registry)
                    st.rerun()
