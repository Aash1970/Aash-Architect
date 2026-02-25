# Career Architect Pro — CV SaaS Platform

**Version:** 1.0.0 | **Copyright:** © 2026 Pose Perfect Ltd | **Architecture:** Modular, Portable, Testable

---

## Architecture Overview

This platform is built to be **production-grade, modular, and portable**. Streamlit is used as a temporary UI layer. All business logic is implemented as pure Python services that are fully independent of any UI framework. Migration to FastAPI + React requires no changes to the service layer.

```
/app
├── /models          — Pure Python data models (CVModel, UserModel)
├── /roles           — Permission matrix, role hierarchy
├── /tier            — Tier rules and feature gating
├── /validation      — All validation logic (server-side)
├── /i18n            — Internationalisation (en, es, fr, de)
├── /ats             — ATS scoring engine (independent module)
├── /security        — AES-256-GCM encryption + package builder
├── /lifecycle       — CV versioning + retention policies
├── /services        — Business service layer (data, auth, cv, role, tier)
├── /admin           — Admin and SystemAdmin operations
├── /ui              — Streamlit UI (ONLY layer with Streamlit imports)
│   └── /pages       — Individual page components
└── /tests           — Full test suite (6 mandatory files)

/seed_data           — Development/test seed data + loader
requirements.txt
README.md
```

---

## Architecture Rules (Strict Enforcement)

| Rule | Enforcement |
|------|-------------|
| No business logic in UI | `app/ui/` only calls service functions |
| No Streamlit outside `/ui` | Verified by test_package_integrity.py AST check |
| No DB calls outside DataService | All access via `app/services/data_service.py` |
| All permissions checked centrally | `app/roles/permission_matrix.py` + `RoleService` |
| All tier limits enforced in service layer | `TierService.assert_*()` methods |
| All validation server-side | `app/validation/validators.py` |
| No hardcoded display strings in UI | `app/i18n/__init__.py` `t()` function |

---

## Role System

| Role | Capabilities |
|------|-------------|
| **User** | Create/edit own CVs, export, submit to coach (Premium only) |
| **Coach** | View assigned users' CVs, add notes |
| **Admin** | User management, metrics, coach management, reports |
| **SystemAdmin** | All Admin + retention override, hard delete, language control, tier management |

Permission matrix defined in: `app/roles/permission_matrix.py`

---

## Tier System

| Feature | Free | Premium | Enterprise |
|---------|------|---------|------------|
| Max CVs | 2 | Unlimited | Unlimited |
| ATS Basic | ✗ | ✓ | ✓ |
| ATS Advanced | ✗ | ✓ | ✓ |
| ATS Analytics | ✗ | ✗ | ✓ |
| Coach Submission | ✗ | ✓ | ✓ |
| Monthly Exports | 3 | Unlimited | Unlimited |
| Export Formats | PDF | PDF, DOCX, JSON | PDF, DOCX, JSON, XML |
| Version History | 7 days | 90 days | 365 days |

Tier rules defined in: `app/tier/tier_rules.py`

---

## Internationalisation

Phase 1 languages supported: **English (en), Spanish (es), French (fr), German (de)**

All display strings loaded via `app/i18n/__init__.py:t(key, lang_code)`.
No hardcoded strings in UI. Services return semantic keys, not translated text.
Language switch is runtime-dynamic.

---

## ATS Scoring Engine

Located: `app/ats/scoring_engine.py`

- **Independent module** — no Streamlit, no UI dependencies
- Accepts: CV dict + job description text
- Outputs: `ATSScore` object with:
  - `overall_score` (0–100)
  - `keyword_match_rate` (%)
  - `completeness_score` (%)
  - `format_score` (%)
  - `matched_keywords` / `missing_keywords`
  - `recommendations` (sorted by impact)
  - `advanced_analytics` (Enterprise tier only)

---

## Security

Located: `app/security/`

- **AES-256-GCM** encryption via `cryptography` library
- Every export package contains:
  - `manifest.json` — version, created_at, checksum (SHA-256), user_id, tier
  - `cv_data.enc` — AES-256-GCM encrypted CV JSON
  - `key.b64` — base64 package key (production: replace with HSM/KMS)
- UI **never** calls encryption directly
- `PackageBuilder` enforces minimum package size (>1KB)
- Empty/invalid CVs are blocked from export with validation error

---

## Running the Application

### Prerequisites

```bash
pip install -r requirements.txt
```

### Local Mode (No Supabase Required)

The platform auto-detects Supabase environment variables. Without them, it runs with a local in-memory store — ideal for development and testing.

```bash
# Run the Streamlit app
streamlit run app/ui/app.py

# Or use the main entry point
python -m streamlit run app/ui/app.py
```

### With Supabase

```bash
export SUPABASE_URL="https://your-project.supabase.co"
export SUPABASE_KEY="your-anon-key"
streamlit run app/ui/app.py
```

---

## Loading Seed Data

```bash
python seed_data/seed_loader.py
```

**Seed accounts:**

| Role | Email | Password |
|------|-------|----------|
| User (Free) | alice.free@example.com | FreeUser@123! |
| User (Premium) | bob.premium@example.com | PremiumUser@123! |
| User (Enterprise) | carol.enterprise@example.com | EnterpriseUser@123! |
| Coach | diana.coach@example.com | CoachDiana@123! |
| Admin | evan.admin@example.com | AdminEvan@123! |
| SystemAdmin | fiona.sysadmin@example.com | SysAdmin@Fiona123! |

---

## Running Tests

```bash
# All tests
pytest app/tests/ -v

# With coverage report
pytest app/tests/ -v --cov=app --cov-report=term-missing

# Individual test files
pytest app/tests/test_validation.py -v
pytest app/tests/test_roles.py -v
pytest app/tests/test_tier.py -v
pytest app/tests/test_encryption.py -v
pytest app/tests/test_ats.py -v
pytest app/tests/test_package_integrity.py -v
```

**Tests must pass before deployment.**

---

## Regression Checklist

Before every release, verify:

- [ ] No business logic in UI (`app/ui/`)
- [ ] No Streamlit import outside `/ui` (enforced by `test_package_integrity.py`)
- [ ] All roles enforced via `RoleService.require_permission()`
- [ ] All tiers enforced via `TierService.assert_*()` methods
- [ ] Validation blocks empty/1-char saves
- [ ] `st.date_input` used for all date fields
- [ ] Email format validated server-side
- [ ] Mobile numeric validation enforced server-side
- [ ] All 4 languages loading correctly
- [ ] ATS module imports cleanly without Streamlit
- [ ] Encryption module imports cleanly without Streamlit
- [ ] All 6 test files pass

---

## Migration Path

When migrating from Streamlit to FastAPI + React:

1. Delete `app/ui/` entirely
2. Create `app/api/` with FastAPI routers
3. Wire routers to the **existing service layer** — zero service changes required
4. Services are pure Python functions, fully portable

---

## Portability Guarantee

```python
# Works independently of ANY UI framework:
from app.services.cv_service import CVService
from app.services.data_service import DataService
from app.services.role_service import RoleService
from app.services.tier_service import TierService
from app.lifecycle.versioning import VersioningService
from app.security.package_builder import PackageBuilder

ds = DataService()
cv_svc = CVService(ds, RoleService(), TierService(ds), VersioningService(), PackageBuilder())

# Create a CV — no Streamlit required
cv = cv_svc.create_cv(cv_data, requester_id="u1", requester_role="User", requester_tier="Premium")
```
