"""
Encryption Service — Production Grade
AES-256 encryption for all exported packages.
UI MUST NOT perform encryption directly.
All encryption operations go through this module.

Implementation:
  - Uses cryptography library (Fernet wraps AES-128-CBC; for true AES-256
    we use AES-GCM via cryptography.hazmat primitives)
  - AES-256-GCM with random IV per encryption
  - SHA-256 checksums for integrity verification
"""

import os
import json
import base64
import hashlib
import secrets
from typing import Tuple, Optional

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend


# AES-256 key size in bytes
_KEY_SIZE_BYTES = 32  # 256 bits
# GCM nonce size
_NONCE_SIZE = 12  # 96 bits (recommended for GCM)
# PBKDF2 iterations
_PBKDF2_ITERATIONS = 260_000
# Salt size for key derivation
_SALT_SIZE = 32  # 256 bits


class EncryptionError(Exception):
    """Raised when encryption or decryption fails."""


class EncryptionService:
    """
    AES-256-GCM encryption service.

    Provides:
      - Key generation and management
      - encrypt/decrypt with authenticated encryption
      - Checksum generation and verification
    """

    def generate_key(self) -> bytes:
        """
        Generates a cryptographically random 256-bit AES key.
        Returns raw bytes — caller is responsible for secure storage.
        """
        return secrets.token_bytes(_KEY_SIZE_BYTES)

    def derive_key_from_password(self, password: str, salt: bytes) -> bytes:
        """
        Derives a 256-bit key from a password using PBKDF2-HMAC-SHA256.

        Args:
            password: User-provided password string
            salt:     Random salt (use generate_salt() to create)

        Returns:
            32-byte AES-256 key
        """
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=_KEY_SIZE_BYTES,
            salt=salt,
            iterations=_PBKDF2_ITERATIONS,
            backend=default_backend(),
        )
        return kdf.derive(password.encode("utf-8"))

    def generate_salt(self) -> bytes:
        """Generates a random salt for key derivation."""
        return secrets.token_bytes(_SALT_SIZE)

    def encrypt(self, plaintext: bytes, key: bytes) -> bytes:
        """
        Encrypts plaintext using AES-256-GCM.
        Returns: salt(32) + nonce(12) + ciphertext+tag

        Args:
            plaintext: Raw bytes to encrypt
            key:       32-byte AES key

        Returns:
            Encrypted bytes (nonce prepended, tag appended by GCM)
        """
        if len(key) != _KEY_SIZE_BYTES:
            raise EncryptionError(
                f"Key must be {_KEY_SIZE_BYTES} bytes; got {len(key)}."
            )
        nonce = secrets.token_bytes(_NONCE_SIZE)
        aesgcm = AESGCM(key)
        ciphertext = aesgcm.encrypt(nonce, plaintext, None)
        # Format: nonce | ciphertext+tag
        return nonce + ciphertext

    def decrypt(self, encrypted: bytes, key: bytes) -> bytes:
        """
        Decrypts AES-256-GCM encrypted data.

        Args:
            encrypted: Bytes from encrypt() (nonce prepended)
            key:       32-byte AES key

        Returns:
            Decrypted plaintext bytes

        Raises:
            EncryptionError on authentication failure or bad key
        """
        if len(key) != _KEY_SIZE_BYTES:
            raise EncryptionError(
                f"Key must be {_KEY_SIZE_BYTES} bytes; got {len(key)}."
            )
        if len(encrypted) < _NONCE_SIZE + 16:
            raise EncryptionError("Encrypted data is too short to be valid.")

        nonce = encrypted[:_NONCE_SIZE]
        ciphertext = encrypted[_NONCE_SIZE:]

        aesgcm = AESGCM(key)
        try:
            return aesgcm.decrypt(nonce, ciphertext, None)
        except Exception as exc:
            raise EncryptionError(
                "Decryption failed — data may be corrupted or key is wrong."
            ) from exc

    def encrypt_text(self, text: str, key: bytes) -> str:
        """
        Encrypts a UTF-8 string and returns base64-encoded ciphertext.
        Convenient for storing encrypted strings in databases.
        """
        cipher = self.encrypt(text.encode("utf-8"), key)
        return base64.b64encode(cipher).decode("ascii")

    def decrypt_text(self, b64_ciphertext: str, key: bytes) -> str:
        """
        Decrypts a base64-encoded ciphertext string back to UTF-8 text.
        """
        encrypted = base64.b64decode(b64_ciphertext.encode("ascii"))
        return self.decrypt(encrypted, key).decode("utf-8")

    def encrypt_json(self, data: dict, key: bytes) -> bytes:
        """Serialises dict to JSON and encrypts."""
        json_bytes = json.dumps(data, ensure_ascii=False).encode("utf-8")
        return self.encrypt(json_bytes, key)

    def decrypt_json(self, encrypted: bytes, key: bytes) -> dict:
        """Decrypts and deserialises JSON to dict."""
        json_bytes = self.decrypt(encrypted, key)
        return json.loads(json_bytes.decode("utf-8"))


def generate_checksum(data: bytes) -> str:
    """
    Generates a SHA-256 checksum hex digest of the given bytes.
    Used in package manifests for integrity verification.
    """
    return hashlib.sha256(data).hexdigest()


def verify_checksum(data: bytes, expected_checksum: str) -> bool:
    """
    Verifies that data matches the expected SHA-256 checksum.

    Returns:
        True if checksums match, False otherwise
    """
    actual = generate_checksum(data)
    return secrets.compare_digest(actual, expected_checksum)


# ── Module-level convenience functions ───────────────────────────────────────

_service = EncryptionService()


def encrypt_data(plaintext: bytes, key: bytes) -> bytes:
    """Module-level convenience: encrypts bytes with AES-256-GCM."""
    return _service.encrypt(plaintext, key)


def decrypt_data(encrypted: bytes, key: bytes) -> bytes:
    """Module-level convenience: decrypts AES-256-GCM bytes."""
    return _service.decrypt(encrypted, key)
