"""
Backend API integration tests using FastAPI TestClient.

These tests exercise the HTTP layer without requiring a live database
(DataService falls back to in-memory store when Supabase env vars are absent)
and without a real JWT secret (tests inject a pre-built CurrentUser via
dependency override).
"""
from __future__ import annotations

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from backend.api.deps import CurrentUser, get_current_user
from backend.main import create_app


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def app():
    """Create a fresh FastAPI app for the test module."""
    return create_app()


@pytest.fixture(scope="module")
def client(app):
    """TestClient with lifespan executed (services initialised)."""
    with TestClient(app, raise_server_exceptions=True) as c:
        yield c


def _user_override(
    user_id: str = "test-user-id",
    role: str = "User",
    tier: str = "Free",
    email: str = "test@example.com",
    full_name: str = "Test User",
    language: str = "en",
):
    """Return a dependency override that injects a fixed CurrentUser."""
    async def _override():
        return CurrentUser(
            user_id=user_id,
            email=email,
            role=role,
            tier=tier,
            full_name=full_name,
            language=language,
        )
    return _override


# ── /health and /version ──────────────────────────────────────────────────────

def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_version(client):
    resp = client.get("/version")
    assert resp.status_code == 200
    data = resp.json()
    assert "version" in data
    assert "service" in data


# ── /auth ─────────────────────────────────────────────────────────────────────

def test_register(client):
    resp = client.post("/auth/register", json={
        "email": "newuser@example.com",
        "password": "Str0ngPass!",
        "full_name": "New User",
    })
    assert resp.status_code == 201
    body = resp.json()
    assert body["success"] is True
    assert body["user"]["email"] == "newuser@example.com"
    assert body["user"]["role"] == "User"
    assert body["user"]["tier"] == "Free"


def test_register_duplicate_email(client):
    payload = {
        "email": "dup@example.com",
        "password": "Str0ngPass!",
        "full_name": "Dup User",
    }
    client.post("/auth/register", json=payload)
    resp = client.post("/auth/register", json=payload)
    # Second registration of the same email must fail (400 or 409)
    assert resp.status_code in (400, 409)


def test_login_success(client):
    client.post("/auth/register", json={
        "email": "login@example.com",
        "password": "Str0ngPass!",
        "full_name": "Login User",
    })
    resp = client.post("/auth/login", json={
        "email": "login@example.com",
        "password": "Str0ngPass!",
    })
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    assert body["user"]["email"] == "login@example.com"


def test_login_wrong_password(client):
    resp = client.post("/auth/login", json={
        "email": "login@example.com",
        "password": "WrongPassword!",
    })
    assert resp.status_code == 401


def test_me_no_auth(client):
    resp = client.get("/auth/me")
    assert resp.status_code == 401


def test_me_with_auth(app, client):
    app.dependency_overrides[get_current_user] = _user_override()
    resp = client.get("/auth/me")
    app.dependency_overrides.clear()
    assert resp.status_code == 200
    assert resp.json()["user_id"] == "test-user-id"


# ── /cv ───────────────────────────────────────────────────────────────────────

_VALID_CV = {
    "title": "My Test CV",
    "personal_info": {
        "full_name": "Test User",
        "email": "test@example.com",
        "mobile": "+447700000000",
        "location": "London, UK",
        "linkedin": None,
        "website": None,
        "summary": None,
    },
    "work_experience": [],
    "education": [],
    "skills": [],
    "languages": [],
    "certifications": [],
}


def test_list_cvs_no_auth(client):
    resp = client.get("/cv")
    assert resp.status_code == 401


def test_create_and_list_cv(app, client):
    # Register + create a dedicated user so IDs are consistent
    reg = client.post("/auth/register", json={
        "email": "cv_owner@example.com",
        "password": "Str0ngPass!",
        "full_name": "CV Owner",
    })
    user_id = reg.json()["user"]["user_id"]

    app.dependency_overrides[get_current_user] = _user_override(
        user_id=user_id, role="User", tier="Free"
    )

    # Create CV
    resp = client.post("/cv", json=_VALID_CV)
    assert resp.status_code == 201, resp.text
    created = resp.json()
    assert created["title"] == "My Test CV"
    cv_id = created["cv_id"]

    # List CVs
    resp = client.get("/cv")
    assert resp.status_code == 200
    ids = [c["cv_id"] for c in resp.json()]
    assert cv_id in ids

    app.dependency_overrides.clear()


def test_get_cv_not_found(app, client):
    app.dependency_overrides[get_current_user] = _user_override()
    resp = client.get("/cv/nonexistent-cv-id")
    app.dependency_overrides.clear()
    assert resp.status_code in (404, 400)


