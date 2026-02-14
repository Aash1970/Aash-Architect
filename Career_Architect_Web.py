import streamlit as st
import json
import os
from datetime import datetime
from fpdf import FPDF

# --- 1. PAGE INITIALIZATION ---
# Sets the browser tab title and layout to "Wide" for the Admin dashboard.
st.set_page_config(page_title="Career Architect By Aash", layout="wide")

# --- 2. THE BRANDING STYLESHEET ---
# This hard-codes your #0E1117 Black background and Teal accents.
st.markdown("""
    <style>
    .main { background-color: #0E1117; color: white; }
    .stButton>button { background-color: #00d1b2; color: black; border-radius: 5px; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. DATABASE (REGISTRY) FUNCTIONS ---
# This manages your users, their "Uses" balance, and their lease expiry dates.
def load_registry():
    # If the file exists, we read it. If not, we create the Master Admin account.
    if os.path.exists('user_registry.json'):
        with open('user_registry.json', 'r') as f:
            return json.load(f)
    return {"aash": {"password": "admin", "tier": "Admin", "uses": 999, "expiry": "2099-12-31"}}

def save_registry(data):
    # This locks in any changes to 'Uses' or new users instantly.
    with open('user_registry.json', 'w') as f:
        json.dump(data, f, indent=4)

# --- 4. THE PDF GENERATOR (STEALTH BRANDING ENGINE) ---
class CareerArchitectPDF(FPDF):
    def header(self):
        # Adds the proprietary title to the top of every page.
        self.set_font('Arial', 'B', 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, 'Career Architect Secure Portal - Proprietary Content', 0, 1, 'C')

    def footer(self):
        # THE MICRO-FOOTER: Your signature at the bottom (Size 6).
        self.set_y(-15)
        self.set_font('Arial', 'I', 6)
        self.set_text_color(180, 180, 180)
        self.cell(0, 10, 'Optimized by The Career Architect | © 2026 Aash Hindocha', 0, 0, 'C')

    def draw_watermark(self):
        # Applies the "DRAFT" diagonal text to protect your work until 'Finalized'.
        self.set_font('Arial', 'B', 50)
        self.set_text_color(200, 200, 200)
        with self.local_context(fill_opacity=0.1): 
            self.rotate(45, 105, 148)
            self.text(35, 190, "DRAFT - CAREER ARCHITECT")
            self.rotate(0)

# --- 5. THE MAIN APPLICATION LOGIC ---
def main():
    registry = load_registry()
    
    # Session State keeps the user logged in while they click between tabs.
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False

    if not st.session_state.logged_in:
        # THE LOGIN SCREEN
        st.title("Career Architect Secure Portal")
        user = st.text_input("Username")
        pw = st.text_input("Password", type="password")
        
        if st.button("Login"):
            if user in registry and registry[user]['password'] == pw:
                # THE LEASE GATE: Blocks access if today is past the expiry date.
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
        # THE DASHBOARD (LOGGED IN)
        st.sidebar.title(f"User: {st.session_state.user}")
        st.sidebar.write(f"Level: {st.session_state.tier}")
        st.sidebar.write(f"Uses Remaining: {registry[st.session_state.user]['uses']}")
        
        # CONTACT HUB
        if st.sidebar.button("Request More Uses"):
            st.info("Emailing: aash1970@gmail.com")
        
        if st.sidebar.button("Logout"):
            st.session_state.logged_in = False
            st.rerun()

        # ADMIN COMMAND CENTER TAB
        if st.session_state.tier == "Admin":
            st.header("Admin Command Center")
            target_user = st.selectbox("Manage User Uses", list(registry.keys()))
            
            # Quick-Add Grid for Uses
            c1, c2, c3 = st.columns(3)
            if c1.button("+10"): registry[target_user]['uses'] += 10
            if c2.button("+50"): registry[target_user]['uses'] += 50
            if c3.button("+100"): registry[target_user]['uses'] += 100
            
            if st.button("Save Changes"):
                save_registry(registry)
                st.success("Uses Updated.")

        # THE STRATEGIC BUILDER (USER/SUPERVISOR VIEW)
        st.divider()
        st.header("Strategic Resilience Builder")
        gaps = st.multiselect("Life-Gap Matrix", ["Health", "Bereavement", "Redundancy", "Break"])
        
        achieve = st.text_area("Key Achievements (One per line)")
        resp = st.text_area("Key Responsibilities (One per line)")
        
        if st.button("Generate & Download Draft"):
            # Check if user has enough "Uses"
            if registry[st.session_state.user]['uses'] > 0:
                registry[st.session_state.user]['uses'] -= 1
                save_registry(registry)
                
                # Output Logic: Achievement-First
                st.subheader("Your Resilience ROI Preview")
                st.write("**KEY ACHIEVEMENTS**")
                for a in achieve.split('\n'): st.write(f"• {a}")
                
                # PDF Creation with Stealth Branding & Watermark
                pdf = CareerArchitectPDF()
                pdf.add_page()
                pdf.draw_watermark()
                pdf.set_font("Arial", size=12)
                pdf.multi_cell(0, 10, f"Achievements:\n{achieve}\n\nResponsibilities:\n{resp}")
                
                # Save PDF with Metadata
                pdf.set_author("Aash Hindocha")
                pdf_bytes = pdf.output(dest='S').encode('latin-1')
                st.download_button("Download Watermarked DRAFT", data=pdf_bytes, file_name="Draft_CV.pdf")
            else:
                st.error("No Uses remaining.")

if __name__ == "__main__":
    main()
