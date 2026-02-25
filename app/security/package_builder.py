"""
CV Package Builder — Production Grade
Builds encrypted, verifiable CV export packages.
UI MUST NOT call encryption directly — only this builder.

Package format (ZIP archive containing):
  manifest.json    — metadata + checksum
  cv_data.enc      — AES-256-GCM encrypted CV JSON
  key.b64          — Base64-encoded package key (for demo; production would use HSM/KMS)

Manifest fields (mandatory per architecture spec):
  version
  created_at
  checksum
  user_id
  tier
"""

import io
import json
import base64
import zipfile
import secrets
from datetime import datetime, timezone
from dataclasses import dataclass
from typing import Dict, Any, Optional

from app.security.encryption import (
    EncryptionService, generate_checksum, verify_checksum
)


class PackageError(Exception):
    """Raised when package creation or verification fails."""


@dataclass
class CVPackage:
    """
    Represents a built CV export package.

    Attributes:
        archive_bytes:  Raw bytes of the ZIP archive
        manifest:       The package manifest dict
        package_key:    The AES-256 key used for encryption (bytes)
    """
    archive_bytes: bytes
    manifest: Dict[str, Any]
    package_key: bytes

    @property
    def checksum(self) -> str:
        return self.manifest.get("checksum", "")

    @property
    def user_id(self) -> str:
        return self.manifest.get("user_id", "")

    @property
    def tier(self) -> str:
        return self.manifest.get("tier", "")


