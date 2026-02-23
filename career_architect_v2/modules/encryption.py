from __future__ import annotations
import base64
import hashlib
import io
import json
import zipfile
from datetime import datetime, timezone

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

# In production this must come from environment / secrets manager
_APP_SECRET = b"career_architect_pro_enterprise_2026_kdf_salt"


# ── Key derivation ────────────────────────────────────────────

def _derive_key(user_id: str) -> bytes:
    """
    Deterministically derive a 256-bit Fernet-compatible key from user_id.
    The same user always receives the same key; different users get different keys.
    """
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=user_id.encode("utf-8"),
        iterations=100_000,
    )
    raw = kdf.derive(_APP_SECRET)
    return base64.urlsafe_b64encode(raw)


# ── Core encrypt / decrypt ────────────────────────────────────

def encrypt_data(plaintext: str, user_id: str) -> str:
    """Encrypt a plaintext string for user_id.  Returns a URL-safe string."""
    key = _derive_key(user_id)
    return Fernet(key).encrypt(plaintext.encode("utf-8")).decode("utf-8")


def decrypt_data(ciphertext: str, user_id: str) -> str:
    """Decrypt a ciphertext string for user_id."""
    key = _derive_key(user_id)
    return Fernet(key).decrypt(ciphertext.encode("utf-8")).decode("utf-8")


# ── Integrity ─────────────────────────────────────────────────

def generate_checksum(data: str) -> str:
    """SHA-256 hex digest of a string."""
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


# ── Encrypted export package ──────────────────────────────────

def create_encrypted_zip(cv_data: dict, user_id: str, email: str) -> bytes:
    """
    Build an encrypted .cap (Career Architect Package) ZIP:
      cv_encrypted.cap  — Fernet-encrypted CV JSON
      manifest.json     — metadata + integrity checksum (plaintext)

    The encrypted blob cannot be read without the application key + user_id.
    Returns the raw ZIP bytes suitable for st.download_button.
    """
    cv_json     = json.dumps(cv_data, indent=2, ensure_ascii=False)
    encrypted   = encrypt_data(cv_json, user_id)
    checksum    = generate_checksum(cv_json)

    manifest = {
        "app":       "Career Architect Pro",
        "version":   "v2.0.0",
        "user":      email,
        "checksum":  checksum,
        "encrypted": True,
        "algorithm": "Fernet/AES-128-CBC+HMAC-SHA256 via PBKDF2-HMAC-SHA256",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("cv_encrypted.cap",  encrypted)
        zf.writestr("manifest.json",     json.dumps(manifest, indent=2))
    return buf.getvalue()


def verify_package_checksum(cv_data: dict, checksum: str) -> bool:
    """Verify that cv_data matches a previously stored checksum."""
    return generate_checksum(json.dumps(cv_data, indent=2, ensure_ascii=False)) == checksum
