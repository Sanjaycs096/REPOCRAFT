"""Tests 75-84: repocraft_status.py diagnostic CLI commands and modes."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
import pytest

from engine.release import PackageBuilder

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
STATUS_SCRIPT = REPO_ROOT / "skill" / "scripts" / "repocraft_status.py"


def test_63_cli_help():
    """Verify --help exits with code 0."""
    res = subprocess.run([sys.executable, str(STATUS_SCRIPT), "--help"], capture_output=True, text=True)
    assert res.returncode == 0
    assert "diagnostic and environment inspector" in res.stdout


def test_64_cli_invalid_args():
    """Verify unknown argument exits with code 2."""
    res = subprocess.run([sys.executable, str(STATUS_SCRIPT), "--unknown-flag"], capture_output=True, text=True)
    assert res.returncode == 2


def test_65_cli_json_mode(tmp_path: Path):
    """Verify --json produces valid parseable JSON."""
    res = subprocess.run(
        [sys.executable, str(STATUS_SCRIPT), "--target", str(tmp_path), "--json"],
        capture_output=True, text=True,
    )
    assert res.returncode == 0
    data = json.loads(res.stdout)
    assert data["schema_version"] == "1.0.0"
    assert data["repocraft_version"] == "1.0.0-rc1"
    assert data["overall_status"] in ("READY", "READY_WITH_LIMITATIONS")


def test_66_cli_text_mode(tmp_path: Path):
    """Verify text output contains status and banner."""
    res = subprocess.run(
        [sys.executable, str(STATUS_SCRIPT), "--target", str(tmp_path)],
        capture_output=True, text=True,
    )
    assert res.returncode == 0
    assert "RepoCraft Status & Diagnostic Report" in res.stdout
    assert "Python Runtime:" in res.stdout


def test_67_cli_verify_installation(tmp_path: Path):
    """Verify --verify-installation detects intact or missing installation."""
    # First on uninstalled project
    res1 = subprocess.run(
        [sys.executable, str(STATUS_SCRIPT), "--target", str(tmp_path), "--verify-installation", "--json"],
        capture_output=True, text=True,
    )
    data1 = json.loads(res1.stdout)
    assert data1["installation_verification"]["is_valid"] is False
    assert data1["overall_status"] == "INVALID_INSTALLATION"

    # Install repocraft into tmp_path
    subprocess.run(
        [sys.executable, str(REPO_ROOT / "install.py"), "--source", str(REPO_ROOT), "--target", str(tmp_path)],
        check=True,
    )

    # Now verify installation again
    res2 = subprocess.run(
        [sys.executable, str(STATUS_SCRIPT), "--target", str(tmp_path), "--verify-installation", "--json"],
        capture_output=True, text=True,
    )
    assert res2.returncode == 0
    data2 = json.loads(res2.stdout)
    assert data2["installation_verification"]["is_valid"] is True
    assert data2["overall_status"] == "READY"


def test_68_cli_verify_package(tmp_path: Path):
    """Verify --verify-package checks release archive integrity."""
    dist = tmp_path / "dist"
    zip_path, _ = PackageBuilder.build_zip(REPO_ROOT, dist)

    res = subprocess.run(
        [sys.executable, str(STATUS_SCRIPT), "--target", str(tmp_path), "--verify-package", str(zip_path), "--json"],
        capture_output=True, text=True,
    )
    assert res.returncode == 0
    data = json.loads(res.stdout)
    assert data["package_verification"]["is_valid"] is True
    assert data["package_verification"]["extractable"] is True


def test_69_read_only_guarantee(tmp_path: Path):
    """Verify running repocraft_status modifies zero files in target directory."""
    sentinel = tmp_path / "user_code.py"
    sentinel.write_text("print('hello world')", encoding="utf-8")
    before_files = set(tmp_path.rglob("*"))

    subprocess.run([sys.executable, str(STATUS_SCRIPT), "--target", str(tmp_path), "--json"], check=True)

    after_files = set(tmp_path.rglob("*"))
    assert before_files == after_files
    assert sentinel.read_text(encoding="utf-8") == "print('hello world')"


def test_69b_status_cli_reports_dir_option(tmp_path: Path):
    """Verify --reports option evaluates lifecycle state."""
    reports = tmp_path / "reports"
    reports.mkdir()
    (reports / "inventory.json").write_text(
        json.dumps({
            "schema_version": "1.0.0",
            "generated_at": "2026-01-01T00:00:00Z",
            "target_root": str(tmp_path),
            "files_count": 1,
        }),
        encoding="utf-8",
    )
    res = subprocess.run(
        [sys.executable, str(STATUS_SCRIPT), "--target", str(tmp_path), "--reports", str(reports), "--json"],
        capture_output=True, text=True,
    )
    assert res.returncode == 0
    data = json.loads(res.stdout)
    assert data["lifecycle_verification"]["checked"] is True
    assert "phase_1_intel" in data["lifecycle_verification"]["executed_phases"]


def test_69c_status_cli_python_version_support():
    """Verify current python runtime reports supported >= 3.9."""
    res = subprocess.run([sys.executable, str(STATUS_SCRIPT), "--json"], capture_output=True, text=True)
    assert res.returncode == 0
    data = json.loads(res.stdout)
    assert data["python_environment"]["supported"] is True


def test_69d_status_cli_available_phases_count():
    """Verify all 7 phases are listed in available_phases."""
    res = subprocess.run([sys.executable, str(STATUS_SCRIPT), "--json"], capture_output=True, text=True)
    assert res.returncode == 0
    data = json.loads(res.stdout)
    assert len(data["available_phases"]) == 7


def test_69e_status_cli_known_limitations_included():
    """Verify known limitations are present in JSON output."""
    res = subprocess.run([sys.executable, str(STATUS_SCRIPT), "--json"], capture_output=True, text=True)
    assert res.returncode == 0
    data = json.loads(res.stdout)
    assert len(data["known_limitations"]) >= 2

