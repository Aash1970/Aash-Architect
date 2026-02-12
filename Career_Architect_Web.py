import hashlib
import streamlit as st

# --- MASTER CONFIG ---
VERSION = "3.0.7"
APP_NAME = "The Career Architect"
# The absolute hash for 'architect2026'
MASTER_KEY = "80562e8055655761a6c117e37279318b76e2797e8c0e6f6631b7952e46f66863"

st.set_page_config(page_title=APP_NAME, layout="centered")

# --- INDESTRUCTIBLE LOGIN ---
if 'auth' not in st.session_state:
    st.session_state.auth = False

if not st.session_state.auth:
    st.title(APP_NAME)
    # Using a simple form to catch the "Enter" key immediately
    with st.form("login_gate"):
        u = st.text_input("Username").lower().strip()
        p = st.text_input("Password", type="password").strip()
        submit = st.form_submit_button("Unlock System")
        
        if submit:
            # Direct string comparison for admin_aash
            if u == "admin_aash" and hashlib.sha256(p.encode()).hexdigest() == MASTER_KEY:
                st.session_state.auth = True
                st.rerun()
            else:
                st.error(f"Access Denied. Ensure no spaces are in the password.")
    st.stop()

# --- SUCCESS STATE ---
st.success("System Open.")
st.write("If you can see this, the door is finally fixed.")
if st.button("Proceed to Setup"):
    st.write("Logic Restored.")
