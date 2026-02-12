import streamlit as st
import hashlib
import json
import os
from datetime import datetime

# --- ARCHITECT MASTER CONFIG ---
VERSION = "2.9.1"
APP_NAME = "The Career Architect"
COPYRIGHT = "© 2026 Aash Hindocha"
ADMIN_EMAIL = "your-email@example.com" # We will update this later
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
st.set_page_config(page_title=f"{APP_NAME}", layout="wide")
registry = load_registry()

if 'auth' not in st.session_state:
    st.session_state.update({'auth': False, 'user': None, 'level': 0})

# --- LOGIN GATE ---
if not st.session_state['auth']:
    st.title(f"🔐 {APP_NAME}")
    st.subheader("Professional Resilience Engine")
    u = st.text_input("Username").strip().lower()
    p = st.text_input("Password", type="password").strip()
    
    if st.button("Unlock System"):
        input_hash = hashlib.sha256(p.encode()).hexdigest()
        user_data = registry.get(u)
        
        if u == "admin_aash" and input_hash == ADMIN_HASH:
            st.session_state.update({'auth': True, 'user': u, 'level': 3})
            st.rerun()
        elif user_data and user_data["hash"] == input_hash:
            expiry_dt = datetime.strptime(user_data["expiry"], "%Y-%m-%d")
            if datetime.now() > expiry_dt:
                st.error("🚨 Lease Expired. Please contact Aash Hindocha.")
            else:
                st.session_state.update({'auth': True, 'user': u, 'level': user_data["level"]})
                st.rerun()
        else:
            st.error("Access Denied.")
    st.stop()

# --- SIDEBAR (THE CONTACT HUB) ---
st.sidebar.title(APP_NAME)
st.sidebar.success(f"Verified: {st.session_state['user']} (L{st.session_state['level']})")

# Smart Contact Buttons
st.sidebar.markdown("### Support & Licensing")
mail_subject = f"Use Request: {st.session_state['user']}"
st.sidebar.markdown(f'<a href="mailto:{ADMIN_EMAIL}?subject={mail_subject}" style="text-decoration:none;"><button style="width:100%; border-radius:5px; border:1px solid #ccc; padding:5px;">➕ Request More Uses</button></a>', unsafe_allow_html=True)

st.sidebar.markdown(f'<a href="mailto:{ADMIN_EMAIL}?subject=Architect Inquiry" style="text-decoration:none; margin-top:10px;"><button style="width:100%; border-radius:5px; border:1px solid #ccc; padding:5px;">📧 Contact Architect</button></a>', unsafe_allow_html=True)

if st.sidebar.button("Logout", use_container_width=True):
    st.session_state.update({'auth': False, 'user': None, 'level': 0})
    st.rerun()

st.sidebar.markdown(f"--- \n <p style='font-size:10px;'>{COPYRIGHT}<br>Build: {VERSION}</p>", unsafe_allow_html=True)

# --- MAIN INTERFACE ---
tabs = ["Resilience Engine"]
if st.session_state['level'] >= 2: tabs.append("CV & Job Search")
if st.session_state['level'] >= 3: tabs.append("Admin Console")

active_tabs = st.tabs(tabs)

with active_tabs[0]:
    st.header("🛡️ Resilience Engine")
    st.info("Core data tools are initializing...")

if "Admin Console" in tabs:
    with active_tabs[-1]:
        st.header("🎮 Command Center")
        # Registry Management code remains the same...
        st.subheader("📋 User Management")
        for user, details in list(registry.items()):
            if user == "admin_aash": continue
            with st.container(border=True):
                c1, c2, c3 = st.columns([2, 2, 1])
                c1.write(f"**{user}** (Tier {details['level']})")
                c2.write(f"Uses: {details['usage']} | Expiry: {details['expiry']}")
                if c3.button(f"Revoke", key=f"del_{user}"):
                    del registry[user]
                    save_registry(registry)
                    st.rerun()
