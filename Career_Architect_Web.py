import hashlib
import json
import os
import streamlit as st

# --- MASTER CONFIG ---
VERSION = "3.0.2"
APP_NAME = "The Career Architect"
COPYRIGHT = "© 2026 Aash Hindocha"
REGISTRY_FILE = "registry.json"

# --- EMERGENCY KEY RESET ---
# Typing 'architect2026' will now generate the correct hash automatically
TEMP_RESET_PASSWORD = "architect2026"
RESET_HASH = hashlib.sha256(TEMP_RESET_PASSWORD.encode()).hexdigest()

def load_registry_emergency():
    # This FORCES the registry to accept the new password hash
    admin_data = {"admin_aash": {"hash": RESET_HASH, "level": 3, "usage": 9999, "expiry": "2099-12-31"}}
    if not os.path.exists(REGISTRY_FILE):
        with open(REGISTRY_FILE, "w") as f:
            json.dump(admin_data, f)
    return admin_data

# --- APP START ---
st.set_page_config(page_title=APP_NAME)
registry = load_registry_emergency() # Using the forced reset logic

if 'auth' not in st.session_state:
    st.session_state.auth = False

if not st.session_state.auth:
    st.title("🔐 " + APP_NAME)
    st.info("Emergency Reset Mode Active: Use the temporary password.")
    
    u = st.text_input("Username").lower().strip()
    p = st.text_input("Password", type="password")
    
    if st.button("Unlock"):
        if u == "admin_aash":
            # Check against the temporary reset hash
            if hashlib.sha256(p.encode()).hexdigest() == RESET_HASH:
                st.session_state.auth = True
                st.session_state.user = u
                st.session_state.level = 3
                st.rerun()
            else:
                st.error("Invalid Password. Please use the temporary reset password.")
        else:
            st.error("Username not recognized.")
    st.stop()

# --- SUCCESS STATE ---
st.success(f"Welcome back, {st.session_state.user}. Access Restored.")
st.write("We are back in. Shall we restore the Clean UI and move to Step 2?")

st.write(f"--- \n {COPYRIGHT}")
