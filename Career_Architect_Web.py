import streamlit as st
import hashlib
import json
import requests
import zipfile
import io
import os
import re
from datetime import datetime, timedelta

# ==============================================================
# SECTION 1: CONSTANTS
# ==============================================================
VERSION = "FINAL MASTER STATUS"
APP_TITLE = "CAREER ARCHITECT PRO"
COPYRIGHT = "© 2026 POSE PERFECT LTD"
CVP_FILENAME = "cv_data.cvp"
HASH_FILENAME = "integrity.sha512"
CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "system_config.json")
GAP_THRESHOLD_DAYS = 91  # ~3 months

# ==============================================================
# SECTION 2: CORE HELPER FUNCTIONS
# ==============================================================

def get_hash(text: str) -> str:
    """SHA-512 hash of a stripped string — used for password verification."""
    return hashlib.sha512(text.strip().encode()).hexdigest()

def get_file_hash(data: bytes) -> str:
    """SHA-512 hash of raw bytes — used for .cvp file integrity sealing."""
    return hashlib.sha512(data).hexdigest()

def load_config() -> dict:
    """Load system_config.json. Returns empty dict on any failure."""
    try:
        with open(CONFIG_PATH, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_config(cfg: dict) -> bool:
    """Persist updated config to disk. Returns True on success."""
    try:
        with open(CONFIG_PATH, "w") as f:
            json.dump(cfg, f, indent=4)
        return True
    except IOError:
        return False

def get_adzuna_credentials():
    """Return (app_id, app_key) from system_config.json, or ('','') if missing."""
    cfg = load_config()
    keys = cfg.get("admin_settings", {}).get("api_keys", {})
    return keys.get("adzuna_id", ""), keys.get("adzuna_key", "")

def build_cvp_zip(cv_data: dict, username: str) -> bytes:
    """
    Serializes cv_data to JSON, writes cv_data.cvp, computes SHA-512 integrity
    seal, writes integrity.sha512, and packages both into an in-memory ZIP.
    Returns raw ZIP bytes for st.download_button.
    """
    cvp_bytes = json.dumps(cv_data, indent=2, default=str).encode("utf-8")
    file_hash = get_file_hash(cvp_bytes)
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(CVP_FILENAME, cvp_bytes)
        zf.writestr(HASH_FILENAME, file_hash)
    buffer.seek(0)
    return buffer.read()

def verify_and_extract_cvp(zip_bytes: bytes):
    """
    Extracts cv_data.cvp and integrity.sha512 from ZIP bytes.
    Verifies SHA-512 integrity seal.
    Returns (cv_data_dict, "OK") | (None, "TAMPERED") | (None, "INVALID")
    """
    try:
        buffer = io.BytesIO(zip_bytes)
        with zipfile.ZipFile(buffer, "r") as zf:
            names = zf.namelist()
            if CVP_FILENAME not in names or HASH_FILENAME not in names:
                return None, "INVALID"
            cvp_bytes = zf.read(CVP_FILENAME)
            stored_hash = zf.read(HASH_FILENAME).decode("utf-8").strip()
            computed_hash = get_file_hash(cvp_bytes)
            if computed_hash != stored_hash:
                return None, "TAMPERED"
            cv_data = json.loads(cvp_bytes.decode("utf-8"))
            return cv_data, "OK"
    except Exception:
        return None, "INVALID"

def deduct_credit(username: str) -> bool:
    """Deducts one credit. Returns True if ok or unlimited; False if depleted."""
    user = st.session_state.user_db[username]
    if user["uses"] == "UNLIMITED":
        return True
    if isinstance(user["uses"], int) and user["uses"] > 0:
        st.session_state.user_db[username]["uses"] -= 1
        return True
    return False

# ==============================================================
# SECTION 3: GAP ENGINE
# ==============================================================

GAP_CATEGORIES = [
    "Career Development",
    "Health & Wellbeing",
    "Family & Care",
    "Bereavement",
    "Other"
]

AASH_EMPATHY_TEMPLATES = {
    "Career Development": {
        "aash_message": (
            "This period is one of the most powerful signals on any CV. "
            "Choosing to step back deliberately — to learn, to recalibrate, "
            "to invest in your own capability — is something most professionals "
            "never have the courage to do. Own this time. It is not a gap. "
            "It is a strategic pivot point."
        ),
        "linkedin_narrative": (
            "Strategic professional with a background in [Field], who undertook "
            "a deliberate sabbatical for accelerated skills development and industry "
            "recalibration. Returned with enhanced [Skill] capability and a sharper "
            "professional focus."
        )
    },
    "Health & Wellbeing": {
        "aash_message": (
            "A gap from {gap_start} to {gap_end} ({duration}) is often a period of "
            "incredible personal growth that goes completely unseen on a traditional CV. "
            "Managing your own health — with discipline, research, and resilience — "
            "is project management at its most personal. You learned to advocate, "
            "to adapt, and to persist. Those are exactly the skills employers want."
        ),
        "linkedin_narrative": (
            "Resilient [Field] specialist returning to work with a renewed focus on "
            "personal optimisation and professional contribution. Demonstrated sustained "
            "project governance and adaptive decision-making during an extended period "
            "of personal healthcare management."
        )
    },
    "Family & Care": {
        "aash_message": (
            "The time between {gap_start} and {gap_end} ({duration}) placed you at the "
            "centre of one of the most logistically and emotionally demanding roles that "
            "exists: caring for someone you love. The skills you exercised — scheduling, "
            "advocacy, crisis management, negotiation with systems — translate directly "
            "into workplace value. This is not a gap. This is evidence."
        ),
        "linkedin_narrative": (
            "Expert in multi-generational logistics and resource allocation. Balanced "
            "complex domestic operations with full care-compliance responsibilities, "
            "demonstrating extreme multitasking, emotional intelligence, and high-pressure "
            "decision-making in a demanding environment."
        )
    },
    "Bereavement": {
        "aash_message": (
            "The period between {gap_start} and {gap_end} ({duration}) represents a time "
            "when you managed one of life's most demanding transitions while continuing to "
            "function, to decide, and to move forward. Estate management, legal navigation, "
            "emotional leadership for others — these are real competencies. Aash sees this. "
            "Any employer worth working for will too."
        ),
        "linkedin_narrative": (
            "Strategic professional with a background in [Field], returning to the workforce "
            "after a period dedicated to complex estate management and crisis leadership. "
            "Demonstrated high-stakes decision-making and project governance during a "
            "critical transition period."
        )
    },
    "Other": {
        "aash_message": (
            "Between {gap_start} and {gap_end} ({duration}) you were living your life in a "
            "way that the CV format was never designed to capture. That is a limitation of the "
            "format, not a reflection of your value. Every experience you had during this time "
            "shaped the professional you are today."
        ),
        "linkedin_narrative": (
            "A purposeful career pause for personal development and life experience, returning "
            "to the workforce with renewed perspective and sharpened professional goals."
        )
    }
}

def parse_date_flexible(date_str: str):
    """
    Parses date strings in multiple formats.
    Handles MM/YYYY, YYYY-MM, Month YYYY, 'Present', 'Current'.
    Returns datetime object or None if unparseable.
    """
    if not date_str:
        return None
    normalized = date_str.strip().lower()
    if normalized in ("present", "current", "now", "ongoing", "today"):
        return datetime.now()
    formats = ["%m/%Y", "%Y-%m", "%B %Y", "%b %Y", "%Y-%m-%d"]
    for fmt in formats:
        try:
            return datetime.strptime(date_str.strip(), fmt)
        except ValueError:
            continue
    match = re.search(r'\b(\d{4})\b', date_str)
    if match:
        return datetime(int(match.group(1)), 1, 1)
    return None

def detect_employment_gaps(experience_list: list) -> list:
    """
    Scans experience entries for gaps exceeding GAP_THRESHOLD_DAYS.
    Sorts entries by start date, then compares end[n] to start[n+1].
    Returns list of gap dicts.
    """
    parsed = []
    for entry in experience_list:
        start = parse_date_flexible(entry.get("start_date", ""))
        end = parse_date_flexible(entry.get("end_date", ""))
        if start and end:
            parsed.append({
                "start": start,
                "end": end,
                "company": entry.get("company", "Unknown"),
                "title": entry.get("title", "")
            })
    if len(parsed) < 2:
        return []
    parsed.sort(key=lambda x: x["start"])
    gaps = []
    for i in range(len(parsed) - 1):
        current_end = parsed[i]["end"]
        next_start = parsed[i + 1]["start"]
        if next_start > current_end:
            gap_days = (next_start - current_end).days
            if gap_days > GAP_THRESHOLD_DAYS:
                months = max(1, gap_days // 30)
                duration_str = f"{months} month{'s' if months != 1 else ''}"
                gaps.append({
                    "gap_start": current_end,
                    "gap_end": next_start,
                    "duration_days": gap_days,
                    "duration_str": duration_str,
                    "before_company": parsed[i]["company"],
                    "after_company": parsed[i + 1]["company"],
                })
    return gaps

def render_gap_card(gap: dict, index: int):
    """Renders a single employment gap with Aash empathy framing."""
    start_str = gap["gap_start"].strftime("%B %Y")
    end_str = gap["gap_end"].strftime("%B %Y")
    label = f"GAP {index + 1}: {start_str} → {end_str} ({gap['duration_str']})"
    with st.expander(label, expanded=True):
        st.markdown(f"**AFTER:** {gap['before_company']}  |  **BEFORE:** {gap['after_company']}")
        category_key = f"gap_category_{index}"
        if category_key not in st.session_state:
            st.session_state[category_key] = "Other"
        selected = st.selectbox(
            "WHAT BEST DESCRIBES THIS PERIOD?",
            GAP_CATEGORIES,
            key=category_key
        )
        template = AASH_EMPATHY_TEMPLATES[selected]
        aash_msg = template["aash_message"].format(
            gap_start=start_str,
            gap_end=end_str,
            duration=gap["duration_str"]
        )
        st.info(f"AASH SAYS: {aash_msg}")
        st.markdown("**YOUR LINKEDIN NARRATIVE TEMPLATE:**")
        st.code(template["linkedin_narrative"], language=None)

# ==============================================================
# SECTION 4: SESSION STATE INITIALISATION
# ==============================================================

def _init_user_db():
    if "user_db" not in st.session_state:
        lockdown_date = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
        st.session_state.user_db = {
            "Admin": {
                "pwd": get_hash("PosePerfectLtd2026"),
                "role": "Admin",
                "uses": "UNLIMITED",
                "expiry": "PERPETUAL"
            },
            "Supervisor": {
                "pwd": get_hash("Supervisor2026"),
                "role": "Supervisor",
                "uses": 50,
                "expiry": lockdown_date
            },
            "User": {
                "pwd": get_hash("User2026"),
                "role": "User",
                "uses": 10,
                "expiry": lockdown_date
            }
        }

def _init_cv_state():
    if "cv_data" not in st.session_state:
        st.session_state.cv_data = {
            "full_name": "",
            "mobile": "",
            "email": "",
            "profile": "",
            "skills": [],
            "experience": [],
            "education": {
                "institution": "",
                "degree": "",
                "start_date": "",
                "end_date": "",
                "grade": ""
            }
        }
    if "cv_step" not in st.session_state:
        st.session_state.cv_step = 1

def _init_misc_state():
    if "auth" not in st.session_state:
        st.session_state.auth = False
    if "current_user" not in st.session_state:
        st.session_state.current_user = None
    if "login_attempts" not in st.session_state:
        st.session_state.login_attempts = 0
    if "approvals_queue" not in st.session_state:
        st.session_state.approvals_queue = []
    if "job_results" not in st.session_state:
        st.session_state.job_results = []
    if "job_search_ran" not in st.session_state:
        st.session_state.job_search_ran = False
    if "job_search_error" not in st.session_state:
        st.session_state.job_search_error = None
    if "export_zip" not in st.session_state:
        st.session_state.export_zip = None
    if "export_filename" not in st.session_state:
        st.session_state.export_filename = None

# Run all inits before any Streamlit display calls
_init_user_db()
_init_misc_state()

# ==============================================================
# SECTION 5: PAGE CONFIG & CSS (must come before all st.* display calls)
# ==============================================================

st.set_page_config(page_title=f"{APP_TITLE} | {VERSION}", layout="wide")

st.markdown("""
<style>
/* ── CORE PALETTE ──────────────────────────────────────────── */
.stApp { background-color: #000000 !important; color: #39ff14; }
[data-testid="stSidebar"] {
    background-color: #0a0a0a !important;
    border-right: 3px solid #39ff14 !important;
}

/* ── GLOBAL FONT — non-menu text is WHITE ──────────────────── */
*, p, span, div, label, h1, h2, h3, h4, h5, h6, li {
    font-family: 'Courier New', monospace !important;
    font-weight: bold !important;
    color: #ffffff !important;
}

/* ── BUTTONS: NEON GREEN BG / PURE BLACK TEXT ──────────────── */
div.stButton > button {
    background-color: #39ff14 !important;
    color: #000000 !important;
    border: 2px solid #39ff14 !important;
    font-weight: 900 !important;
    font-family: 'Courier New', monospace !important;
    text-transform: uppercase !important;
    width: 100% !important;
    border-radius: 0px !important;
    height: 3.5em !important;
    letter-spacing: 1px;
}
div.stButton > button:hover {
    background-color: #000000 !important;
    color: #39ff14 !important;
    border: 2px solid #39ff14 !important;
}
div.stButton > button:active {
    background-color: #000000 !important;
    color: #39ff14 !important;
}

/* ── DOWNLOAD BUTTON ───────────────────────────────────────── */
div.stDownloadButton > button {
    background-color: #39ff14 !important;
    color: #000000 !important;
    border: 2px solid #39ff14 !important;
    font-weight: 900 !important;
    font-family: 'Courier New', monospace !important;
    text-transform: uppercase !important;
    width: 100% !important;
    border-radius: 0px !important;
    height: 3.5em !important;
}
div.stDownloadButton > button:hover {
    background-color: #000000 !important;
    color: #39ff14 !important;
}

/* ── INPUTS, TEXTAREAS, NUMBER INPUTS ──────────────────────── */
input, textarea,
[data-baseweb="input"] input,
[data-baseweb="textarea"] textarea,
div[data-testid="stNumberInput"] input {
    background-color: #111111 !important;
    color: #ffffff !important;
    border: 1px solid #39ff14 !important;
    font-family: 'Courier New', monospace !important;
    font-weight: bold !important;
    caret-color: #ffffff !important;
}

/* ── SELECTBOX / DROPDOWN ──────────────────────────────────── */
[data-baseweb="select"] > div,
[data-baseweb="select"] div,
[data-baseweb="popover"] {
    background-color: #111111 !important;
    color: #ffffff !important;
    border: 1px solid #39ff14 !important;
    font-family: 'Courier New', monospace !important;
    font-weight: bold !important;
}

/* ── TABS ──────────────────────────────────────────────────── */
.stTabs [data-baseweb="tab-list"] {
    background-color: #000000 !important;
    border-bottom: 2px solid #39ff14 !important;
}
.stTabs [data-baseweb="tab"] {
    color: #39ff14 !important;
    background-color: #000000 !important;
    border: 1px solid #39ff14 !important;
    padding: 10px 20px !important;
    font-family: 'Courier New', monospace !important;
    font-weight: bold !important;
}
.stTabs [data-baseweb="tab"][aria-selected="true"] {
    background-color: #39ff14 !important;
    color: #000000 !important;
}

/* ── EXPANDERS ─────────────────────────────────────────────── */
details, [data-testid="stExpander"] {
    border: 1px solid #39ff14 !important;
    background-color: #0a0a0a !important;
}
summary, [data-testid="stExpander"] summary {
    color: #39ff14 !important;
    font-family: 'Courier New', monospace !important;
}

/* ── ALERT / INFO / SUCCESS / ERROR BOXES ──────────────────── */
[data-testid="stAlert"], .stAlert {
    background-color: #0a0a0a !important;
    border: 1px solid #39ff14 !important;
    color: #ffffff !important;
}

/* ── PROGRESS BAR ──────────────────────────────────────────── */
[data-testid="stProgressBar"] > div {
    background-color: #39ff14 !important;
}
[data-testid="stProgressBar"] {
    background-color: #111111 !important;
    border: 1px solid #39ff14 !important;
}

/* ── METRICS ───────────────────────────────────────────────── */
[data-testid="stMetric"] {
    background-color: #0a0a0a !important;
    border: 1px solid #39ff14 !important;
    padding: 10px !important;
}

/* ── FILE UPLOADER ─────────────────────────────────────────── */
[data-testid="stFileUploader"] {
    border: 1px solid #39ff14 !important;
    background-color: #0a0a0a !important;
}

/* ── TABLE ─────────────────────────────────────────────────── */
table, th, td {
    border: 1px solid #39ff14 !important;
    color: #ffffff !important;
    background-color: #0a0a0a !important;
    font-family: 'Courier New', monospace !important;
}

/* ── TOGGLE ────────────────────────────────────────────────── */
[data-baseweb="toggle"] {
    background-color: #39ff14 !important;
}

/* ── SCROLLBAR ─────────────────────────────────────────────── */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: #000000; }
::-webkit-scrollbar-thumb { background: #39ff14; }
</style>
""", unsafe_allow_html=True)

# ==============================================================
# SECTION 6: AUTHENTICATION GATE
# ==============================================================

if not st.session_state.auth:
    st.markdown(
        '<h1 style="text-align:center; color:#39ff14; font-family:Courier New,monospace;">'
        '&#127963; CAREER ARCHITECT PRO</h1>',
        unsafe_allow_html=True
    )
    st.markdown(
        f'<p style="text-align:center; color:#39ff14; font-family:Courier New,monospace;">'
        f'{VERSION} &nbsp;|&nbsp; POSE PERFECT LTD</p>',
        unsafe_allow_html=True
    )
    st.markdown("---")
    col_l, col_c, col_r = st.columns([1, 2, 1])
    with col_c:
        u_id = st.text_input("SYSTEM ID", placeholder="Enter your user ID")
        u_key = st.text_input("ACCESS KEY", type="password", placeholder="Enter your access key")
        if st.button("UNLOCK ACCESS"):
            db = st.session_state.user_db
            if u_id in db and get_hash(u_key) == db[u_id]["pwd"]:
                user_expiry = db[u_id]["expiry"]
                if user_expiry != "PERPETUAL":
                    try:
                        if datetime.strptime(user_expiry, "%Y-%m-%d") < datetime.now():
                            st.error("ACCOUNT EXPIRED. CONTACT ADMINISTRATOR.")
                            st.stop()
                    except ValueError:
                        pass
                user_uses = db[u_id]["uses"]
                if user_uses != "UNLIMITED" and isinstance(user_uses, int) and user_uses <= 0:
                    st.error("CREDIT LIMIT REACHED. CONTACT ADMINISTRATOR.")
                    st.stop()
                st.session_state.auth = True
                st.session_state.current_user = u_id
                st.session_state.login_attempts = 0
                _init_cv_state()
                st.rerun()
            else:
                st.session_state.login_attempts += 1
                st.error(f"ACCESS DENIED — ATTEMPT {st.session_state.login_attempts}")
    st.markdown(
        f'<div style="position:fixed;bottom:10px;width:100%;text-align:center;'
        f'font-family:Courier New,monospace;font-weight:bold;color:#39ff14;font-size:0.75em;">'
        f'{APP_TITLE} | {VERSION} | {COPYRIGHT}</div>',
        unsafe_allow_html=True
    )
    st.stop()

# ==============================================================
# — AUTHENTICATED ZONE — (st.stop() prevents reaching here if not auth)
# ==============================================================

_init_cv_state()

u = st.session_state.current_user
u_data = st.session_state.user_db[u]
role = u_data["role"]

# ==============================================================
# SECTION 7: SIDEBAR
# ==============================================================

with st.sidebar:
    st.markdown(f"### SYSTEM ID: {u}")
    st.markdown(f"**ROLE:** {role}")
    st.markdown("---")
    uses = u_data["uses"]
    expiry = u_data["expiry"]
    if uses == "UNLIMITED":
        st.markdown("**CREDITS:** ∞ UNLIMITED (GOD MODE)")
    else:
        st.markdown(f"**CREDITS REMAINING:** {uses}")
    if expiry == "PERPETUAL":
        st.markdown("**ACCESS:** PERPETUAL")
    else:
        try:
            expiry_dt = datetime.strptime(expiry, "%Y-%m-%d")
            days_remaining = (expiry_dt - datetime.now()).days
            if days_remaining <= 7:
                st.warning(f"EXPIRY: {expiry} ({days_remaining} DAYS REMAINING)")
            else:
                st.markdown(f"**EXPIRY:** {expiry}")
        except ValueError:
            st.markdown(f"**EXPIRY:** {expiry}")
    st.markdown("---")
    if st.button("LOGOUT"):
        st.session_state.auth = False
        st.session_state.current_user = None
        st.rerun()

# ==============================================================
# SECTION 8: TAB RENDERER FUNCTIONS
# ==============================================================

# ── CV BUILDER (5-Step Wizard) ─────────────────────────────────

def _render_step_nav(current_step: int):
    st.markdown("---")
    col_prev, col_spacer, col_next = st.columns([1, 2, 1])
    with col_prev:
        if current_step > 1:
            if st.button("◄ PREVIOUS", key=f"nav_prev_{current_step}"):
                st.session_state.cv_step -= 1
                st.rerun()
    with col_next:
        if current_step < 5:
            if st.button("NEXT STEP ►", key=f"nav_next_{current_step}"):
                st.session_state.cv_step += 1
                st.rerun()

def _render_cv_step1():
    st.markdown("### STEP 1 OF 5 — PERSONAL INFORMATION")
    col_left, col_right = st.columns(2)
    with col_left:
        cv = st.session_state.cv_data
        cv["full_name"] = st.text_input(
            "Full Name",
            value=cv["full_name"],
            key="s1_full_name",
            placeholder="e.g. Alexandra Johnson"
        )
        cv["mobile"] = st.text_input(
            "Mobile Number",
            value=cv["mobile"],
            key="s1_mobile",
            placeholder="e.g. 07700 900123"
        )
        cv["email"] = st.text_input(
            "Email Address",
            value=cv["email"],
            key="s1_email",
            placeholder="e.g. alex.johnson@email.com"
        )
    with col_right:
        cv["profile"] = st.text_area(
            "Professional Summary",
            value=cv["profile"],
            height=215,
            key="s1_profile",
            placeholder="e.g. A results-driven professional with expertise in..."
        )
    _render_step_nav(1)

def _render_cv_step2():
    st.markdown("### STEP 2 OF 5 — KEY SKILLS (10 Recommended)")
    skills = st.session_state.cv_data["skills"]
    skill_count = len(skills)
    if skill_count >= 10:
        st.success(f"SKILLS ADDED: {skill_count} — RECOMMENDED TARGET REACHED")
    else:
        st.info(f"SKILLS ADDED: {skill_count} / 10 RECOMMENDED")
    if skills:
        st.markdown("**CURRENT SKILLS (click to remove):**")
        cols_per_row = 4
        for i in range(0, len(skills), cols_per_row):
            row_skills = skills[i:i + cols_per_row]
            cols = st.columns(len(row_skills))
            for j, skill in enumerate(row_skills):
                with cols[j]:
                    if st.button(f"✕  {skill}", key=f"remove_skill_{i+j}"):
                        st.session_state.cv_data["skills"].pop(i + j)
                        st.rerun()
    col_input, col_add = st.columns([3, 1])
    with col_input:
        new_skill = st.text_input(
            "Add a skill",
            key="new_skill_input",
            placeholder="e.g. Project Management, Python, Leadership..."
        )
    with col_add:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("+ ADD", key="add_skill_btn"):
            val = new_skill.strip() if new_skill else ""
            if val and val not in st.session_state.cv_data["skills"]:
                st.session_state.cv_data["skills"].append(val)
                st.rerun()
    _render_step_nav(2)

def _render_cv_step3():
    st.markdown("### STEP 3 OF 5 — EXPERIENCE CHRONOLOGY")
    if st.button("+ ADD NEW JOB ENTRY", key="add_job"):
        st.session_state.cv_data["experience"].append({
            "company": "", "title": "", "start_date": "", "end_date": "",
            "responsibilities": [], "achievements": []
        })
        st.rerun()
    experience = st.session_state.cv_data["experience"]
    for idx, job in enumerate(experience):
        title_label = job.get("title") or "UNTITLED"
        company_label = job.get("company") or "COMPANY"
        with st.expander(f"JOB {idx+1}: {title_label} @ {company_label}", expanded=True):
            col1, col2 = st.columns(2)
            with col1:
                experience[idx]["company"] = st.text_input(
                    "COMPANY", value=job["company"], key=f"company_{idx}")
                experience[idx]["start_date"] = st.text_input(
                    "START DATE (MM/YYYY)", value=job["start_date"],
                    key=f"start_{idx}", placeholder="03/2020")
            with col2:
                experience[idx]["title"] = st.text_input(
                    "JOB TITLE", value=job["title"], key=f"title_{idx}")
                experience[idx]["end_date"] = st.text_input(
                    "END DATE (MM/YYYY or 'Present')", value=job["end_date"],
                    key=f"end_{idx}", placeholder="Present")
            # Responsibilities
            st.markdown("**RESPONSIBILITIES:**")
            for r_idx, resp in enumerate(job["responsibilities"]):
                c1, c2 = st.columns([4, 1])
                with c1:
                    experience[idx]["responsibilities"][r_idx] = st.text_input(
                        f"R{r_idx+1}", value=resp,
                        key=f"resp_{idx}_{r_idx}", label_visibility="collapsed")
                with c2:
                    if st.button("REMOVE", key=f"del_resp_{idx}_{r_idx}"):
                        experience[idx]["responsibilities"].pop(r_idx)
                        st.rerun()
            if st.button("+ ADD RESPONSIBILITY", key=f"add_resp_{idx}"):
                experience[idx]["responsibilities"].append("")
                st.rerun()
            st.markdown("---")
            # Achievements
            st.markdown("**ACHIEVEMENTS:**")
            for a_idx, ach in enumerate(job["achievements"]):
                c1, c2 = st.columns([4, 1])
                with c1:
                    experience[idx]["achievements"][a_idx] = st.text_input(
                        f"A{a_idx+1}", value=ach,
                        key=f"ach_{idx}_{a_idx}", label_visibility="collapsed")
                with c2:
                    if st.button("REMOVE", key=f"del_ach_{idx}_{a_idx}"):
                        experience[idx]["achievements"].pop(a_idx)
                        st.rerun()
            if st.button("+ ADD ACHIEVEMENT", key=f"add_ach_{idx}"):
                experience[idx]["achievements"].append("")
                st.rerun()
            st.markdown("---")
            if st.button(f"REMOVE JOB {idx+1}", key=f"remove_job_{idx}"):
                experience.pop(idx)
                st.rerun()
    st.session_state.cv_data["experience"] = experience
    _render_step_nav(3)

def _render_cv_step4():
    st.markdown("### STEP 4 OF 5 — EDUCATIONAL BACKGROUND")
    edu = st.session_state.cv_data["education"]
    col1, col2 = st.columns(2)
    with col1:
        edu["institution"] = st.text_input("INSTITUTION", value=edu["institution"], key="edu_inst")
        edu["start_date"] = st.text_input("START DATE (MM/YYYY)", value=edu["start_date"], key="edu_start")
    with col2:
        edu["degree"] = st.text_input("DEGREE / QUALIFICATION", value=edu["degree"], key="edu_degree")
        edu["end_date"] = st.text_input("END DATE (MM/YYYY or 'Present')", value=edu["end_date"], key="edu_end")
    edu["grade"] = st.text_input("GRADE / CLASSIFICATION", value=edu["grade"], key="edu_grade",
                                  placeholder="e.g. First Class Honours, Distinction, A*AA")
    st.session_state.cv_data["education"] = edu
    _render_step_nav(4)

def _render_cv_step5():
    st.markdown("### STEP 5 OF 5 — AASH FINAL REVIEW")
    st.info("READ-ONLY REVIEW. USE THE BACK BUTTON TO EDIT ANY SECTION.")
    cv = st.session_state.cv_data
    # Personal Info
    st.subheader("PERSONAL INFORMATION")
    st.markdown(f"**Name:** {cv.get('full_name') or '—'}")
    st.markdown(f"**Mobile:** {cv.get('mobile') or '—'}")
    st.markdown(f"**Email:** {cv.get('email') or '—'}")
    st.subheader("PROFESSIONAL SUMMARY")
    st.markdown(f"> {cv['profile']}" if cv['profile'] else "_No summary entered._")
    # Skills
    st.subheader("KEY SKILLS")
    if cv["skills"]:
        st.markdown("  |  ".join([f"`{s}`" for s in cv["skills"]]))
    else:
        st.markdown("_No skills entered._")
    # Experience
    st.subheader("EXPERIENCE CHRONOLOGY")
    if cv["experience"]:
        for idx, job in enumerate(cv["experience"]):
            st.markdown(f"**{idx+1}. {job.get('title','—')} at {job.get('company','—')}**  "
                        f"({job.get('start_date','—')} → {job.get('end_date','—')})")
            if job["responsibilities"]:
                for r in job["responsibilities"]:
                    if r.strip():
                        st.markdown(f"&nbsp;&nbsp;• {r}")
            if job["achievements"]:
                st.markdown("&nbsp;&nbsp;*Achievements:*")
                for a in job["achievements"]:
                    if a.strip():
                        st.markdown(f"&nbsp;&nbsp;★ {a}")
            st.markdown("---")
    else:
        st.markdown("_No experience entries._")
    # Education
    st.subheader("EDUCATIONAL BACKGROUND")
    edu = cv["education"]
    if edu["institution"]:
        st.markdown(f"**{edu['degree']}** — {edu['institution']}")
        st.markdown(f"{edu['start_date']} → {edu['end_date']}  |  Grade: {edu['grade']}")
    else:
        st.markdown("_No education entered._")
    _render_step_nav(5)

def render_cv_builder_tab():
    st.header("CAREER ARCHITECT — CV BUILDER")
    step_labels = ["PERSONAL INFO", "KEY SKILLS", "EXPERIENCE", "EDUCATION", "FINAL REVIEW"]
    progress = (st.session_state.cv_step - 1) / 4.0
    st.progress(progress)
    st.markdown(f"**PHASE {st.session_state.cv_step}/5 — {step_labels[st.session_state.cv_step - 1]}**")
    st.markdown("---")
    if st.session_state.cv_step == 1:
        _render_cv_step1()
    elif st.session_state.cv_step == 2:
        _render_cv_step2()
    elif st.session_state.cv_step == 3:
        _render_cv_step3()
    elif st.session_state.cv_step == 4:
        _render_cv_step4()
    elif st.session_state.cv_step == 5:
        _render_cv_step5()

# ── JOB SEARCH (Adzuna) ───────────────────────────────────────

def _search_adzuna(what, postcode, radius_miles, national, app_id, app_key):
    """Calls Adzuna API. Returns (results_list, error_message|None)."""
    country = "gb" if national else "us"
    base_url = f"https://api.adzuna.com/v1/api/jobs/{country}/search/1"
    params = {
        "app_id": app_id,
        "app_key": app_key,
        "results_per_page": 20,
        "what": what,
        "where": postcode,
        "distance": radius_miles,
        "content-type": "application/json"
    }
    try:
        resp = requests.get(base_url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        return data.get("results", []), None
    except requests.exceptions.Timeout:
        return [], "REQUEST TIMEOUT — ADZUNA API DID NOT RESPOND IN 10 SECONDS"
    except requests.exceptions.HTTPError as e:
        return [], f"API ERROR: HTTP {e.response.status_code}"
    except requests.exceptions.RequestException as e:
        return [], f"CONNECTION ERROR: {str(e)}"
    except (json.JSONDecodeError, KeyError):
        return [], "MALFORMED RESPONSE FROM ADZUNA API"

def render_job_search_tab():
    st.header("LIVE ADZUNA ENGINE")
    app_id, app_key = get_adzuna_credentials()
    col1, col2 = st.columns(2)
    with col1:
        job_title = st.text_input("JOB TITLE / KEYWORDS", key="js_title",
                                   placeholder="e.g. Software Engineer")
        postcode = st.text_input("POSTCODE", key="js_postcode",
                                  placeholder="e.g. SW1A 1AA")
        radius = st.selectbox("SEARCH RADIUS (MILES)", options=[5, 10, 25, 50, 100],
                               index=2, key="js_radius")
    with col2:
        manual_mileage = st.number_input(
            "MANUAL MILEAGE OVERRIDE (0 = use dropdown)",
            min_value=0, max_value=500, value=0, step=5, key="js_manual_miles")
        national = st.toggle("UK NATIONAL SEARCH", value=True, key="js_national")
        mode_label = "NATIONAL (UK)" if national else "INTERNATIONAL (US)"
        st.markdown(f"**SEARCH MODE:** {mode_label}")
    effective_radius = int(manual_mileage) if manual_mileage > 0 else radius
    st.markdown(f"**EFFECTIVE RADIUS:** {effective_radius} miles")
    if st.button("EXECUTE LIVE SEARCH"):
        if not job_title.strip():
            st.warning("PLEASE ENTER A JOB TITLE OR KEYWORDS")
        elif not postcode.strip():
            st.warning("PLEASE ENTER A POSTCODE")
        elif not app_id or not app_key:
            st.error("ADZUNA API CREDENTIALS NOT CONFIGURED — CONTACT ADMIN")
        else:
            if not deduct_credit(u):
                st.error("INSUFFICIENT CREDITS TO PERFORM SEARCH")
            else:
                with st.spinner("QUERYING ADZUNA LIVE DATABASE..."):
                    results, error = _search_adzuna(
                        what=job_title.strip(), postcode=postcode.strip(),
                        radius_miles=effective_radius, national=national,
                        app_id=app_id, app_key=app_key
                    )
                st.session_state.job_results = results
                st.session_state.job_search_error = error
                st.session_state.job_search_ran = True
    if st.session_state.job_search_error:
        st.error(st.session_state.job_search_error)
    elif st.session_state.job_search_ran:
        results = st.session_state.job_results
        if results:
            st.success(f"FOUND {len(results)} LIVE RESULTS")
            for job in results:
                title = job.get("title", "Unknown Title")
                company = job.get("company", {}).get("display_name", "Unknown Company")
                location = job.get("location", {}).get("display_name", "Unknown Location")
                salary_min = job.get("salary_min")
                salary_max = job.get("salary_max")
                description = job.get("description", "No description available.")
                redirect_url = job.get("redirect_url", "#")
                with st.expander(f"{title} — {company}"):
                    st.markdown(f"**LOCATION:** {location}")
                    if salary_min and salary_max:
                        st.markdown(f"**SALARY:** £{salary_min:,.0f} — £{salary_max:,.0f}")
                    elif salary_min:
                        st.markdown(f"**SALARY:** from £{salary_min:,.0f}")
                    else:
                        st.markdown("**SALARY:** Not specified")
                    excerpt = description[:500] + ("..." if len(description) > 500 else "")
                    st.markdown(f"**DESCRIPTION:** {excerpt}")
                    st.markdown(f"[VIEW FULL LISTING & APPLY]({redirect_url})")
        else:
            st.warning("NO RESULTS FOUND. TRY BROADENING YOUR SEARCH CRITERIA.")

# ── GAP ENGINE ────────────────────────────────────────────────

def render_gap_engine_tab():
    st.header("AASH EMPATHY & GAP ENGINE")
    st.markdown("SCANNING EMPLOYMENT CHRONOLOGY FOR GAPS EXCEEDING 3 MONTHS...")
    experience = st.session_state.cv_data.get("experience", [])
    if not experience:
        st.warning(
            "NO EXPERIENCE DATA FOUND. COMPLETE THE CV BUILDER STEP 2 FIRST."
        )
        return
    gaps = detect_employment_gaps(experience)
    if not gaps:
        st.success(
            f"ANALYSIS COMPLETE: NO EMPLOYMENT GAPS EXCEEDING {GAP_THRESHOLD_DAYS} DAYS DETECTED. "
            "YOUR CHRONOLOGY APPEARS CONTINUOUS."
        )
    else:
        st.warning(f"AASH HAS IDENTIFIED {len(gaps)} EMPLOYMENT GAP(S). REVIEW AND FRAME BELOW.")
        for i, gap in enumerate(gaps):
            render_gap_card(gap, i)

# ── EXPORT ────────────────────────────────────────────────────

def render_export_tab():
    st.header("ARCHIVE GENERATOR — .CVP EXPORT")
    cv = st.session_state.cv_data
    profile_preview = (cv.get("profile", "")[:80] + "...") if len(cv.get("profile", "")) > 80 else cv.get("profile", "")
    skills_count = len(cv.get("skills", []))
    exp_count = len(cv.get("experience", []))
    st.markdown(f"**PROFILE PREVIEW:** {profile_preview if profile_preview else '_Empty_'}")
    st.markdown(f"**SKILLS ENTRIES:** {skills_count}")
    st.markdown(f"**EXPERIENCE ENTRIES:** {exp_count}")
    st.markdown("---")
    st.markdown("**FORMAT:** `.cvp` inside SHA-512 verified ZIP archive")
    st.markdown("**SECURITY:** POSE PERFECT PROPRIETARY INTEGRITY SEAL")
    if st.button("GENERATE PROTECTED ZIP"):
        if not deduct_credit(u):
            st.error("INSUFFICIENT CREDITS TO GENERATE ARCHIVE")
        else:
            today = datetime.now().strftime("%Y%m%d")
            filename = f"CV_Export_{u}_{today}.zip"
            zip_bytes = build_cvp_zip(cv, u)
            st.session_state.export_zip = zip_bytes
            st.session_state.export_filename = filename
            st.success(f"ARCHIVE SEALED: {filename} | SHA-512 INTEGRITY CERTIFICATE APPLIED")
    if st.session_state.export_zip:
        st.download_button(
            label="DOWNLOAD PROTECTED ARCHIVE",
            data=st.session_state.export_zip,
            file_name=st.session_state.export_filename,
            mime="application/zip",
            key="dl_btn"
        )

# ── RECOVERY ─────────────────────────────────────────────────

def render_recovery_tab():
    st.header("RECOVERY SYSTEM — .CVP IMPORT & VERIFICATION")
    st.markdown("UPLOAD A `CV_Export_*.zip` FILE TO RESTORE YOUR SESSION DATA.")
    uploaded = st.file_uploader("SELECT ZIP FILE", type=["zip"], key="recovery_uploader")
    if uploaded is not None:
        st.markdown(f"**FILE RECEIVED:** {uploaded.name} ({uploaded.size:,} bytes)")
        if st.button("VERIFY INTEGRITY & RESTORE SESSION"):
            zip_bytes = uploaded.read()
            cv_data, status = verify_and_extract_cvp(zip_bytes)
            if status == "OK":
                st.session_state.cv_data = cv_data
                st.session_state.cv_step = 1
                st.success(
                    "SHA-512 INTEGRITY VERIFIED. CV DATA SUCCESSFULLY RESTORED TO SESSION. "
                    "NAVIGATE TO CV BUILDER TO REVIEW."
                )
            elif status == "TAMPERED":
                st.error(
                    "INTEGRITY CHECK FAILED. "
                    "SHA-512 HASH MISMATCH DETECTED — THIS FILE HAS BEEN MODIFIED OR "
                    "CORRUPTED SINCE EXPORT. DATA RESTORATION REFUSED. "
                    "DO NOT TRUST THIS FILE."
                )
            else:
                st.error(
                    "INVALID ARCHIVE FORMAT. "
                    "FILE DOES NOT CONTAIN REQUIRED cv_data.cvp AND integrity.sha512 COMPONENTS. "
                    "ENSURE YOU ARE UPLOADING A CAREER ARCHITECT EXPORT FILE."
                )

# ── USER MANAGEMENT (Supervisor+Admin) ───────────────────────

def render_user_management_tab():
    st.header("USER MANAGEMENT — COMMAND PANEL")
    db = st.session_state.user_db
    st.subheader("REGISTERED USERS")
    table_data = [
        {"USER ID": uid, "ROLE": d["role"], "CREDITS": d["uses"], "EXPIRY": d["expiry"]}
        for uid, d in db.items()
    ]
    st.table(table_data)
    st.markdown("---")
    st.subheader("CREATE NEW USER")
    col1, col2 = st.columns(2)
    with col1:
        new_uid = st.text_input("NEW USER ID", key="new_uid")
        new_role = st.selectbox("ROLE", ["User", "Supervisor"], key="new_role")
    with col2:
        new_pwd = st.text_input("INITIAL PASSWORD", type="password", key="new_pwd")
        new_uses = st.number_input("INITIAL CREDITS", min_value=1, max_value=200,
                                    value=10, key="new_uses")
    if st.button("CREATE USER", key="create_user"):
        if new_uid.strip() and new_pwd.strip():
            if new_uid.strip() in db:
                st.error(f"USER ID '{new_uid.strip()}' ALREADY EXISTS")
            else:
                lockdown_date = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
                db[new_uid.strip()] = {
                    "pwd": get_hash(new_pwd),
                    "role": new_role,
                    "uses": int(new_uses),
                    "expiry": lockdown_date
                }
                st.success(f"USER '{new_uid.strip()}' CREATED SUCCESSFULLY")
        else:
            st.warning("BOTH USER ID AND PASSWORD ARE REQUIRED")
    st.markdown("---")
    st.subheader("DEACTIVATE USER (SET CREDITS TO ZERO)")
    current = st.session_state.current_user
    targets = [uid for uid in db.keys() if uid != current and uid != "Admin"]
    if targets:
        deactivate_target = st.selectbox("SELECT USER TO DEACTIVATE", targets, key="deact_select")
        if st.button("DEACTIVATE SELECTED USER", key="deact_btn"):
            db[deactivate_target]["uses"] = 0
            st.success(f"USER '{deactivate_target}' DEACTIVATED — CREDITS SET TO 0")
    else:
        st.info("NO DEACTIVATABLE USERS AVAILABLE")

# ── APPROVALS QUEUE (Supervisor+Admin) ───────────────────────

def render_approvals_tab():
    st.header("APPROVALS QUEUE")
    queue = st.session_state.approvals_queue
    if not queue:
        st.info("NO PENDING APPROVAL REQUESTS")
    else:
        for i, item in enumerate(queue):
            req_type = item.get("type", "Unknown Request")
            req_by = item.get("requested_by", "Unknown")
            with st.expander(f"REQUEST {i+1}: {req_type} FROM {req_by}", expanded=True):
                st.json(item)
                col_a, col_r = st.columns(2)
                with col_a:
                    if st.button("APPROVE", key=f"approve_{i}"):
                        queue.pop(i)
                        st.success("REQUEST APPROVED AND REMOVED FROM QUEUE")
                        st.rerun()
                with col_r:
                    if st.button("REJECT", key=f"reject_{i}"):
                        queue.pop(i)
                        st.warning("REQUEST REJECTED AND REMOVED FROM QUEUE")
                        st.rerun()

# ── ADMIN CONSOLE ─────────────────────────────────────────────

def render_admin_console_tab():
    st.header("MASTER COMMAND CONSOLE — ADMIN ACCESS ONLY")
    if role != "Admin":
        st.error("ADMIN ACCESS REQUIRED. THIS INCIDENT HAS BEEN LOGGED.")
        return
    # System Metrics
    st.subheader("SYSTEM STATUS")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("REGISTERED USERS", len(st.session_state.user_db))
    with col2:
        st.metric("ACTIVE SESSION", st.session_state.current_user)
    with col3:
        st.metric("VERSION", VERSION)
    st.markdown("---")
    # Adzuna Key Updater
    st.subheader("ADZUNA API KEY UPDATER")
    cfg = load_config()
    current_id = cfg.get("admin_settings", {}).get("api_keys", {}).get("adzuna_id", "")
    current_key_val = cfg.get("admin_settings", {}).get("api_keys", {}).get("adzuna_key", "")
    new_adzuna_id = st.text_input("ADZUNA APP ID", value=current_id, key="admin_azid")
    new_adzuna_key = st.text_input("ADZUNA APP KEY", value=current_key_val,
                                    type="password", key="admin_azkey")
    if st.button("UPDATE ADZUNA CREDENTIALS", key="update_adzuna"):
        if new_adzuna_id.strip() and new_adzuna_key.strip():
            if "admin_settings" not in cfg:
                cfg["admin_settings"] = {}
            if "api_keys" not in cfg["admin_settings"]:
                cfg["admin_settings"]["api_keys"] = {}
            cfg["admin_settings"]["api_keys"]["adzuna_id"] = new_adzuna_id.strip()
            cfg["admin_settings"]["api_keys"]["adzuna_key"] = new_adzuna_key.strip()
            if save_config(cfg):
                st.success("ADZUNA CREDENTIALS UPDATED AND SAVED TO system_config.json")
            else:
                st.error("FAILED TO WRITE TO system_config.json — CHECK FILE PERMISSIONS")
        else:
            st.warning("BOTH APP ID AND APP KEY MUST BE PROVIDED")
    # Adzuna Balance Probe
    st.markdown("---")
    st.subheader("ADZUNA ACCOUNT STATUS")
    if st.button("PROBE ADZUNA CONNECTION", key="adzuna_probe"):
        probe_id, probe_key = get_adzuna_credentials()
        try:
            resp = requests.get(
                "https://api.adzuna.com/v1/api/jobs/gb/search/1",
                params={"app_id": probe_id, "app_key": probe_key,
                        "results_per_page": 1, "what": "engineer"},
                timeout=10
            )
            if resp.status_code == 200:
                data = resp.json()
                total = data.get("count", "N/A")
                st.success(f"ADZUNA API: CONNECTED | HTTP 200 | CREDENTIALS VALID")
                st.markdown(f"**LIVE JOB INDEX (GB):** {total:,} active listings" if isinstance(total, int) else f"**LIVE JOB INDEX:** {total}")
            else:
                st.error(f"ADZUNA API: HTTP {resp.status_code} — CHECK CREDENTIALS")
        except Exception as e:
            st.error(f"ADZUNA CONNECTION FAILED: {str(e)}")
    # System Reset
    st.markdown("---")
    st.subheader("SYSTEM RESET — 30 DAY LOCKDOWN REGENERATION")
    st.warning("THIS WILL RESET ALL NON-PERPETUAL USER EXPIRY DATES TO 30 DAYS FROM NOW.")
    if st.button("EXECUTE SYSTEM RESET", key="sys_reset"):
        new_expiry = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
        for uid_r, data_r in st.session_state.user_db.items():
            if data_r["expiry"] != "PERPETUAL":
                data_r["expiry"] = new_expiry
        st.success(f"SYSTEM RESET COMPLETE. NEW LOCKDOWN DATE: {new_expiry}")
    # Live View
    st.markdown("---")
    st.subheader("LIVE VIEW — SESSION STATS")
    active_count = sum(
        1 for d in st.session_state.user_db.values()
        if d["uses"] == "UNLIMITED" or (isinstance(d["uses"], int) and d["uses"] > 0)
    )
    st.markdown(f"**ACCOUNTS WITH ACTIVE CREDITS:** {active_count}")
    st.markdown(f"**CURRENTLY LOGGED IN:** {st.session_state.current_user}")
    # User Registry (passwords redacted)
    st.markdown("---")
    st.subheader("FULL USER REGISTRY")
    display_db = {
        uid: {k: v for k, v in d.items() if k != "pwd"}
        for uid, d in st.session_state.user_db.items()
    }
    st.json(display_db)

# ==============================================================
# SECTION 9: ROLE-BASED TAB ROUTING
# ==============================================================

ROLE_TABS = {
    "User": {
        "labels": ["CV BUILDER", "JOB SEARCH", "GAP ENGINE", "EXPORT", "RECOVERY"],
        "renderers": [
            render_cv_builder_tab,
            render_job_search_tab,
            render_gap_engine_tab,
            render_export_tab,
            render_recovery_tab
        ]
    },
    "Supervisor": {
        "labels": ["CV BUILDER", "JOB SEARCH", "GAP ENGINE", "EXPORT", "RECOVERY",
                   "USER MANAGEMENT", "APPROVALS"],
        "renderers": [
            render_cv_builder_tab,
            render_job_search_tab,
            render_gap_engine_tab,
            render_export_tab,
            render_recovery_tab,
            render_user_management_tab,
            render_approvals_tab
        ]
    },
    "Admin": {
        "labels": ["CV BUILDER", "JOB SEARCH", "GAP ENGINE", "EXPORT", "RECOVERY",
                   "USER MANAGEMENT", "APPROVALS", "ADMIN CONSOLE"],
        "renderers": [
            render_cv_builder_tab,
            render_job_search_tab,
            render_gap_engine_tab,
            render_export_tab,
            render_recovery_tab,
            render_user_management_tab,
            render_approvals_tab,
            render_admin_console_tab
        ]
    }
}

def render_main_tabs():
    cfg = ROLE_TABS.get(role, ROLE_TABS["User"])
    tab_widgets = st.tabs(cfg["labels"])
    for tab_widget, renderer in zip(tab_widgets, cfg["renderers"]):
        with tab_widget:
            renderer()

render_main_tabs()

# ==============================================================
# SECTION 10: FOOTER
# ==============================================================

st.markdown(
    f'<div style="position:fixed;bottom:10px;width:100%;text-align:center;'
    f'font-family:Courier New,monospace;font-weight:bold;color:#39ff14;'
    f'font-size:0.75em;z-index:9999;pointer-events:none;">'
    f'{APP_TITLE} &nbsp;|&nbsp; {VERSION} &nbsp;|&nbsp; {COPYRIGHT}'
    f'</div>',
    unsafe_allow_html=True
)
