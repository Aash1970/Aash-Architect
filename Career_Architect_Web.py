# REPLACE YOUR CURRENT CSS BLOCK WITH THIS:
st.markdown("""
    <style>
    /* 1. Fix the Header */
    [data-testid="stHeader"] { background-color: #0A192F !important; }
    h1 { color: #FFFFFF !important; background-color: #0A192F; padding: 20px; text-align: center; border-bottom: 2px solid #008080; }

    /* 2. Fix the Sidebar (Navy background, WHITE text so you can see the input) */
    [data-testid="stSidebar"] { background-color: #0A192F !important; }
    [data-testid="stSidebar"] .stMarkdown p, [data-testid="stSidebar"] label { color: #FFFFFF !important; }
    
    /* 3. Fix the Input Box (White background, BLACK text inside) */
    div[data-baseweb="input"] { background-color: #FFFFFF !important; border: 1px solid #008080 !important; }
    input { color: #000000 !important; }

    /* 4. Fix the Main Work Area (White background, BLACK text) */
    .stApp { background-color: #FFFFFF; }
    .stMarkdown p, h2, h3 { color: #000000 !important; }

    /* 5. Fix the Button (Teal background, WHITE text, Black border) */
    .stButton>button { 
        background-color: #008080 !important; 
        color: #FFFFFF !important; 
        border: 2px solid #000000 !important;
        font-weight: bold;
    }
    
    /* 6. Fix the Mandatory Footer */
    .footer { position: fixed; left: 0; bottom: 0; width: 100%; background-color: #000000; color: #FFFFFF; text-align: center; padding: 10px; border-top: 2px solid #008080; }
    </style>
    """, unsafe_allow_html=True)
