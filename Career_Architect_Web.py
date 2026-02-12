import streamlit as st
import hashlib
import json
import os
from datetime import datetime

# --- ARCHITECT MASTER CONFIG ---
VERSION = "2.9.0"
APP_NAME = "Career Architect By Aash"
COPYRIGHT = "© 2026 [NAME PENDING]" # We will pick from the list next!
REGISTRY_FILE = "registry.json"
ADMIN_HASH = "440e0a91370aa89083fe9c7cd83db170587dd53fe73aa58fc70a48cc463dfed7"

def load_registry():
    if not os.path.exists(REGISTRY_FILE):
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
st.set_page_config(page_title=f"{APP_NAME} {VERSION}", layout="wide")
registry = load_registry()

if 'auth' not in st.session_state:
    st.session_state.update({'auth': False, 'user': None, 'level': 0})

# --- LOGIN GATE (WITH LEASE LOCK) ---
if not st.session_state['auth']:
    st.title(f"🔐 {APP_NAME}: Secure Access")
    u = st.text_input("Username").strip().lower()
    p = st.text_input("Password", type="password").strip()
    
    if st.button("Unlock Vessel"):
        input_hash = hashlib.sha256(p.encode()).hexdigest()
        user_data = registry.get(u)
        
        if u == "admin_aash" and input_hash == ADMIN_HASH:
            st.session_state.update({'auth': True, 'user': u, 'level': 3})
            st.rerun()
        elif user_data and user_data["hash"] == input_hash:
            # LEASE EXPIRY LOCK
            expiry_dt = datetime.strptime(user_data["expiry"], "%Y-%m-%d")
            if datetime.now() > expiry_dt:
                st.error("🚨 Access Revoked: Your lease has expired. Please contact Admin.")
            else:
                st.session_state.update({'auth': True, 'user': u, 'level': user_data["level"]})
                st.rerun()
        else:
            st.error("Invalid Credentials.")
    st.stop()

# --- SIDEBAR & BRANDING ---
st.sidebar.title(APP_NAME)
st.sidebar.caption(f"Build Version: {VERSION}")
st.sidebar.success(f"Verified: {st.session_state['user']} (L{st.session_state['level']})")
if st.sidebar.button("Logout"):
    st.session_state.update({'auth': False, 'user': None, 'level': 0})
    st.rerun()
st.sidebar.markdown(f"--- \n {COPYRIGHT}")

# --- MAIN INTERFACE ---
tabs = ["Resilience Engine"]
if st.session_state['level'] >= 2: tabs.append("CV & Job Search")
if st.session_state['level'] >= 3: tabs.append("Admin Console")

active_tabs = st.tabs(tabs)

with active_tabs[0]:
    st.header("🛡️ Resilience Engine")
    st.info("Level 1 content is being calibrated...")

if "Admin Console" in tabs:
    with active_tabs[-1]:
        st.header("🎮 Architect Command Center")
        
        # 1. CREATE USER
        with st.expander("➕ Create New Licensed User", expanded=True):
            c_a, c_b = st.columns(2)
            with c_a:
                new_u = st.text_input("New Username").strip().lower()
                new_p = st.text_input("New Password", type="password").strip()
            with c_b:
                new_l = st.selectbox("Assign Tier Level", [1, 2])
                new_u_count = st.number_input("Starting Uses", min_value=1, value=10)
            
            if st.button("Generate License"):
                if new_u and new_p:
                    new_h = hashlib.sha256(new_p.encode()).hexdigest()
                    registry[new_u] = {"hash": new_h, "level": new_l, "usage": new_u_count, "expiry": "2026-12-31"}
                    save_registry(registry)
                    st.success(f"License created for {new_u}!")
                    st.rerun()

        # 2. MANAGEMENT LIST (UPGRADED)
        st.subheader("📋 Active License Registry")
        for user, details in list(registry.items()):
            if user == "admin_aash": continue
            with st.container(border=True):
                c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
                c1.write(f"**{user}** (Tier {details['level']})")
                c2.write(f"**Uses Remaining:** {details['usage']}")
                
                add_amt = c3.selectbox("Refill Amount", [5, 10, 25, 50, 100], key=f"sel_{user}")
                if c3.button(f"Add Uses", key=f"btn_{user}"):
                    registry[user]["usage"] += add_amt
                    save_registry(registry)
                    st.rerun()
                if c4.button(f"Revoke", key=f"del_{user}"):
                    del registry[user]
                    save_registry(registry)
                    st.rerun()
