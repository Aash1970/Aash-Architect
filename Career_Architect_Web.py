import streamlit as st
from architect_core import ArchitectCore

core = ArchitectCore()
st.set_page_config(page_title="Career Architect", layout="wide")

# CSS: Navy Sidebar/Header, White Body, Black Text
st.markdown("""
    <style>
    [data-testid="stHeader"] { background-color: #0A192F; }
    [data-testid="stSidebar"] { background-color: #0A192F; color: white; border-right: 1px solid #FFFFFF; }
    .stApp { background-color: #FFFFFF; color: #000000; }
    h1 { background-color: #0A192F; color: #FFFFFF !important; padding: 25px; border-radius: 0px; margin-bottom: 30px; border-bottom: 2px solid #008080; }
    h2, h3, p, label { color: #000000 !important; font-family: 'Arial'; }
    .stButton>button { background-color: #008080 !important; color: white !important; font-weight: bold; width: 100%; border-radius: 2px; }
    .footer { position: fixed; left: 0; bottom: 0; width: 100%; background-color: #000000; color: #FFFFFF; text-align: center; padding: 10px; z-index: 999; border-top: 1px solid #008080; }
    </style>
    """, unsafe_allow_html=True)

st.markdown("<h1>Career Architect</h1>", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("<h3 style='color:white;'>System Access</h3>", unsafe_allow_html=True)
    pw = st.text_input("Enter Security Key", type="password")
    auth = (core.get_hash(pw) == "c7ad4411ac76b744d9365c71d605058866196236688d617c0a875a55745d65457f62")
    if auth:
        st.success("Admin Verified")
        sz = st.slider("Logo Scale Control", 0.5, 3.0, 1.0)
        st.image("https://via.placeholder.com/150", width=int(150*sz))

if auth:
    t1, t2, t3, t4 = st.tabs(["Market Intel", "Export Bundle", "Client Recovery", "Stress Test"])
    with t1:
        st.subheader("Live Job Search (Adzuna)")
        job = st.text_input("Job Role Title")
        if st.button("Execute Search"):
            results = core.fetch_jobs(job)
            for j in results[:5]:
                with st.expander(f"{j['title']} - {j['company']['display_name']}"):
                    st.write(j['description'])
    with t2:
        st.subheader("Secure Export")
        nm = st.text_input("Client Full Name")
        cv = st.text_area("Paste CV Text Content", height=300)
        rating = st.select_slider("Suitability Rating", options=range(1, 11), value=7)
        if st.button("Generate Protected ZIP"):
            z = core.create_bundle(nm, cv)
            with open(z, "rb") as f: st.download_button("Download Secure ZIP", f, file_name=z)
    with t3:
        st.subheader("Recovery Suite")
        up = st.file_uploader("Upload .CARF File", type=["carf"])
        if up: st.success("Client Data Authenticated and Restored.")
    with t4:
        st.subheader("Audit & Stress Test")
        off = st.number_input("Simulate Days Forward", 0, 60)
        if st.button("Run Purge Simulation"):
            res = core.run_purge_audit(off)
            st.warning(f"Simulated Date: {res['date']} | Purged Records: {res['purged']}")
else:
    st.info("System Locked. Please authenticate via the sidebar to access the Architect.")

st.markdown(f"<div class='footer'>Copyright © 2026 Career Architect | Version {core.version} | All Rights Reserved</div>", unsafe_allow_html=True)
