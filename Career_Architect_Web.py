import streamlit as st
import hashlib
import json
import os

# --- ARCHITECT MASTER CONFIG ---
REGISTRY_FILE = "registry.json"

# YOUR ACTUAL TERMINAL HASHES (NEW ADMIN KEY INCLUDED)
ADMIN_HASH = "440e0a91370aa89083fe9c7cd83db170587dd53fe73aa58fc70a48cc463dfed7"
SUPER_HASH = "1706da5412e68d1acc4a8b10a56a65670477ec6d13f742158b7515183e98b92e"
USER_HASH  = "e41ec8a383f616bc4c5c9b59587616adfa6c6e15f4992048b861abbf67a2935f"

def load_registry():
    if not os.path.exists(REGISTRY_FILE):
        data = {
            "admin_aash": {"hash": ADMIN_HASH, "level": 3, "usage": 999},
            "test_super": {"hash": SUPER_HASH, "level": 2, "usage": 10},
            "test_user": {"hash": USER_HASH, "level": 1, "usage": 5}
        }
        with open(REGISTRY_FILE, "w") as f:
            json.dump(data, f)
        return data
    try:
        with open(REGISTRY_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

st.set_page_config(page_title="Career Architect Master", layout="wide")
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
        
        # Hard-coded Admin Fail-safe
        if u == "admin_aash" and input_hash == ADMIN_HASH:
            st.session_state.update({'auth': True, 'user': u, 'level': 3})
            st.rerun()
        elif u in registry and registry[u]["hash"] == input_hash:
            st.session_state.update({'auth': True, 'user': u, 'level': registry[u]["level"]})
            st.rerun()
        else:
            st.error("Access Denied. Check credentials and capitalization.")
    st.stop()

# --- NAVIGATION ---
st.sidebar.success(f"Verified: {st.session_state['user']} (L{st.session_state['level']})")
if st.sidebar.button("Logout"):
    st.session_state.auth = False
    st.rerun()

# --- TIERED TABS ---
tabs = ["Resilience Engine"]
if st.session_state['level'] >= 2: tabs.append("CV & Job Search")
if st.session_state['level'] >= 3: tabs.append("Admin Console")

active_tabs = st.tabs(tabs)

with active_tabs[0]:
    st.header("🛡️ Resilience Engine (Level 1+)")
    st.info("Core data processing active.")

if "CV & Job Search" in tabs:
    with active_tabs[1]:
        st.header("📄 CV Builder & Job Search (Level 2+)")
        st.write("Management and Employee tools visible here.")

if "Admin Console" in tabs:
    with active_tabs[-1]:
        st.header("🎮 Architect Command Center (Level 3 ONLY)")
        st.write("Manage your tiered users and licensing here.")
        st.subheader("Current User Registry")
        st.json(registry)
