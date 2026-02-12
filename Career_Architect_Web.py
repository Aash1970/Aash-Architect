import hashlib
import json
import os
import streamlit as st
from datetime import datetime

# --- ARCHITECT MASTER CONFIG ---
VERSION = "2.9.3"
APP_NAME = "The Career Architect"
COPYRIGHT = "© 2026 Aash Hindocha"
ADMIN_EMAIL = "aash@example.com" 
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

# --- LOGIN GATE ---
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
                st.error("🚨 Lease Expired. Contact Aash Hindocha.")
            else:
                st.session_state.update({'auth': True, 'user': u, 'level': user_data["level"]})
                st.rerun()
        else:
            st.error("Access Denied.")
    st.stop()

# --- SIDEBAR ---
st.sidebar.title(APP_NAME)
st.sidebar.success(f"User: {st.session_state['user']} (L{st.session_state['level']})")
if st.session_state['user'] != "admin_aash":
    st.sidebar.metric("Uses Remaining", registry[st.session_state['user']]['usage'])

st.sidebar.markdown("### Support")
mail_subject = f"Use Request: {st.session_state['user']}"
st.sidebar.markdown(f'<a href="mailto:{ADMIN_EMAIL}?subject={mail_subject}" style="text-decoration:none;"><button style="width:100%; border-radius:5px; border:1px solid #ccc; padding:8px; cursor:pointer;">➕ Request More Uses</button></a>', unsafe_allow_html=True)

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
    st.header("🛡️ Resilience Engine: ROI Calculator")
    
    # LEVEL 1 TOOL LOGIC
    with st.form("roi_tool"):
        col1, col2 = st.columns(2)
        industry = col1.selectbox("Industry", ["Technology", "Finance", "Healthcare", "Creative", "Manufacturing"])
        current_sal = col2.number_input("Current Annual Salary (£)", min_value=10000, step=1000)
        experience = st.slider("Years of Experience", 0, 40, 5)
        
        submit = st.form_submit_button("Calculate Resilience & ROI (1 Use)")
        
        if submit:
            user = st.session_state['user']
            if user != "admin_aash" and registry[user]['usage'] < 1:
                st.error("Insufficient Uses. Please request more.")
            else:
                # Deduct Use
                if user != "admin_aash":
                    registry[user]['usage'] -= 1
                    save_registry(registry)
                
                # Logic (Mock ROI calculation for testing)
                market_avg = current_sal * 1.15 # 15% upside logic
                st.success("Analysis Complete!")
                st.write(f"### Results for {st.session_state['user']}")
                st.write(f"**Market Value Projection:** £{market_avg:,.2f}")
                st.progress(0.75, text="Resilience Score: 75%")
                st.rerun() # Refresh usage counter in sidebar

if "CV & Job Search" in tabs:
    with active_tabs[1]:
        st.header("📄 CV & Job Search")
        st.info("Level 2 Tools: LinkedIn Blueprint Engine coming next.")

if "Admin Console" in tabs:
    with active_tabs[-1]:
        st.header("🎮 Command Center")
        # All Admin logic from v2.9.2 is kept here perfectly...
        with st.expander("➕ Create New Licensed User", expanded=False):
            ca, cb = st.columns(2)
            nu = ca.text_input("Username").strip().lower()
            np = ca.text_input("Password", type="password").strip()
            nl = cb.selectbox("Level", [1, 2])
            nus = cb.number_input("Uses", min_value=1, value=10)
            nex = cb.date_input("Expiry", value=datetime(2026, 12, 31))
            if st.button("Generate License"):
                if nu and np:
                    nh = hashlib.sha256(np.encode()).hexdigest()
                    registry[nu] = {"hash": nh, "level": nl, "usage": nus, "expiry": nex.strftime("%Y-%m-%d")}
                    save_registry(registry)
                    st.success(f"Done!")
                    st.rerun()
        
        st.subheader("📋 Registry")
        for u_name, d in list(registry.items()):
            if u_name == "admin_aash": continue
            with st.container(border=True):
                c1, c2, c3 = st.columns([2, 1, 1])
                c1.write(f"**{u_name}** (L{d['level']}) | Exp: {d['expiry']}")
                c2.write(f"Uses: {d['usage']}")
                refill = c3.selectbox("Refill", [5, 10, 25, 50], key=f"r_{u_name}")
                if c3.button("Add", key=f"b_{u_name}"):
                    registry[u_name]["usage"] += refill
                    save_registry(registry)
                    st.rerun()
