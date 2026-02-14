import streamlit as st
import json
import os
from datetime import datetime
from fpdf import FPDF

# --- 1. PAGE INITIALIZATION ---
st.set_page_config(page_title="Career Architect By Aash", layout="wide")

# --- 2. THE BRANDING STYLESHEET (WITH EYE-ICON FIX) ---
st.markdown("""
    <style>
    /* Dark Mode Theme */
    .main { background-color: #0E1117; color: white; }
    
    /* THE FIX: Prevents text from overlapping the 'eye' icon in password fields */
    input[type="password"] {
        padding-right: 50px !important;
    }
    
    /* Standardized Buttons */
    .stButton>button { 
        background-color: #00d1b2; 
        color: black; 
        border-radius: 5px; 
        font-weight: bold; 
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. DATABASE (REGISTRY) FUNCTIONS ---
def load_registry():
    # Loads the user list and permissions from our JSON 'locked' file
    if os.path.exists('user_registry.json'):
        with open('user_registry.json', 'r') as f:
            return json.load(f)
    return {"aash": {"password": "admin", "tier": "Admin", "uses": 999, "expiry": "2099-12-31"}}

def save_registry(data):
    # Saves updates to GitHub/Streamlit environment
    with open('user_registry.json', 'w') as f:
        json.dump(data, f, indent=4)

# --- 4. THE PDF GENERATOR ENGINE ---
class CareerArchitectPDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, 'Career Architect Secure Portal - Proprietary Content', 0, 1, 'C')

    def footer(self):
        # Micro-Footer branding
        self.set_y(-15)
        self.set_font('Arial', 'I', 6)
        self.set_text_color(180, 180, 180)
        self.cell(0, 10, 'Optimized by The Career Architect | © 2026 Aash Hindocha', 0, 0, 'C')

    def draw_watermark(self):
        # Stealth Watermark logic
        self.set_font('Arial', 'B', 50)
        self.set_text_color(200, 200, 200)
        with self.local_context(fill_opacity=0.1): 
            self.rotate(45, 105, 148)
            self.text(35, 190, "DRAFT - CAREER ARCHITECT")
            self.rotate(0)

# --- 5. THE MAIN APPLICATION ---
def main():
    registry = load_registry()
    
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False

    if not st.session_state.logged_in:
        # --- LOGIN SCREEN ---
        st.title("Career Architect Secure Portal")
        user = st.text_input("Username")
        pw = st.text_input("Password", type="password")
        
        if st.button("Login"):
            if user in registry and registry[user]['password'] == pw:
                # The Lease Gate check
                expiry = datetime.strptime(registry[user]['expiry'], '%Y-%m-%d')
                if datetime.now() > expiry:
                    st.error("Account Lease Expired. Contact aash1970@gmail.com")
                else:
                    st.session_state.logged_in = True
                    st.session_state.user = user
                    st.session_state.tier = registry[user]['tier']
                    st.rerun()
            else:
                st.error("Access Denied.")

    else:
        # --- LOGGED IN DASHBOARD ---
        st.sidebar.title(f"User: {st.session_state.user}")
        st.sidebar.write(f"Level: {st.session_state.tier}")
        st.sidebar.write(f"Uses Remaining: {registry[st.session_state.user]['uses']}")
        
        if st.sidebar.button("Logout"):
            st.session_state.logged_in = False
            st.rerun()

        # --- ADMIN COMMAND CENTER ---
        if st.session_state.tier == "Admin":
            st.header("Admin Command Center")
            
            admin_tab1, admin_tab2, admin_tab3 = st.tabs(["Create New User", "Manage Existing", "System Security"])
            
            with admin_tab1:
                st.subheader("Add a New Client/Supervisor")
                new_u = st.text_input("New Username")
                new_p = st.text_input("New Password", type="password", key="new_u_pass")
                new_t = st.selectbox("Tier", ["User", "Supervisor"])
                new_e = st.date_input("Lease Expiry", datetime(2026, 12, 31))
                if st.button("Register User"):
                    if new_u and new_p:
                        registry[new_u] = {"password": new_p, "tier": new_t, "uses": 5, "expiry": str(new_e)}
                        save_registry(registry)
                        st.success(f"User {new_u} created!")
            
            with admin_tab2:
                st.subheader("Update Uses or Reset Passwords")
                target = st.selectbox("Select User to Modify", list(registry.keys()))
                
                # Use Management Grid
                c1, c2 = st.columns(2)
                if c1.button("+25 Uses"): 
                    registry[target]['uses'] += 25
                    save_registry(registry)
                    st.rerun()
                if c2.button("+100 Uses"): 
                    registry[target]['uses'] += 100
                    save_registry(registry)
                    st.rerun()
                
                # Password Reset (for forgotten credentials)
                reset_p = st.text_input(f"New Password for {target}", type="password")
                if st.button("Confirm Reset"):
                    if reset_p: 
                        registry[target]['password'] = reset_p
                        save_registry(registry)
                        st.success(f"Password for {target} updated.")

            with admin_tab3:
                st.subheader("Master Admin Security")
                st.write("Current Admin Username: aash")
                new_admin_p = st.text_input("New Admin Password", type="password")
                if st.button("Confirm Password Change"):
                    if new_admin_p:
                        registry['aash']['password'] = new_admin_p
                        save_registry(registry)
                        st.success("Admin password updated successfully.")

        # --- USER WORKSPACE ---
        st.divider()
        st.header("Resilience Strategy Builder")
        gaps = st.multiselect("Life-Gap Matrix", ["Health", "Bereavement", "Redundancy", "Break"])
        achieve = st.text_area("Key Achievements (One per line)")
        resp = st.text_area("Key Responsibilities (One per line)")
        
        if st.button("Generate & Download Draft"):
            if registry[st.session_state.user]['uses'] > 0:
                registry[st.session_state.user]['uses'] -= 1
                save_registry(registry)
                
                # PDF Creation with Stealth Branding & Watermark
                pdf = CareerArchitectPDF()
                pdf.add_page()
                pdf.set_author("Aash Hindocha")
                pdf.draw_watermark()
                pdf.set_font("Arial", size=12)
                pdf.multi_cell(0, 10, f"Achievements:\n{achieve}\n\nResponsibilities:\n{resp}")
                
                pdf_bytes = pdf.output(dest='S').encode('latin-1')
                st.download_button("Download Watermarked DRAFT", data=pdf_bytes, file_name="Draft_CV.pdf")
            else:
                st.error("No Uses remaining.")

if __name__ == "__main__":
    main()
