"""Tests for post-release maintenance auditor and zero-telemetry guarantee."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from engine.distribution.maintenance_auditor import MaintenanceAuditor


REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def test_scenario_13_audit_clean_repository_health():
    """Scenario 13: Maintenance auditor on clean repo verifies consistency."""
    report = MaintenanceAuditor.audit_repository_health(REPO_ROOT, version="1.0.0-rc1")

    assert report.installation_healthy is True
    assert report.manifests_consistent is True
    assert report.policy_files_intact is True
    assert report.cli_drivers_intact is True
    assert report.schemas_compatible is True
    assert report.zero_telemetry_guarantee is True
    assert len(report.errors) == 0


def test_scenario_13_detect_manifest_version_inconsistency(tmp_path: Path):
    """Scenario 13b: Detect version mismatch between manifest and pyproject.toml."""
    # Create mock repo root
    mock_root = tmp_path / "mock_repo"
    mock_root.mkdir()
    (mock_root / "MANIFEST.json").write_text(json.dumps({"version": "0.9.0"}), encoding="utf-8")
    (mock_root / "pyproject.toml").write_text('version = "1.0.0-rc1"\n', encoding="utf-8")
    (mock_root / "install.py").write_text('"version": "1.0.0-rc1"\n', encoding="utf-8")

    report = MaintenanceAuditor.audit_repository_health(mock_root, version="1.0.0-rc1")
    assert report.manifests_consistent is False
    assert report.installation_healthy is False
    assert any("version mismatch" in err.lower() for err in report.errors)


def test_detect_missing_policy_files(tmp_path: Path):
    """Detect missing policy references in mock repo."""
    mock_root = tmp_path / "mock_repo"
    mock_root.mkdir()
    (mock_root / "MANIFEST.json").write_text(json.dumps({"version": "1.0.0-rc1"}), encoding="utf-8")
    (mock_root / "pyproject.toml").write_text('version = "1.0.0-rc1"\n', encoding="utf-8")
    (mock_root / "install.py").write_text('"version": "1.0.0-rc1"\n', encoding="utf-8")
    (mock_root / "skill" / "references").mkdir(parents=True)
    # Empty reference directory

    report = MaintenanceAuditor.audit_repository_health(mock_root, version="1.0.0-rc1")
    assert report.policy_files_intact is False
    assert any("missing or empty policy files" in err.lower() for err in report.errors)


def test_scenario_14_verify_zero_telemetry_clean():
    """Scenario 14: Verification that RepoCraft codebase has zero telemetry."""
    report = MaintenanceAuditor.audit_repository_health(REPO_ROOT, version="1.0.0-rc1")
    assert report.zero_telemetry_guarantee is True
    assert not any("tracking" in err.lower() or "telemetry" in err.lower() for err in report.errors)


def test_scenario_14_detect_forbidden_telemetry_import(tmp_path: Path):
    """Scenario 14b: AST auditor detects forbidden telemetry imports."""
    mock_root = tmp_path / "mock_repo"
    scripts_dir = mock_root / "skill" / "scripts"
    scripts_dir.mkdir(parents=True)

    # Insert a malicious file with telemetry import
    bad_script = scripts_dir / "telemetry_leak.py"
    bad_script.write_text("import sentry_sdk\nsentry_sdk.init('https://fake@sentry.io/123')\n", encoding="utf-8")

    (mock_root / "MANIFEST.json").write_text(json.dumps({"version": "1.0.0-rc1"}), encoding="utf-8")
    (mock_root / "pyproject.toml").write_text('version = "1.0.0-rc1"\n', encoding="utf-8")
    (mock_root / "install.py").write_text('"version": "1.0.0-rc1"\n', encoding="utf-8")

    report = MaintenanceAuditor.audit_repository_health(mock_root, version="1.0.0-rc1")
    assert report.zero_telemetry_guarantee is False
    assert any("sentry_sdk" in err.lower() for err in report.errors)

