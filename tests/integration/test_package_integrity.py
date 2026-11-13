"""Tests 41-48: Package integrity verification, traversal protection, and secret scanning."""
from __future__ import annotations

import zipfile
from pathlib import Path
import pytest

from engine.release import (
    IntegrityVerifier,
    PackageBuilder,
    PackageManifest,
)


def test_41_verify_valid_archive(tmp_path: Path):
    """Verify an intact archive passes all integrity checks."""
    src = tmp_path / "src"
    src.mkdir()
    for f in ["README.md", "MANIFEST.json", "install.py", "pyproject.toml"]:
        (src / f).write_text(f"# {f}\n", encoding="utf-8")
    skill_dir = src / "skill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text("# Skill\n", encoding="utf-8")
    scripts = skill_dir / "scripts"
    scripts.mkdir()
    for s in ["repocraft_intel.py", "repocraft_maintenance.py", "repocraft_security.py", "repocraft_repair.py", "repocraft_git.py", "repocraft_status.py"]:
        (scripts / s).write_text("#!/usr/bin/env python3\n", encoding="utf-8")

    dist = tmp_path / "dist"
    zip_path, manifest = PackageBuilder.build_zip(src, dist)

    res = IntegrityVerifier.verify_archive(zip_path, manifest)
    assert res.is_valid is True
    assert res.extractable is True
    assert res.path_traversal_detected is False
    assert len(res.errors) == 0


def test_42_detect_path_traversal_entry(tmp_path: Path):
    """Detect and reject path traversal attempts in ZIP archive."""
    bad_zip = tmp_path / "traversal.zip"
    with zipfile.ZipFile(bad_zip, "w") as zf:
        zf.writestr("../../escape.txt", "malicious payload")
        zf.writestr("README.md", "# Valid")

    res = IntegrityVerifier.verify_archive(bad_zip)
    assert res.is_valid is False
    assert res.path_traversal_detected is True
    assert any("traversal" in err.lower() for err in res.errors)


def test_43_detect_duplicate_archive_entries(tmp_path: Path):
    """Detect duplicate filenames in zip archive."""
    dup_zip = tmp_path / "duplicate.zip"
    with zipfile.ZipFile(dup_zip, "w") as zf:
        zf.writestr("README.md", "# First")
        zf.writestr("README.md", "# Second")

    res = IntegrityVerifier.verify_archive(dup_zip)
    assert res.is_valid is False
    assert len(res.duplicate_entries) > 0
    assert any("duplicate" in err.lower() for err in res.errors)


def test_44_detect_unexpected_dev_files(tmp_path: Path):
    """Detect accidental inclusion of development cache or tests in release package."""
    dev_zip = tmp_path / "dev_leaks.zip"
    with zipfile.ZipFile(dev_zip, "w") as zf:
        zf.writestr("README.md", "# Ok")
        zf.writestr("tests/test_something.py", "def test_foo(): pass")
        zf.writestr("skill/__pycache__/cache.pyc", "binary")

    res = IntegrityVerifier.verify_archive(dev_zip)
    assert res.is_valid is False
    assert len(res.unexpected_files) >= 2


def test_45_detect_corrupt_zip_archive(tmp_path: Path):
    """Detect invalid or corrupted ZIP files."""
    corrupt_zip = tmp_path / "corrupt.zip"
    corrupt_zip.write_bytes(b"not a valid zip file header")

    res = IntegrityVerifier.verify_archive(corrupt_zip)
    assert res.is_valid is False
    assert any("invalid" in err.lower() or "corrupted" in err.lower() for err in res.errors)


def test_46_detect_secret_pattern_leak(tmp_path: Path):
    """Detect potential GitHub personal access tokens packaged in files."""
    leak_zip = tmp_path / "leak.zip"
    with zipfile.ZipFile(leak_zip, "w") as zf:
        zf.writestr("README.md", "README text")
        # Synthesize fake GitHub PAT pattern
        zf.writestr("config.py", f"GITHUB_TOKEN = 'ghp_{'A' * 36}'")

    res = IntegrityVerifier.verify_archive(leak_zip)
    assert res.is_valid is False
    assert len(res.secret_patterns_detected) > 0
    assert any("secret" in err.lower() for err in res.errors)


def test_46b_detect_drive_letter_path_traversal(tmp_path: Path):
    """Detect Windows drive-letter escape attempt in zip entry."""
    bad_zip = tmp_path / "drive_escape.zip"
    with zipfile.ZipFile(bad_zip, "w") as zf:
        zf.writestr("C:/windows/system32/calc.exe", "fake")
    res = IntegrityVerifier.verify_archive(bad_zip)
    assert res.is_valid is False
    assert res.path_traversal_detected is True


def test_46c_detect_ssh_private_key_leak(tmp_path: Path):
    """Detect accidental RSA private key pattern inside package."""
    key_zip = tmp_path / "ssh_key.zip"
    with zipfile.ZipFile(key_zip, "w") as zf:
        zf.writestr("id_rsa", "-----BEGIN RSA PRIVATE KEY-----\nMIIEowIBAAKCAQEA0\n")
    res = IntegrityVerifier.verify_archive(key_zip)
    assert res.is_valid is False
    assert len(res.secret_patterns_detected) > 0


def test_46d_detect_aws_access_key_leak(tmp_path: Path):
    """Detect accidental AWS access key in package."""
    aws_zip = tmp_path / "aws.zip"
    with zipfile.ZipFile(aws_zip, "w") as zf:
        zf.writestr("credentials.txt", "aws_access_key_id = AKIAIOSFODNN7EXAMPLE")
    res = IntegrityVerifier.verify_archive(aws_zip)
    assert res.is_valid is False
    assert len(res.secret_patterns_detected) > 0


def test_46e_non_existent_archive_handling(tmp_path: Path):
    """Detect non-existent archive file."""
    res = IntegrityVerifier.verify_archive(tmp_path / "missing.zip")
    assert res.is_valid is False
    assert any("not found" in err.lower() for err in res.errors)

