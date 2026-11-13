"""Tests 67-74: Security acceptance, standard library verification, and audit tools."""
from __future__ import annotations

import json
from pathlib import Path
import pytest

from engine.compatibility import InstallationAdapter
from engine.release import ArchitectureAuditor, SecurityAuditor

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def test_59_architecture_auditor_clean():
    """Verify ArchitectureAuditor executes without critical or high severity defects."""
    audit = ArchitectureAuditor.audit(REPO_ROOT)
    assert audit["audit_status"] == "PASS"
    critical_or_high = [
        f for f in audit["findings"]
        if f["severity"] in ("CRITICAL", "HIGH")
    ]
    assert len(critical_or_high) == 0, f"Critical/High findings: {critical_or_high}"
    md = ArchitectureAuditor.generate_markdown(audit)
    assert "Architecture & Structural Audit" in md


def test_60_security_auditor_clean():
    """Verify SecurityAuditor confirms zero unauthorized shell=True and standard library runtime."""
    audit = SecurityAuditor.audit(REPO_ROOT)
    assert audit["audit_status"] == "PASS"
    assert audit["dependency_count"] == 0
    assert audit["subprocess_safety"] == "STRICT_LIST_ONLY"
    critical_or_high = [
        f for f in audit["findings"]
        if f["severity"] in ("CRITICAL", "HIGH")
    ]
    assert len(critical_or_high) == 0, f"Security findings: {critical_or_high}"
    md = SecurityAuditor.generate_markdown(audit)
    assert "Security & Supply Chain Audit" in md


def test_61_install_path_traversal_rejection(tmp_path: Path):
    """Verify InstallationAdapter rejects destination path escapes."""
    target = tmp_path / "project"
    target.mkdir()

    # Outside repo
    outside_dest = tmp_path / "outside_dir"
    safe, err = InstallationAdapter.validate_destination_safety(outside_dest, target)
    assert safe is False
    assert "escapes" in err.lower()

    # Inside .git
    git_dest = target / ".git"
    safe, err = InstallationAdapter.validate_destination_safety(git_dest, target)
    assert safe is False
    assert ".git" in err.lower()

    # Target root itself
    safe, err = InstallationAdapter.validate_destination_safety(target, target)
    assert safe is False
    assert "root" in err.lower()


def test_62_pyproject_dependencies_empty():
    """Verify RepoCraft requires zero runtime pip packages."""
    text = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert "dependencies = []" in text


def test_62b_secret_redaction_in_git_url():
    """Verify redact_url strips basic auth tokens."""
    from engine.git.git_environment import redact_url
    clean_url, was_redacted = redact_url("https://user:ghp_secrettoken123@github.com/org/repo.git")
    assert was_redacted is True
    assert "ghp_secrettoken123" not in clean_url
    assert "***:***" in clean_url or "***@" in clean_url


def test_62c_no_hardcoded_developer_paths():
    """Verify no hardcoded developer paths exist in skill/scripts Python files."""
    py_files = list((REPO_ROOT / "skill" / "scripts").rglob("*.py"))
    forbidden_tokens = ["Users/sanja", "Users\\sanja", "/home/", "C:\\Users\\"]
    for pf in py_files:
        content = pf.read_text(encoding="utf-8", errors="replace")
        for token in forbidden_tokens:
            assert token not in content, f"Hardcoded developer path found in {pf}: {token}"


def test_62d_all_cli_scripts_have_docstrings():
    """Verify every CLI script contains an informative module docstring."""
    cli_files = [
        "repocraft_intel.py",
        "repocraft_maintenance.py",
        "repocraft_security.py",
        "repocraft_repair.py",
        "repocraft_git.py",
        "repocraft_status.py",
    ]
    for c in cli_files:
        path = REPO_ROOT / "skill" / "scripts" / c
        content = path.read_text(encoding="utf-8", errors="replace")
        assert '"""' in content, f"Missing docstring in {c}"


def test_62e_all_cli_scripts_define_argparse():
    """Verify all CLI scripts use standard argparse."""
    cli_files = [
        "repocraft_intel.py",
        "repocraft_maintenance.py",
        "repocraft_security.py",
        "repocraft_repair.py",
        "repocraft_git.py",
        "repocraft_status.py",
    ]
    for c in cli_files:
        path = REPO_ROOT / "skill" / "scripts" / c
        content = path.read_text(encoding="utf-8", errors="replace")
        assert "argparse" in content, f"argparse not imported in {c}"

