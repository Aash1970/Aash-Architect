"""
Test Suite: CV Package Integrity
Covers app/security/package_builder.py
Verifies encrypted packages are valid, non-empty, and verifiable.
"""

import pytest
import json
import zipfile
import io
from app.security.package_builder import (
    PackageBuilder, CVPackage, PackageError,
    build_cv_package, verify_package_integrity
)


# ── Fixtures ──────────────────────────────────────────────────────────────────

SAMPLE_CV = {
    "cv_id": "cv-pkg-001",
    "user_id": "user-001",
    "title": "Test CV",
    "tier": "Premium",
    "version": 3,
    "personal_info": {
        "full_name": "Jane Doe",
        "email": "jane@example.com",
        "mobile": "+44 7700 000000",
        "location": "London, UK",
        "linkedin": "https://linkedin.com/in/janedoe",
        "summary": "Experienced software engineer with Python expertise.",
    },
    "work_experience": [
        {
            "company": "TechCorp",
            "position": "Engineer",
            "start_date": "2020-01-01",
            "end_date": "2024-01-01",
            "is_current": False,
            "description": "Developed microservices.",
            "achievements": ["Improved performance by 30%"],
        }
    ],
    "education": [],
    "skills": [{"name": "Python", "level": "Expert"}],
    "languages": [{"name": "English", "proficiency": "Native"}],
    "certifications": [],
}


# ── PackageBuilder.build ──────────────────────────────────────────────────────

class TestPackageBuilderBuild:
    def setup_method(self):
        self.builder = PackageBuilder()

    def test_returns_cv_package(self):
        pkg = self.builder.build(SAMPLE_CV, user_id="u1", tier="Premium")
        assert isinstance(pkg, CVPackage)

    def test_archive_bytes_not_empty(self):
        pkg = self.builder.build(SAMPLE_CV, user_id="u1", tier="Premium")
        assert len(pkg.archive_bytes) > 0

    def test_archive_exceeds_1kb(self):
        """Architecture spec: No <1KB empty zip outputs allowed."""
        pkg = self.builder.build(SAMPLE_CV, user_id="u1", tier="Premium")
        assert len(pkg.archive_bytes) >= 1024

    def test_manifest_has_required_fields(self):
        """Manifest MUST include: version, created_at, checksum, user_id, tier."""
        pkg = self.builder.build(SAMPLE_CV, user_id="u1", tier="Premium")
        manifest = pkg.manifest
        for field in ["version", "created_at", "checksum", "user_id", "tier"]:
            assert field in manifest, f"Manifest missing field: {field}"

    def test_manifest_user_id_correct(self):
        pkg = self.builder.build(SAMPLE_CV, user_id="user-abc", tier="Free")
        assert pkg.manifest["user_id"] == "user-abc"

    def test_manifest_tier_correct(self):
        pkg = self.builder.build(SAMPLE_CV, user_id="u1", tier="Enterprise")
        assert pkg.manifest["tier"] == "Enterprise"

    def test_manifest_checksum_is_sha256(self):
        pkg = self.builder.build(SAMPLE_CV, user_id="u1", tier="Premium")
        checksum = pkg.manifest["checksum"]
        assert len(checksum) == 64  # SHA-256 hex digest

    def test_manifest_encryption_field(self):
        pkg = self.builder.build(SAMPLE_CV, user_id="u1", tier="Premium")
        assert pkg.manifest["encryption"] == "AES-256-GCM"

    def test_package_key_is_32_bytes(self):
        pkg = self.builder.build(SAMPLE_CV, user_id="u1", tier="Premium")
        assert len(pkg.package_key) == 32

    def test_is_valid_zip_archive(self):
        pkg = self.builder.build(SAMPLE_CV, user_id="u1", tier="Premium")
        assert zipfile.is_zipfile(io.BytesIO(pkg.archive_bytes))

    def test_zip_contains_required_files(self):
        pkg = self.builder.build(SAMPLE_CV, user_id="u1", tier="Premium")
        with zipfile.ZipFile(io.BytesIO(pkg.archive_bytes), "r") as zf:
            names = zf.namelist()
        for required_file in ["manifest.json", "cv_data.enc", "key.b64"]:
            assert required_file in names, f"Missing: {required_file}"

    def test_different_builds_have_different_checksums(self):
        """Different CV content should produce different checksums."""
        cv2 = {**SAMPLE_CV, "title": "Different CV Title"}
        pkg1 = self.builder.build(SAMPLE_CV, user_id="u1", tier="Premium")
        pkg2 = self.builder.build(cv2, user_id="u1", tier="Premium")
        assert pkg1.checksum != pkg2.checksum

    def test_empty_cv_raises_package_error(self):
        """Architecture spec: If CV content invalid — Block export."""
        with pytest.raises(PackageError):
            self.builder.build({}, user_id="u1", tier="Free")

    def test_tiny_cv_raises_package_error(self):
        """Architecture spec: No <1KB empty zip outputs allowed."""
        with pytest.raises(PackageError):
            self.builder.build({"x": "y"}, user_id="u1", tier="Free")


