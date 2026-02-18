# CLAUDE.md — Aash-Architect / Career Architect Pro

## Project Overview

**Career Architect Pro** is a Streamlit-based web application built for career coaching professionals. It provides a role-gated, multi-user environment for CV building, live job searching, employment gap analysis, and CV data archival/recovery.

Copyright © 2026 Pose Perfect Ltd. All rights reserved.

---

## Repository Structure

```
Aash-Architect/
├── Career_Architect_Web.py   # Primary application — Streamlit web UI (main entry point)
├── Career_Architect_User.py  # Legacy Tkinter desktop UI (older prototype)
├── architect_core.py         # Entry-point wrapper referencing ArchitectCore class
├── requirements.txt          # Python dependencies
├── system_config.json        # Branding, API keys, admin hash (do not commit secrets)
└── user_registry.json        # Persistent user data store
```

---

## Running the Application

```bash
# Install dependencies
pip install -r requirements.txt

# Launch the web application
streamlit run Career_Architect_Web.py
```

The app runs on `http://localhost:8501` by default.

---

## Architecture

### Authentication & Role System

`Career_Architect_Web.py` uses an in-session user database (`st.session_state.user_db`) with three built-in roles:

| Role       | Tabs Available                                                      | Credits       | Expiry      |
|------------|----------------------------------------------------------------------|---------------|-------------|
| User       | CV Builder, Job Search, Gap Engine, Export, Recovery                | 10 (default)  | 30-day lock |
| Supervisor | + User Management, Approvals                                        | 50 (default)  | 30-day lock |
| Admin      | + Admin Console (Adzuna key update, system reset, full user view)  | UNLIMITED     | PERPETUAL   |

Passwords are stored as **SHA-512 hashes** (via `hashlib.sha512`). Default credentials are initialised in `_init_user_db()`.

### Key Sections (Career_Architect_Web.py)

| Section | Description |
|---------|-------------|
| 1 — Constants | Version string, file names, gap threshold (91 days) |
| 2 — Core Helpers | Hashing, config I/O, Adzuna credentials, CVP ZIP builder/verifier |
| 3 — Gap Engine | Employment gap detection (`detect_employment_gaps`), empathy templates, gap card renderer |
| 4 — Session State Init | `_init_user_db`, `_init_cv_state`, `_init_misc_state` |
| 5 — Page Config & CSS | Neon-green-on-black branding (Courier New, `#39ff14` on `#000000`) |
| 6 — Auth Gate | Login screen with `st.stop()` guard |
| 7 — Sidebar | User info, credits/expiry display, logout |
| 8 — Tab Renderers | CV Builder (5-step wizard), Job Search, Gap Engine, Export, Recovery, User Management, Approvals, Admin Console |
| 9 — Tab Routing | `ROLE_TABS` dict maps role → labels + renderer functions |
| 10 — Footer | Fixed neon footer bar |

### CV Data Shape

```python
cv_data = {
    "full_name": str,
    "mobile": str,
    "email": str,
    "profile": str,
    "skills": [str, ...],
    "experience": [
        {
            "company": str,
            "title": str,
            "start_date": str,   # MM/YYYY or flexible
            "end_date": str,     # MM/YYYY | "Present"
            "responsibilities": [str, ...],
            "achievements": [str, ...]
        }, ...
    ],
    "education": {
        "institution": str,
        "degree": str,
        "start_date": str,
        "end_date": str,
        "grade": str
    }
}
```

### Export Format (.cvp)

CV data is serialised to JSON, then packaged into a ZIP alongside a `integrity.sha512` file (raw SHA-512 hash of the `.cvp` bytes). The `verify_and_extract_cvp` function validates integrity on import.

### Job Search (Adzuna API)

- Endpoint: `https://api.adzuna.com/v1/api/jobs/{country}/search/1`
- Credentials stored in `system_config.json` under `admin_settings.api_keys`
- Country: `gb` (UK national) or `us` (international), toggled in UI
- Each search deducts one credit from the logged-in user

### Employment Gap Engine

- Threshold: 91 days (`GAP_THRESHOLD_DAYS`)
- Date parsing supports: `MM/YYYY`, `YYYY-MM`, `Month YYYY`, `Present`, `Current`, year-only
- Gap categories: Career Development, Health & Wellbeing, Family & Care, Bereavement, Other
- Each category has an "Aash empathy message" and a LinkedIn narrative template

---

## Configuration Files

### system_config.json

```json
{
  "admin_settings": {
    "admin_hash": "<sha512 of admin password>",
    "branding": { ... },
    "api_keys": {
      "adzuna_id": "<app_id>",
      "adzuna_key": "<app_key>"
    }
  },
  "system_info": {
    "version": "FINAL MASTER STATUS",
    "build_date": "...",
    "manifest_compliance": "V13.0",
    "copyright": "Copyright © 2026 Pose Perfect Ltd"
  }
}
```

> **Warning:** `system_config.json` contains live API keys. Do not commit real credentials to version control.

### user_registry.json

Stores persistent user data. The in-session `user_db` is initialised from session state, not from this file directly at startup.

---

## Styling

The app uses a custom CSS block injected via `st.markdown(..., unsafe_allow_html=True)`:

- **Background:** `#000000`
- **Sidebar background:** `#0a0a0a`
- **Accent / neon:** `#39ff14`
- **Font:** `Courier New, monospace` (bold throughout)
- **Buttons:** Neon green fill → inverts on hover

---

## Dependencies

```
streamlit
requests
```

> `datetime` is a Python standard library module and does not need to be in `requirements.txt`.

---

## Branch & Development Notes

- Primary development branch: `claude/update-claude-md-n3SK5`
- Main production branch: `main`
- The `Career_Architect_User.py` Tkinter app is a legacy prototype and is not actively maintained.
- `architect_core.py` references an `ArchitectCore` class that is not present in the current repository — this file is not used by the main web application.
