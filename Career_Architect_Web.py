import hashlib
import json
import os
import streamlit as st

# --- MASTER CONFIG (LOCKED) ---
VERSION = "3.0.1"
APP_NAME = "The Career Architect"
COPYRIGHT = "© 2026 Aash Hindocha"
REGISTRY_FILE = "registry.json"
# This is the SHA-256 hash for your password
ADMIN_HASH = "440e0a91370aa89083fe9c7cd83db170587dd53fe73aa58fc70a48cc463dfed7"

# --- SELF-HEALING REGISTRY ---
def load_registry_safe():
    # If file doesn't exist or is broken, we REBUILD it right now
    default_admin = {"admin_aash": {"hash": ADMIN_HASH, "level": 3, "usage": 9999, "expiry": "2099-12-31"}}
    if not os.path.exists(REGISTRY_FILE):
        with open(REGISTRY_FILE, "w") as f:
            json.dump(default_admin, f)
        return default_admin
    try:
        with open(REGISTRY_FILE, "r") as f:
            data = json.load(f)
            # Ensure admin is ALWAYS in there
            if "admin_aash" not in data:
                data["admin_aash"] = default_admin["admin_aash"]
            return data
    except Exception:
        # If the file is corrupted/unreadable, overwrite it with working data
        with open(REGISTRY_FILE, "w") as f:
            json.dump(default_admin, f)
        return default_admin

# --- APP INITIALIZATION ---
st.set_page_config(page_title=APP_NAME)
registry = load_registry_safe()

if 'auth' not in st.session_state:
    st.session_state.auth = False
if 'user' not in st.session_state:
    st.session_state.user = None

# --- LOGIN GATE ---
if not st.session_state.auth:
    st.title(APP_NAME)
    st.subheader("System Lock")
    u = st.text_input("Username").lower().strip()
    p = st.text_input("Password", type="password")
    
    if st.button("Unlock"):
        user_data = registry.get(u)
        if user_data:
            if hashlib.sha256(p.encode()).hexdigest() == user_data["hash"]:
                st.session_state.auth = True
                st.session_state.user = u
                st.session_state.level = user_data["level"]
                st.rerun()
            else:
                st.error("Invalid Password.")
        else:
            st.error(f"User '{u}' not recognized.")
    st.stop()

# --- SUCCESS STATE ---
st.sidebar.success(f"Verified: {st.session_state.user}")
st.header("Step 1: Personal Information")
st.info("System access restored. We are back on track.")

# --- FOOTER ---
st.write(f"--- \n {COPYRIGHT} | Build {VERSION}")