# ── PackageBuilder.verify ─────────────────────────────────────────────────────

class TestPackageBuilderVerify:
    def setup_method(self):
        self.builder = PackageBuilder()
        self.pkg = self.builder.build(SAMPLE_CV, user_id="user-001", tier="Premium")

    def test_valid_package_verifies(self):
        result = self.builder.verify(self.pkg.archive_bytes)
        assert result["valid"] is True
        assert result["errors"] == []

    def test_valid_package_has_manifest(self):
        result = self.builder.verify(self.pkg.archive_bytes)
        assert "manifest" in result
        assert result["manifest"].get("user_id") == "user-001"

    def test_corrupted_archive_fails_verification(self):
        """Corrupting the archive bytes should fail verification."""
        corrupted = self.pkg.archive_bytes[:-50] + b"\x00" * 50
        result = self.builder.verify(corrupted)
        assert result["valid"] is False
        assert len(result["errors"]) > 0

    def test_non_zip_fails_verification(self):
        result = self.builder.verify(b"this is not a zip file at all")
        assert result["valid"] is False
        assert any("ZIP" in e or "zip" in e for e in result["errors"])

    def test_missing_manifest_file_fails(self):
        """Package missing manifest.json should fail."""
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w") as zf:
            zf.writestr("cv_data.enc", b"fake encrypted data")
            zf.writestr("key.b64", "fakekey")
        result = self.builder.verify(buffer.getvalue())
        assert result["valid"] is False

    def test_manifest_missing_fields_fails(self):
        """Manifest without required fields should fail."""
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w") as zf:
            zf.writestr("manifest.json", json.dumps({"version": "1.0.0"}))
            zf.writestr("cv_data.enc", b"fake")
            zf.writestr("key.b64", "fakekey")
        result = self.builder.verify(buffer.getvalue())
        assert result["valid"] is False


# ── PackageBuilder.extract_cv ─────────────────────────────────────────────────

class TestExtractCv:
    def setup_method(self):
        self.builder = PackageBuilder()

    def test_extract_roundtrip(self):
        pkg = self.builder.build(SAMPLE_CV, user_id="u1", tier="Premium")
        extracted = self.builder.extract_cv(pkg.archive_bytes)
        # Core CV fields should be preserved
        assert extracted["cv_id"] == SAMPLE_CV["cv_id"]
        assert extracted["personal_info"]["email"] == SAMPLE_CV["personal_info"]["email"]

    def test_extract_invalid_package_raises(self):
        with pytest.raises(PackageError):
            self.builder.extract_cv(b"not a valid package")


# ── Module-level convenience functions ───────────────────────────────────────

class TestConvenienceFunctions:
    def test_build_cv_package_returns_cv_package(self):
        pkg = build_cv_package(SAMPLE_CV, user_id="u1", tier="Premium")
        assert isinstance(pkg, CVPackage)

    def test_verify_package_integrity_returns_dict(self):
        pkg = build_cv_package(SAMPLE_CV, user_id="u1", tier="Premium")
        result = verify_package_integrity(pkg.archive_bytes)
        assert isinstance(result, dict)
        assert "valid" in result
        assert result["valid"] is True

    def test_package_user_id_property(self):
        pkg = build_cv_package(SAMPLE_CV, user_id="user-xyz", tier="Free")
        assert pkg.user_id == "user-xyz"

    def test_package_tier_property(self):
        pkg = build_cv_package(SAMPLE_CV, user_id="u1", tier="Enterprise")
        assert pkg.tier == "Enterprise"

    def test_package_checksum_property(self):
        pkg = build_cv_package(SAMPLE_CV, user_id="u1", tier="Premium")
        assert len(pkg.checksum) == 64


# ── Architecture enforcement tests ────────────────────────────────────────────

class TestArchitectureEnforcement:
    def test_no_streamlit_import_in_package_builder(self):
        """package_builder.py MUST NOT import streamlit."""
        import ast
        import pathlib
        path = pathlib.Path(__file__).parent.parent / "security" / "package_builder.py"
        source = path.read_text()
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        assert alias.name != "streamlit", \
                            "streamlit imported in package_builder.py!"
                elif isinstance(node, ast.ImportFrom):
                    assert node.module != "streamlit", \
                        "streamlit imported in package_builder.py!"

    def test_no_streamlit_import_in_encryption(self):
        """encryption.py MUST NOT import streamlit."""
        import ast
        import pathlib
        path = pathlib.Path(__file__).parent.parent / "security" / "encryption.py"
        source = path.read_text()
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        assert alias.name != "streamlit"
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        assert "streamlit" not in node.module