class PackageBuilder:
    """
    Builds and verifies encrypted CV export packages.

    Usage:
        builder = PackageBuilder()
        pkg = builder.build(cv_dict, user_id="u123", tier="Premium")
        zip_bytes = pkg.archive_bytes  # write to file or send to browser
    """

    PACKAGE_VERSION = "1.0.0"

    def __init__(self):
        self._enc = EncryptionService()

    def build(
        self,
        cv_dict: Dict[str, Any],
        user_id: str,
        tier: str,
        app_version: str = "1.0.0",
    ) -> CVPackage:
        """
        Builds an encrypted CV package.

        Args:
            cv_dict:     CV data as dictionary
            user_id:     Owner's user ID (included in manifest)
            tier:        User's tier (included in manifest)
            app_version: Application version string

        Returns:
            CVPackage with archive bytes and manifest

        Raises:
            PackageError if CV data is invalid or too small
        """
        # Validate CV has meaningful content
        cv_json = json.dumps(cv_dict, ensure_ascii=False)
        if len(cv_json) < 50:
            raise PackageError(
                "CV content is insufficient for export. "
                "Please complete your CV before exporting."
            )

        # Generate a fresh AES-256 key for this package
        package_key = self._enc.generate_key()

        # Encrypt CV data
        cv_bytes = cv_json.encode("utf-8")
        encrypted_cv = self._enc.encrypt(cv_bytes, package_key)

        # Generate checksum of original (plaintext) CV bytes
        cv_checksum = generate_checksum(cv_bytes)

        # Build manifest
        now_utc = datetime.now(timezone.utc).isoformat()
        manifest: Dict[str, Any] = {
            "version": self.PACKAGE_VERSION,
            "app_version": app_version,
            "created_at": now_utc,
            "checksum": cv_checksum,
            "user_id": user_id,
            "tier": tier,
            "encryption": "AES-256-GCM",
            "contents": ["manifest.json", "cv_data.enc", "key.b64"],
        }

        # Encode package key as Base64 for storage in package
        # (In production: key would be wrapped by HSM/KMS or user password)
        key_b64 = base64.b64encode(package_key).decode("ascii")

        # Build ZIP archive
        archive_bytes = self._build_zip(manifest, encrypted_cv, key_b64)

        # Validate output is substantial
        if len(archive_bytes) < 1024:
            raise PackageError(
                "Generated package is too small — possible data integrity issue."
            )

        return CVPackage(
            archive_bytes=archive_bytes,
            manifest=manifest,
            package_key=package_key,
        )

    def verify(self, archive_bytes: bytes) -> Dict[str, Any]:
        """
        Verifies the integrity of a CV package.

        Reads the manifest and verifies:
          - All required manifest fields are present
          - The encrypted CV can be decrypted with the embedded key
          - The decrypted CV checksum matches manifest checksum

        Args:
            archive_bytes: Raw bytes of the ZIP package

        Returns:
            Dict with keys: valid (bool), manifest (dict), errors (list)
        """
        result: Dict[str, Any] = {
            "valid": False,
            "manifest": {},
            "errors": [],
        }

        try:
            with zipfile.ZipFile(io.BytesIO(archive_bytes), "r") as zf:
                # Check all required files present
                names = zf.namelist()
                required = ["manifest.json", "cv_data.enc", "key.b64"]
                missing_files = [f for f in required if f not in names]
                if missing_files:
                    result["errors"].append(
                        f"Package missing files: {missing_files}"
                    )
                    return result

                # Load manifest
                manifest_bytes = zf.read("manifest.json")
                manifest = json.loads(manifest_bytes.decode("utf-8"))
                result["manifest"] = manifest

                # Check required manifest fields
                required_fields = [
                    "version", "created_at", "checksum", "user_id", "tier"
                ]
                missing_fields = [
                    f for f in required_fields if f not in manifest
                ]
                if missing_fields:
                    result["errors"].append(
                        f"Manifest missing fields: {missing_fields}"
                    )
                    return result

                # Load and decode key
                key_b64_bytes = zf.read("key.b64")
                package_key = base64.b64decode(key_b64_bytes.decode("ascii"))

                # Decrypt CV data
                encrypted_cv = zf.read("cv_data.enc")
                cv_bytes = self._enc.decrypt(encrypted_cv, package_key)

                # Verify checksum
                if not verify_checksum(cv_bytes, manifest["checksum"]):
                    result["errors"].append(
                        "Checksum mismatch — package may be corrupted."
                    )
                    return result

        except zipfile.BadZipFile:
            result["errors"].append("Archive is not a valid ZIP file.")
            return result
        except Exception as exc:
            result["errors"].append(f"Verification failed: {exc}")
            return result

        result["valid"] = True
        return result

    def extract_cv(self, archive_bytes: bytes) -> Dict[str, Any]:
        """
        Extracts and decrypts CV data from a package.

        Args:
            archive_bytes: Raw ZIP package bytes

        Returns:
            Decrypted CV dictionary

        Raises:
            PackageError on any failure
        """
        verification = self.verify(archive_bytes)
        if not verification["valid"]:
            errors = "; ".join(verification["errors"])
            raise PackageError(f"Package integrity check failed: {errors}")

        with zipfile.ZipFile(io.BytesIO(archive_bytes), "r") as zf:
            key_b64_bytes = zf.read("key.b64")
            package_key = base64.b64decode(key_b64_bytes.decode("ascii"))
            encrypted_cv = zf.read("cv_data.enc")
            cv_bytes = self._enc.decrypt(encrypted_cv, package_key)
            return json.loads(cv_bytes.decode("utf-8"))

    def _build_zip(
        self,
        manifest: Dict[str, Any],
        encrypted_cv: bytes,
        key_b64: str,
    ) -> bytes:
        """Builds the ZIP archive containing all package files."""
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
            # manifest.json
            manifest_bytes = json.dumps(
                manifest, indent=2, ensure_ascii=False
            ).encode("utf-8")
            zf.writestr("manifest.json", manifest_bytes)

            # cv_data.enc — binary encrypted data
            zf.writestr("cv_data.enc", encrypted_cv)

            # key.b64 — base64-encoded package key
            zf.writestr("key.b64", key_b64.encode("ascii"))

        return buffer.getvalue()


# ── Module-level convenience functions ───────────────────────────────────────

_builder = PackageBuilder()


def build_cv_package(
    cv_dict: Dict[str, Any],
    user_id: str,
    tier: str,
) -> CVPackage:
    """Convenience wrapper. Builds and returns a CVPackage."""
    return _builder.build(cv_dict, user_id=user_id, tier=tier)


def verify_package_integrity(archive_bytes: bytes) -> Dict[str, Any]:
    """Convenience wrapper. Verifies a package and returns result dict."""
    return _builder.verify(archive_bytes)
