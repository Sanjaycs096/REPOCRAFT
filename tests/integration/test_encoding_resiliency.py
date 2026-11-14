"""Regression test suite for cross-platform encoding resiliency.

Validates that RepoCraft installer and all CLI entry points handle
restrictive codepages (such as Windows cp1252, cp437, or ASCII) gracefully
without throwing UnicodeEncodeError when emitting emojis or unicode paths.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def test_install_unicode_path_under_cp1252(tmp_path: Path):
    """Regression test for test_51 failure: install.py must not crash under cp1252."""
    target = tmp_path / "proyecto_ñ_🚀"
    target.mkdir()

    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "cp1252"

    cmd = [
        sys.executable, str(REPO_ROOT / "install.py"),
        "--source", str(REPO_ROOT),
        "--agent", "antigravity",
        "--target", str(target),
    ]
    res = subprocess.run(cmd, env=env, capture_output=True, text=True, check=False)
    assert res.returncode == 0, f"install.py failed under cp1252: {res.stderr}"
    assert (target / ".agent" / "skills" / "repocraft" / "SKILL.md").is_file()


def test_status_cli_text_mode_under_cp1252(tmp_path: Path):
    """Regression test for test_66 failure: repocraft_status.py text mode must not crash under cp1252."""
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "cp1252"

    cmd = [
        sys.executable, str(REPO_ROOT / "skill" / "scripts" / "repocraft_status.py"),
        "--target", str(tmp_path),
    ]
    res = subprocess.run(cmd, env=env, capture_output=True, text=True, check=False)
    assert res.returncode == 0, f"repocraft_status.py failed under cp1252: {res.stderr}"
    assert "RepoCraft Status & Diagnostic Report" in res.stdout


def test_status_cli_json_mode_under_cp1252(tmp_path: Path):
    """Verify repocraft_status.py --json works under cp1252."""
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "cp1252"

    cmd = [
        sys.executable, str(REPO_ROOT / "skill" / "scripts" / "repocraft_status.py"),
        "--target", str(tmp_path),
        "--json",
    ]
    res = subprocess.run(cmd, env=env, capture_output=True, text=True, check=False)
    assert res.returncode == 0, f"repocraft_status.py --json failed under cp1252: {res.stderr}"


def test_release_cli_verify_distribution_under_cp1252(tmp_path: Path):
    """Verify repocraft_release.py verify-distribution works under cp1252."""
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "cp1252"

    cmd = [
        sys.executable, str(REPO_ROOT / "skill" / "scripts" / "repocraft_release.py"),
        "verify-distribution",
    ]
    res = subprocess.run(cmd, cwd=REPO_ROOT, env=env, capture_output=True, text=True, check=False)
    assert res.returncode == 0, f"repocraft_release.py failed under cp1252: {res.stderr}"
    assert "Distribution Check:" in res.stdout


@pytest.mark.parametrize("script_name", [
    "repocraft_intel.py",
    "repocraft_maintenance.py",
    "repocraft_security.py",
    "repocraft_repair.py",
    "repocraft_git.py",
    "repocraft_status.py",
    "repocraft_release.py",
])
def test_all_clis_help_under_cp1252(script_name: str):
    """Verify every CLI entry point runs --help under cp1252 without UnicodeEncodeError."""
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "cp1252"

    script = REPO_ROOT / "skill" / "scripts" / script_name
    cmd = [sys.executable, str(script), "--help"]
    res = subprocess.run(cmd, env=env, capture_output=True, text=True, check=False)
    assert res.returncode == 0, f"{script_name} --help failed under cp1252: {res.stderr}"
    assert "usage:" in res.stdout.lower() or "help" in res.stdout.lower()
