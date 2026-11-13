"""Tests for RepoCraft distribution package verification engine."""

from __future__ import annotations

import zipfile
from pathlib import Path

import pytest

from engine.distribution.distribution_types import DistributionCheckStatus
from engine.distribution.distribution_verifier import DistributionVerifier


REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DIST_ZIP = REPO_ROOT / "dist" / "repocraft-1.0.0-rc1.zip"


def test_scenario_01_verify_valid_distribution_package():
    """Scenario 1: Distribution package verification (clean zip, SHA-256 matches)."""
    assert DIST_ZIP.exists(), f"Distribution package not found at {DIST_ZIP}"

    verifier = DistributionVerifier(repo_root=REPO_ROOT, package_path=DIST_ZIP)
    result = verifier.verify()

    assert result.is_valid is True
    assert result.status == DistributionCheckStatus.VALID
    assert len(result.archive_sha256) == 64
    assert result.path_traversal_safe is True
    assert result.secret_scan_valid is True
    assert result.integrity_valid is True
    assert len(result.errors) == 0


def test_scenario_02_detect_corrupted_distribution_package(tmp_path: Path):
    """Scenario 2: Tampered distribution package detection (corrupted bytes)."""
    corrupt_zip = tmp_path / "corrupt.zip"
    corrupt_zip.write_bytes(b"PK\x03\x04this is totally corrupted zip payload garbage")

    verifier = DistributionVerifier(repo_root=REPO_ROOT, package_path=corrupt_zip)
    result = verifier.verify()

    assert result.is_valid is False
    assert result.status in (DistributionCheckStatus.INVALID, DistributionCheckStatus.CORRUPTED)
    assert any("corrupt" in err.lower() or "not a valid zip" in err.lower() or "bad" in err.lower() for err in result.errors)


def test_detect_missing_distribution_package(tmp_path: Path):
    """Scenario 2b: Missing distribution package detection."""
    missing_zip = tmp_path / "nonexistent.zip"

    verifier = DistributionVerifier(repo_root=REPO_ROOT, package_path=missing_zip)
    result = verifier.verify()

    assert result.is_valid is False
    assert result.status == DistributionCheckStatus.INVALID
    assert any("not found" in err.lower() for err in result.errors)


def test_scenario_03_reject_path_traversal_zip_slip(tmp_path: Path):
    """Scenario 3: Path traversal attack rejection in package archive (Zip Slip)."""
    malicious_zip = tmp_path / "malicious.zip"
    with zipfile.ZipFile(malicious_zip, "w") as zf:
        zf.writestr("../../etc/passwd", "root:x:0:0:root:/root:/bin/bash\n")
        zf.writestr("skill/SKILL.md", "# Test Skill\n")

    verifier = DistributionVerifier(repo_root=REPO_ROOT, package_path=malicious_zip)
    result = verifier.verify()

    assert result.path_traversal_safe is False
    assert result.is_valid is False
    assert any("traversal" in err.lower() for err in result.errors)


def test_reject_absolute_path_in_archive(tmp_path: Path):
    """Rejection of absolute path entries in archive."""
    malicious_zip = tmp_path / "malicious_abs.zip"
    with zipfile.ZipFile(malicious_zip, "w") as zf:
        zf.writestr("/etc/shadow", "forbidden\n")

    verifier = DistributionVerifier(repo_root=REPO_ROOT, package_path=malicious_zip)
    result = verifier.verify()

    assert result.path_traversal_safe is False
    assert result.is_valid is False


def test_detect_secret_in_distribution_archive(tmp_path: Path):
    """Detect accidental secret patterns bundled inside archive."""
    leaky_zip = tmp_path / "leaky.zip"
    with zipfile.ZipFile(leaky_zip, "w") as zf:
        zf.writestr(
            "skill/secret.txt",
            "-----BEGIN RSA PRIVATE KEY-----\nMIIEowIBAAKCAQEA0\n-----END RSA PRIVATE KEY-----\n"
        )
        zf.writestr("skill/SKILL.md", "# Valid skill\n")

    verifier = DistributionVerifier(repo_root=REPO_ROOT, package_path=leaky_zip)
    result = verifier.verify()

    assert result.secret_scan_valid is False
    assert result.is_valid is False
    assert any("secret" in err.lower() for err in result.errors)
