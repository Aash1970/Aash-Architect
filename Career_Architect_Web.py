import hashlib
import json
import os
import streamlit as st

# --- MASTER CONFIG (LOCKED) ---
VERSION = "3.0.0"
APP_NAME = "The Career Architect"
COPYRIGHT = "© 2026 Aash Hindocha"
REGISTRY_FILE = "registry.json"
ADMIN_HASH = "440e0a91370aa89083fe9c7cd83db170587dd53fe73aa58fc70a48cc463dfed7"

# --- CORE DATA ---
def load_registry():
    if not os.path.exists(REGISTRY_FILE):
        return {"admin_aash": {"hash": ADMIN_HASH, "level": 3, "usage": 9999, "expiry": "2099-12-31"}}
    with open(REGISTRY_FILE, "r") as f: return json.load(f)

registry = load_registry()

# --- SESSION INITIALIZATION ---
if 'auth' not in st.session_state:
    st.session_state.auth = False
if 'user' not in st.session_state:
    st.session_state.user = None
if 'step' not in st.session_state:
    st.session_state.step = 1

# --- BRANDING ---
st.title(APP_NAME)

# --- LOGIN GATE (ZERO-CONTAINER LOGIC) ---
if not st.session_state.auth:
    u = st.text_input("Username").lower().strip()
    p = st.text_input("Password", type="password")
    
    if st.button("Unlock System"):
        user_data = registry.get(u)
        if user_data:
            input_hash = hashlib.sha256(p.encode()).hexdigest()
            if input_hash == user_data["hash"]:
                st.session_state.auth = True
                st.session_state.user = u
                st.session_state.level = user_data["level"]
                st.success("Access Granted! Click again to enter.")
                st.rerun()
            else:
                st.error("Incorrect Password.")
        else:
            st.error("User not found.")
    st.stop()

# --- POST-LOGIN CONTENT ---
st.sidebar.success(f"Logged in as: {st.session_state.user}")

if st.session_state.step == 1:
    st.subheader("Step 1: Personal Information")
    st.text_input("Full Name")
    if st.button("Next"):
        st.session_state.step = 2
        st.rerun()

# --- ADMIN TOOLS (SIDEBAR) ---
if st.session_state.level == 3:
    with st.sidebar:
        if st.button("Logout"):
            st.session_state.auth = False
            st.rerun()

st.write(f"--- \n {COPYRIGHT} | Build {VERSION}")
