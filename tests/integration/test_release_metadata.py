"""Tests 59-66: Release metadata, version consistency, gate evaluations, and checklist."""
from __future__ import annotations

import json
from pathlib import Path
import pytest

from engine.release import (
    GateStatus,
    PackageManifest,
    PackageValidationResult,
    ReleaseReportGenerator,
    ReleaseStatus,
    ReleaseValidator,
)

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def test_54_version_consistency():
    """Verify version string is identical across pyproject.toml, MANIFEST.json, install.py, and repocraft_status.py."""
    # pyproject.toml
    pyproject_text = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert 'version = "1.0.0-rc1"' in pyproject_text

    # MANIFEST.json
    manifest_data = json.loads((REPO_ROOT / "MANIFEST.json").read_text(encoding="utf-8"))
    assert manifest_data["version"] == "1.0.0-rc1"
    assert manifest_data["phase"] == 6

    # install.py
    install_text = (REPO_ROOT / "install.py").read_text(encoding="utf-8")
    assert '"version": "1.0.0-rc1"' in install_text

    # repocraft_status.py
    status_text = (REPO_ROOT / "skill" / "scripts" / "repocraft_status.py").read_text(encoding="utf-8")
    assert 'VERSION = "1.0.0-rc1"' in status_text


def test_55_evaluate_release_gates_all_pass():
    """Verify all 9 release gates evaluate to PASS under valid conditions."""
    status, gates = ReleaseValidator.evaluate_all_gates(
        source_root=REPO_ROOT,
        package_valid=True,
        integration_valid=True,
        all_tests_passed=True,
        test_counts={"phase_0": 2, "phase_1": 22, "phase_2": 41, "phase_3": 70, "phase_4": 82, "phase_5": 101},
    )
    assert status == ReleaseStatus.READY_FOR_RELEASE
    assert len(gates) == 9
    assert all(g.status == GateStatus.PASS for g in gates.values())


def test_56_gate_c_fails_on_integration_failure():
    """Verify Gate C fails and blocks release when lifecycle integration fails."""
    status, gates = ReleaseValidator.evaluate_all_gates(
        source_root=REPO_ROOT,
        package_valid=True,
        integration_valid=False,
        all_tests_passed=True,
    )
    assert status == ReleaseStatus.BLOCKED
    assert gates["gate_c_integration"].status == GateStatus.FAIL
    assert len(gates["gate_c_integration"].blockers) > 0


def test_57_gate_g_fails_on_test_failure():
    """Verify Gate G fails when test assertions fail."""
    status, gates = ReleaseValidator.evaluate_all_gates(
        source_root=REPO_ROOT,
        package_valid=True,
        integration_valid=True,
        all_tests_passed=False,
    )
    assert status == ReleaseStatus.BLOCKED
    assert gates["gate_g_testing"].status == GateStatus.FAIL


def test_58_generate_release_artifacts(tmp_path: Path):
    """Verify ReleaseReportGenerator writes all 4 release artifacts cleanly."""
    reports = tmp_path / "reports"
    reports.mkdir()

    manifest = PackageManifest(
        package_name="RepoCraft",
        version="1.0.0-rc1",
        archive_name="repocraft-1.0.0-rc1.zip",
        archive_sha256="fake_sha256",
        created_at="2026-01-01T00:00:00Z",
        total_files=5,
        total_bytes=1000,
        files={},
    )
    integrity = PackageValidationResult(
        is_valid=True,
        archive_path="repocraft-1.0.0-rc1.zip",
    )
    status, gates = ReleaseValidator.evaluate_all_gates(
        source_root=REPO_ROOT,
        package_valid=True,
        integration_valid=True,
        all_tests_passed=True,
    )

    out = ReleaseReportGenerator.generate(
        output_dir=reports,
        manifest=manifest,
        integrity_result=integrity,
        release_status=status,
        gates=gates,
    )

    assert out["release_manifest"].is_file()
    assert out["package_integrity"].is_file()
    assert out["release_readiness"].is_file()
    assert out["release_checklist"].is_file()

    chk_text = out["release_checklist"].read_text(encoding="utf-8")
    assert "Release Readiness Checklist" in chk_text
    assert "READY FOR RELEASE" in chk_text

