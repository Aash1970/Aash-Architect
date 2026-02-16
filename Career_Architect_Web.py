st.markdown("""
    <style>
    /* 1. HEADER: White font, Navy background */
    [data-testid="stHeader"] { background-color: #0A192F !important; }
    h1 { color: #FFFFFF !important; background-color: #0A192F; padding: 20px; text-align: center; border-bottom: 2px solid #008080; }

    /* 2. SIDEBAR: Navy background, FORCE WHITE TEXT */
    [data-testid="stSidebar"] { background-color: #0A192F !important; }
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p, 
    [data-testid="stSidebar"] label { color: #FFFFFF !important; font-weight: bold; }
    
    /* 3. INPUT BOX: White background, Black text inside so you can see what you type */
    div[data-baseweb="input"] { background-color: #FFFFFF !important; border: 2px solid #008080 !important; }
    input { color: #000000 !important; }

    /* 4. MAIN SCREEN: White background, FORCE BLACK TEXT */
    .stApp { background-color: #FFFFFF !important; }
    .stMarkdown p, h2, h3, .stAlert p { color: #000000 !important; font-weight: 500; }

    /* 5. BUTTONS: Teal background, White text, Black border */
    .stButton>button { 
        background-color: #008080 !important; 
        color: #FFFFFF !important; 
        border: 2px solid #000000 !important;
        border-radius: 5px;
    }
    
    /* 6. FOOTER: Black background, White text */
    .footer { position: fixed; left: 0; bottom: 0; width: 100%; background-color: #000000; color: #FFFFFF; text-align: center; padding: 10px; border-top: 2px solid #008080; }
    </style>
    """, unsafe_allow_html=True)
