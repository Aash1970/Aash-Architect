"""
Test Suite: Encryption System
Covers app/security/encryption.py
"""

import pytest
import os
import secrets
from app.security.encryption import (
    EncryptionService, EncryptionError,
    encrypt_data, decrypt_data, generate_checksum, verify_checksum
)


class TestEncryptionService:
    def setup_method(self):
        self.svc = EncryptionService()
        self.key = self.svc.generate_key()

    def test_generate_key_length(self):
        key = self.svc.generate_key()
        assert len(key) == 32  # 256 bits

    def test_generate_key_is_random(self):
        key1 = self.svc.generate_key()
        key2 = self.svc.generate_key()
        assert key1 != key2

    def test_encrypt_returns_bytes(self):
        result = self.svc.encrypt(b"hello world", self.key)
        assert isinstance(result, bytes)

    def test_encrypted_different_from_plaintext(self):
        plaintext = b"secret data"
        result = self.svc.encrypt(plaintext, self.key)
        assert result != plaintext

    def test_encrypt_decrypt_roundtrip(self):
        plaintext = b"Hello, World! This is test data."
        encrypted = self.svc.encrypt(plaintext, self.key)
        decrypted = self.svc.decrypt(encrypted, self.key)
        assert decrypted == plaintext

    def test_encrypt_decrypt_unicode(self):
        plaintext = "Hello Wörld 你好 мир".encode("utf-8")
        encrypted = self.svc.encrypt(plaintext, self.key)
        decrypted = self.svc.decrypt(encrypted, self.key)
        assert decrypted == plaintext

    def test_decrypt_with_wrong_key_raises(self):
        plaintext = b"secret"
        encrypted = self.svc.encrypt(plaintext, self.key)
        wrong_key = self.svc.generate_key()
        with pytest.raises(EncryptionError):
            self.svc.decrypt(encrypted, wrong_key)

    def test_decrypt_corrupted_data_raises(self):
        plaintext = b"data"
        encrypted = self.svc.encrypt(plaintext, self.key)
        # Corrupt the last byte
        corrupted = encrypted[:-1] + bytes([encrypted[-1] ^ 0xFF])
        with pytest.raises(EncryptionError):
            self.svc.decrypt(corrupted, self.key)

    def test_wrong_key_size_raises(self):
        with pytest.raises(EncryptionError):
            self.svc.encrypt(b"data", b"short_key")

    def test_encrypt_text_roundtrip(self):
        text = "Production-grade CV SaaS platform."
        b64 = self.svc.encrypt_text(text, self.key)
        result = self.svc.decrypt_text(b64, self.key)
        assert result == text

    def test_encrypt_json_roundtrip(self):
        data = {
            "user_id": "u123",
            "tier": "Premium",
            "name": "Jane Döe",
            "skills": ["Python", "FastAPI"],
        }
        encrypted = self.svc.encrypt_json(data, self.key)
        decrypted = self.svc.decrypt_json(encrypted, self.key)
        assert decrypted == data

    def test_each_encryption_produces_different_ciphertext(self):
        """AES-GCM uses random nonce — same plaintext must produce different ciphertext."""
        plaintext = b"same data"
        enc1 = self.svc.encrypt(plaintext, self.key)
        enc2 = self.svc.encrypt(plaintext, self.key)
        assert enc1 != enc2  # Different nonces

    def test_key_derivation(self):
        salt = self.svc.generate_salt()
        key = self.svc.derive_key_from_password("password123", salt)
        assert len(key) == 32

    def test_key_derivation_deterministic(self):
        salt = self.svc.generate_salt()
        key1 = self.svc.derive_key_from_password("password", salt)
        key2 = self.svc.derive_key_from_password("password", salt)
        assert key1 == key2

    def test_key_derivation_different_passwords(self):
        salt = self.svc.generate_salt()
        key1 = self.svc.derive_key_from_password("password1", salt)
        key2 = self.svc.derive_key_from_password("password2", salt)
        assert key1 != key2

    def test_key_derivation_different_salts(self):
        salt1 = self.svc.generate_salt()
        salt2 = self.svc.generate_salt()
        key1 = self.svc.derive_key_from_password("password", salt1)
        key2 = self.svc.derive_key_from_password("password", salt2)
        assert key1 != key2


class TestGenerateChecksum:
    def test_returns_string(self):
        result = generate_checksum(b"data")
        assert isinstance(result, str)

    def test_hex_digest_length(self):
        # SHA-256 → 64 hex chars
        result = generate_checksum(b"data")
        assert len(result) == 64

    def test_same_data_same_checksum(self):
        data = b"consistent data"
        assert generate_checksum(data) == generate_checksum(data)

    def test_different_data_different_checksum(self):
        assert generate_checksum(b"data1") != generate_checksum(b"data2")

    def test_empty_bytes_has_checksum(self):
        result = generate_checksum(b"")
        assert len(result) == 64

    def test_verify_checksum_true(self):
        data = b"test data"
        checksum = generate_checksum(data)
        assert verify_checksum(data, checksum) is True

    def test_verify_checksum_false_on_mismatch(self):
        data = b"test data"
        assert verify_checksum(data, "wrongchecksum" * 5) is False

    def test_verify_checksum_false_on_tampered_data(self):
        data = b"test data"
        checksum = generate_checksum(data)
        tampered = b"test DATA"
        assert verify_checksum(tampered, checksum) is False


class TestModuleLevelFunctions:
    def test_encrypt_decrypt_convenience_functions(self):
        svc = EncryptionService()
        key = svc.generate_key()
        plaintext = b"convenience test"
        encrypted = encrypt_data(plaintext, key)
        decrypted = decrypt_data(encrypted, key)
        assert decrypted == plaintext

    def test_large_data_encryption(self):
        """Test with ~1MB of data to ensure performance is acceptable."""
        svc = EncryptionService()
        key = svc.generate_key()
        large_data = secrets.token_bytes(1024 * 1024)
        encrypted = svc.encrypt(large_data, key)
        decrypted = svc.decrypt(encrypted, key)
        assert decrypted == large_data