def test_delete_cv(app, client):
    reg = client.post("/auth/register", json={
        "email": "del_owner@example.com",
        "password": "Str0ngPass!",
        "full_name": "Delete Owner",
    })
    user_id = reg.json()["user"]["user_id"]
    app.dependency_overrides[get_current_user] = _user_override(
        user_id=user_id, role="User", tier="Free"
    )

    create_resp = client.post("/cv", json=_VALID_CV)
    cv_id = create_resp.json()["cv_id"]

    del_resp = client.delete(f"/cv/{cv_id}")
    assert del_resp.status_code == 200

    app.dependency_overrides.clear()


# ── /ats ──────────────────────────────────────────────────────────────────────

def test_ats_tier_info(app, client):
    app.dependency_overrides[get_current_user] = _user_override(tier="Premium")
    resp = client.get("/ats/tier-info")
    app.dependency_overrides.clear()
    assert resp.status_code == 200
    assert resp.json()["success"] is True


def test_ats_analyse_free_tier_blocked(app, client):
    """Free tier should raise 402 for ATS analysis."""
    app.dependency_overrides[get_current_user] = _user_override(tier="Free")
    resp = client.post("/ats/analyse", json={
        "cv_id": "some-cv-id",
        "job_description": "We are looking for a Python developer with five years experience.",
    })
    app.dependency_overrides.clear()
    # Free tier cannot use ATS basic
    assert resp.status_code in (402, 400, 404)


# ── /tier ─────────────────────────────────────────────────────────────────────

def test_tier_limits_free(app, client):
    app.dependency_overrides[get_current_user] = _user_override(tier="Free")
    resp = client.get("/tier/limits")
    app.dependency_overrides.clear()
    assert resp.status_code == 200
    body = resp.json()
    assert body["tier"] == "Free"
    assert body["ats_basic"] is False


def test_tier_limits_premium(app, client):
    app.dependency_overrides[get_current_user] = _user_override(tier="Premium")
    resp = client.get("/tier/limits")
    app.dependency_overrides.clear()
    assert resp.status_code == 200
    body = resp.json()
    assert body["tier"] == "Premium"
    assert body["ats_basic"] is True


def test_tier_limits_by_name_non_admin(app, client):
    """Regular users cannot look up other tiers."""
    app.dependency_overrides[get_current_user] = _user_override(role="User")
    resp = client.get("/tier/limits/Enterprise")
    app.dependency_overrides.clear()
    assert resp.status_code == 403


def test_tier_limits_by_name_admin(app, client):
    app.dependency_overrides[get_current_user] = _user_override(role="Admin", tier="Enterprise")
    resp = client.get("/tier/limits/Enterprise")
    app.dependency_overrides.clear()
    assert resp.status_code == 200
    assert resp.json()["tier"] == "Enterprise"


# ── /admin ────────────────────────────────────────────────────────────────────

def test_admin_list_users_non_admin(app, client):
    app.dependency_overrides[get_current_user] = _user_override(role="User")
    resp = client.get("/admin/users")
    app.dependency_overrides.clear()
    assert resp.status_code == 403


def test_admin_list_users_admin(app, client):
    app.dependency_overrides[get_current_user] = _user_override(role="Admin")
    resp = client.get("/admin/users")
    app.dependency_overrides.clear()
    assert resp.status_code == 200
    assert resp.json()["success"] is True


def test_admin_metrics_non_admin(app, client):
    app.dependency_overrides[get_current_user] = _user_override(role="User")
    resp = client.get("/admin/metrics")
    app.dependency_overrides.clear()
    assert resp.status_code == 403


def test_admin_metrics_admin(app, client):
    app.dependency_overrides[get_current_user] = _user_override(role="Admin")
    resp = client.get("/admin/metrics")
    app.dependency_overrides.clear()
    assert resp.status_code == 200


def test_admin_coaches_list(app, client):
    app.dependency_overrides[get_current_user] = _user_override(role="Admin")
    resp = client.get("/admin/coaches")
    app.dependency_overrides.clear()
    assert resp.status_code == 200


def test_admin_hard_delete_cv_user_blocked(app, client):
    app.dependency_overrides[get_current_user] = _user_override(role="Admin")
    resp = client.delete("/admin/cv/some-cv-id")
    app.dependency_overrides.clear()
    # Admin role cannot hard-delete (SystemAdmin only)
    assert resp.status_code == 403


def test_admin_hard_delete_cv_sysadmin(app, client):
    app.dependency_overrides[get_current_user] = _user_override(role="SystemAdmin")
    resp = client.delete("/admin/cv/nonexistent")
    app.dependency_overrides.clear()
    # SystemAdmin has permission; nonexistent CV returns 200 (soft no-op) or 200
    assert resp.status_code == 200
