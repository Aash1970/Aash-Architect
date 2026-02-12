import hashlib
import json
import os
import streamlit as st
from datetime import datetime

# --- ARCHITECT MASTER CONFIG ---
VERSION = "2.9.2"
APP_NAME = "The Career Architect"
COPYRIGHT = "© 2026 Aash Hindocha"
ADMIN_EMAIL = "aash@example.com" # Placeholder: Update to your real email
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
        return {"admin_aash": {"hash": ADMIN_HASH, "level": 3, "usage": 9999, "expiry": "2099-12-31"}}

def save_registry(data):
    with open(REGISTRY_FILE, "w") as f:
        json.dump(data, f, indent=4)

# --- PAGE SETUP ---
st.set_page_config(page_title=APP_NAME, layout="wide")
registry = load_registry()

if 'auth' not in st.session_state:
    st.session_state.update({'auth': False, 'user': None, 'level': 0})

# --- LOGIN GATE (WITH SECURE LEASE LOCK) ---
if not st.session_state['auth']:
    st.title(f"🔐 {APP_NAME}")
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
                st.error("🚨 Access Revoked: Your lease has expired. Please contact Aash Hindocha.")
            else:
                st.session_state.update({'auth': True, 'user': u, 'level': user_data["level"]})
                st.rerun()
        else:
            st.error("Invalid Credentials.")
    st.stop()

# --- SIDEBAR (THE CONTACT & BRANDING HUB) ---
st.sidebar.title(APP_NAME)
st.sidebar.success(f"Verified: {st.session_state['user']} (L{st.session_state['level']})")

st.sidebar.markdown("### Support & Licensing")
mail_subject = f"Use Request: {st.session_state['user']}"
st.sidebar.markdown(f'<a href="mailto:{ADMIN_EMAIL}?subject={mail_subject}" style="text-decoration:none;"><button style="width:100%; border-radius:5px; border:1px solid #ccc; padding:8px; cursor:pointer;">➕ Request More Uses</button></a>', unsafe_allow_html=True)
st.sidebar.markdown(f'<a href="mailto:{ADMIN_EMAIL}?subject=Architect Inquiry" style="text-decoration:none;"><button style="width:100%; border-radius:5px; border:1px solid #ccc; padding:8px; margin-top:10px; cursor:pointer;">📧 Contact Architect</button></a>', unsafe_allow_html=True)

if st.sidebar.button("Logout", use_container_width=True):
    st.session_state.update({'auth': False, 'user': None, 'level': 0})
    st.rerun()
st.sidebar.markdown(f"--- \n <p style='font-size:10px;'>{COPYRIGHT}<br>Build Version: {VERSION}</p>", unsafe_allow_html=True)

# --- MAIN INTERFACE TABS ---
tabs = ["Resilience Engine"]
if st.session_state['level'] >= 2: tabs.append("CV & Job Search")
if st.session_state['level'] >= 3: tabs.append("Admin Console")

active_tabs = st.tabs(tabs)

with active_tabs[0]:
    st.header("🛡️ Resilience Engine")
    st.info("System Ready. This section will house the Core Data Gathering and ROI Tools.")

if "CV & Job Search" in tabs:
    with active_tabs[1]:
        st.header("📄 CV & Job Search")
        st.info("This section will house LinkedIn Optimization and CV Architect tools.")

if "Admin Console" in tabs:
    with active_tabs[-1]:
        st.header("🎮 Architect Command Center")
        
        # 1. FULL USER CREATION FORM
        with st.expander("➕ Create New Licensed User", expanded=True):
            ca, cb = st.columns(2)
            with ca:
                new_u = st.text_input("New Username").strip().lower()
                new_p = st.text_input("New Password", type="password").strip()
            with cb:
                new_l = st.selectbox("Assign Tier Level", [1, 2])
                new_usage = st.number_input("Starting Uses", min_value=1, value=10)
                new_exp = st.date_input("Lease Expiry", value=datetime(2026, 12, 31))
            
            if st.button("Generate License"):
                if new_u and new_p:
                    new_h = hashlib.sha256(new_p.encode()).hexdigest()
                    registry[new_u] = {
                        "hash": new_h, 
                        "level": new_l, 
                        "usage": new_usage, 
                        "expiry": new_exp.strftime("%Y-%m-%d")
                    }
                    save_registry(registry)
                    st.success(f"License created for {new_u}!")
                    st.rerun()

        # 2. FULL USER MANAGEMENT REGISTRY
        st.subheader("📋 Active License Registry")
        for user, details in list(registry.items()):
            if user == "admin_aash": continue
            with st.container(border=True):
                c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
                c1.write(f"**{user}** (Tier {details['level']}) \n Expiry: {details['expiry']}")
                c2.write(f"Uses: {details['usage']}")
                
                # REFILL LOGIC
                add_amt = c3.selectbox("Refill", [5, 10, 25, 50, 100], key=f"sel_{user}")
                if c3.button("Add Uses", key=f"btn_{user}"):
                    registry[user]["usage"] += add_amt
                    save_registry(registry)
                    st.rerun()
                
                # REVOKE LOGIC
                if c4.button("Revoke Access", key=f"del_{user}"):
                    del registry[user]
                    save_registry(registry)
                    st.rerun()
