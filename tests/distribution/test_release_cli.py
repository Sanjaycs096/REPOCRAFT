"""Tests for repocraft_release.py CLI driver across all subcommands."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parent.parent.parent
CLI_PATH = REPO_ROOT / "skill" / "scripts" / "repocraft_release.py"
PACKAGE_PATH = REPO_ROOT / "dist" / "repocraft-1.0.0-rc1.zip"


def run_cli(*args: str) -> subprocess.CompletedProcess:
    cmd = [sys.executable, str(CLI_PATH)] + list(args)
    return subprocess.run(cmd, capture_output=True, text=True, check=False)


def test_scenario_15_cli_inspect_release():
    """Test inspect-release subcommand in text and json mode."""
    res = run_cli("inspect-release")
    assert res.returncode == 0
    assert "Release Candidate: 1.0.0-rc1" in res.stdout

    res_json = run_cli("inspect-release", "--json")
    assert res_json.returncode == 0
    data = json.loads(res_json.stdout)
    assert data["version"] == "1.0.0-rc1"
    assert data["package_exists"] is True


def test_scenario_15_cli_validate_release():
    """Test validate-release subcommand."""
    res = run_cli("validate-release", "--json")
    assert res.returncode == 0
    data = json.loads(res.stdout)
    assert data["status"] in ("READY_FOR_RELEASE", "READY_WITH_LIMITATIONS")
    assert data["gates_evaluated"] >= 9


def test_scenario_15_cli_draft_release_notes(tmp_path: Path):
    """Test draft-release-notes subcommand."""
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir()

    res = run_cli("draft-release-notes", "--reports", str(reports_dir))
    assert res.returncode == 0
    assert "Drafts written to" in res.stdout
    assert (reports_dir / "release-notes-draft.md").is_file()
    assert (reports_dir / "release-announcement-draft.md").is_file()


def test_scenario_15_cli_verify_distribution(tmp_path: Path):
    """Test verify-distribution subcommand."""
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir()

    res = run_cli("verify-distribution", "--package", str(PACKAGE_PATH), "--reports", str(reports_dir), "--json")
    assert res.returncode == 0
    data = json.loads(res.stdout)
    assert data["status"] == "VALID"
    assert data["path_traversal_safe"] is True
    assert (reports_dir / "distribution-verification.json").is_file()


def test_scenario_15_cli_test_installation(tmp_path: Path):
    """Test test-installation subcommand."""
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir()

    res = run_cli("test-installation", "--reports", str(reports_dir), "--json")
    assert res.returncode == 0
    data = json.loads(res.stdout)
    assert "clean_installation" in data
    assert (reports_dir / "installation-acceptance.json").is_file()


def test_scenario_15_cli_plan_upgrade(tmp_path: Path):
    """Test plan-upgrade subcommand."""
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir()

    res = run_cli("plan-upgrade", "--target", str(tmp_path), "--target-version", "1.0.0", "--reports", str(reports_dir), "--json")
    assert res.returncode == 0
    data = json.loads(res.stdout)
    assert data["candidate_version"] == "1.0.0"
    assert (reports_dir / "upgrade-validation.json").is_file()


def test_scenario_15_cli_generate_maintenance_report(tmp_path: Path):
    """Test generate-maintenance-report subcommand."""
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir()

    res = run_cli("generate-maintenance-report", "--reports", str(reports_dir), "--json")
    assert res.returncode == 0
    data = json.loads(res.stdout)
    assert data["installation_healthy"] is True
    assert (reports_dir / "maintenance-report.json").is_file()


def test_cli_invalid_subcommand():
    """Test handling of invalid subcommands."""
    res = run_cli("invalid-command")
    assert res.returncode != 0
