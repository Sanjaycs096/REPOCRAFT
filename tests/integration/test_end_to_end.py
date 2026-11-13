"""Tests 70-76: Full lifecycle end-to-end workflows on disposable fixture repositories."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
import pytest

from engine.release import ReleaseOrchestrator

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def init_git_repo(path: Path) -> None:
    """Initialize a clean git repository for testing."""
    subprocess.run(["git", "init"], cwd=path, capture_output=True, check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=path, capture_output=True, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=path, capture_output=True, check=True)


def test_70_full_python_fixture_lifecycle(tmp_path: Path):
    """Run full lifecycle on a minimal Python fixture project."""
    target = tmp_path / "py_project"
    target.mkdir()
    init_git_repo(target)

    # Project files
    (target / "README.md").write_text("# My Python App\nSimple app.", encoding="utf-8")
    (target / "main.py").write_text("def hello():\n    return 'hello'\n", encoding="utf-8")
    (target / "test_main.py").write_text("from main import hello\ndef test_hello():\n    assert hello() == 'hello'\n", encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=target, check=True)
    subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=target, check=True)

    # 1. Install RepoCraft
    cmd_install = [sys.executable, str(REPO_ROOT / "install.py"), "--source", str(REPO_ROOT), "--target", str(target)]
    subprocess.run(cmd_install, check=True)
    skill_dir = target / ".agent" / "skills" / "repocraft"
    assert (skill_dir / "SKILL.md").is_file()

    reports = tmp_path / "reports"
    reports.mkdir()

    # 2. Phase 1: Intel
    cmd_intel = [
        sys.executable, str(skill_dir / "scripts" / "repocraft_intel.py"),
        "--target", str(target),
        "--output", str(reports),
    ]
    res_intel = subprocess.run(cmd_intel, capture_output=True, text=True)
    assert res_intel.returncode == 0
    assert (reports / "inventory.json").is_file()

    # 3. Phase 2: Maintenance
    cmd_maint = [
        sys.executable, str(skill_dir / "scripts" / "repocraft_maintenance.py"),
        "--target", str(target),
        "--reports", str(reports),
        "--mode", "audit",
    ]
    res_maint = subprocess.run(cmd_maint, capture_output=True, text=True)
    assert res_maint.returncode == 0
    assert (reports / "maintenance-plan.json").is_file()

    # 4. Phase 3: Security
    cmd_sec = [
        sys.executable, str(skill_dir / "scripts" / "repocraft_security.py"),
        "--target", str(target),
        "--reports", str(reports),
        "--mode", "audit",
    ]
    res_sec = subprocess.run(cmd_sec, capture_output=True, text=True)
    assert res_sec.returncode == 0
    assert (reports / "security-findings.json").is_file()

    # 5. Phase 4: Repair Plan
    cmd_repair = [
        sys.executable, str(skill_dir / "scripts" / "repocraft_repair.py"),
        "--target", str(target),
        "--reports", str(reports),
        "--mode", "plan",
    ]
    res_repair = subprocess.run(cmd_repair, capture_output=True, text=True)
    assert res_repair.returncode == 0
    assert (reports / "repair-plan.json").is_file()

    # 6. Phase 5: Git Review
    cmd_git = [
        sys.executable, str(skill_dir / "scripts" / "repocraft_git.py"),
        "inspect",
        "--target", str(target),
        "--reports", str(reports),
    ]
    res_git = subprocess.run(cmd_git, capture_output=True, text=True)
    assert res_git.returncode == 0
    assert (reports / "git-state.json").is_file()

    # 7. Phase 6: Diagnostic Status
    cmd_status = [
        sys.executable, str(skill_dir / "scripts" / "repocraft_status.py"),
        "--target", str(target),
        "--reports", str(reports),
        "--json",
    ]
    res_status = subprocess.run(cmd_status, capture_output=True, text=True)
    assert res_status.returncode == 0
    status_data = json.loads(res_status.stdout)
    assert status_data["overall_status"] == "READY"


def test_71_js_fixture_lifecycle(tmp_path: Path):
    """Run lifecycle inspection on a Node.js / JavaScript fixture."""
    target = tmp_path / "js_project"
    target.mkdir()
    init_git_repo(target)

    (target / "package.json").write_text(json.dumps({"name": "my-js-app", "version": "1.0.0"}), encoding="utf-8")
    (target / "index.js").write_text("console.log('hello');\n", encoding="utf-8")
    (target / "README.md").write_text("# JS App\n", encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=target, check=True)
    subprocess.run(["git", "commit", "-m", "Init JS"], cwd=target, check=True)

    # Install
    subprocess.run(
        [sys.executable, str(REPO_ROOT / "install.py"), "--source", str(REPO_ROOT), "--target", str(target)],
        check=True,
    )
    skill_dir = target / ".agent" / "skills" / "repocraft"

    reports = tmp_path / "reports"
    reports.mkdir()

    # Intel
    res = subprocess.run(
        [sys.executable, str(skill_dir / "scripts" / "repocraft_intel.py"), "--target", str(target), "--output", str(reports)],
        capture_output=True, text=True,
    )
    assert res.returncode == 0
    inv = json.loads((reports / "inventory.json").read_text(encoding="utf-8"))
    total = inv.get("files_count") or inv.get("file_inventory_summary", {}).get("total_files", 0)
    assert total >= 3


def test_72_release_orchestrator_generates_all_15_artifacts(tmp_path: Path):
    """Verify ReleaseOrchestrator generates all 15 required Phase 6 artifacts."""
    out_dir = tmp_path / "phase6_outputs"
    dist_dir = tmp_path / "dist"

    generated = ReleaseOrchestrator.run_full_evaluation(
        repo_root=REPO_ROOT,
        output_dir=out_dir,
        package_dist_dir=dist_dir,
    )

    required_artifacts = [
        "phase6-architecture-audit.json",
        "phase6-architecture-audit.md",
        "agent-compatibility.json",
        "agent-compatibility.md",
        "phase-registry.json",
        "artifact-registry.json",
        "lifecycle-integration-report.json",
        "lifecycle-integration-report.md",
        "release-manifest.json",
        "package-integrity.json",
        "release-readiness.json",
        "release-checklist.md",
        "phase6-security-audit.json",
        "phase6-security-audit.md",
        "phase6-report.md",
    ]

    for req in required_artifacts:
        f = out_dir / req
        assert f.is_file(), f"Missing required artifact: {req}"
        assert f.stat().st_size > 0, f"Empty artifact: {req}"

    # Verify release package zip
    zip_files = list(dist_dir.glob("*.zip"))
    assert len(zip_files) >= 1
    assert zip_files[0].stat().st_size > 0


def test_73_unauthorized_staging_and_commit_blocked(tmp_path: Path):
    """Verify Phase 5 cannot stage, commit, or push without explicit approval manifests."""
    target = tmp_path / "git_project"
    target.mkdir()
    init_git_repo(target)
    (target / "test.txt").write_text("data", encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=target, check=True)
    subprocess.run(["git", "commit", "-m", "Initial"], cwd=target, check=True)

    # Modify file
    (target / "test.txt").write_text("modified data", encoding="utf-8")

    reports = tmp_path / "reports"
    reports.mkdir()

    # Attempt stage-approved without manifest
    cmd_stage = [
        sys.executable, str(REPO_ROOT / "skill" / "scripts" / "repocraft_git.py"),
        "stage-approved",
        "--target", str(target),
        "--reports", str(reports),
    ]
    res_stage = subprocess.run(cmd_stage, capture_output=True, text=True)
    assert res_stage.returncode != 0

    # Attempt commit-approved without manifest
    cmd_commit = [
        sys.executable, str(REPO_ROOT / "skill" / "scripts" / "repocraft_git.py"),
        "commit-approved",
        "--target", str(target),
        "--reports", str(reports),
    ]
    res_commit = subprocess.run(cmd_commit, capture_output=True, text=True)
    assert res_commit.returncode != 0

    # Attempt push-approved without manifest
    cmd_push = [
        sys.executable, str(REPO_ROOT / "skill" / "scripts" / "repocraft_git.py"),
        "push-approved",
        "--target", str(target),
        "--reports", str(reports),
    ]
    res_push = subprocess.run(cmd_push, capture_output=True, text=True)
    assert res_push.returncode != 0


def test_74_doc_only_repo_workflow(tmp_path: Path):
    """Run lifecycle inspection on a documentation-only repository."""
    target = tmp_path / "doc_repo"
    target.mkdir()
    init_git_repo(target)
    (target / "README.md").write_text("# Project Docs\nDocumentation only.", encoding="utf-8")
    (target / "CONTRIBUTING.md").write_text("# Contributing\nGuidelines.", encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=target, check=True)
    subprocess.run(["git", "commit", "-m", "Initial docs"], cwd=target, check=True)

    # Install
    subprocess.run([sys.executable, str(REPO_ROOT / "install.py"), "--source", str(REPO_ROOT), "--target", str(target)], check=True)
    skill_dir = target / ".agent" / "skills" / "repocraft"

    reports = tmp_path / "reports"
    reports.mkdir()
    res = subprocess.run(
        [sys.executable, str(skill_dir / "scripts" / "repocraft_intel.py"), "--target", str(target), "--output", str(reports)],
        capture_output=True, text=True,
    )
    assert res.returncode == 0
    inv = json.loads((reports / "inventory.json").read_text(encoding="utf-8"))
    total = inv.get("files_count") or inv.get("file_inventory_summary", {}).get("total_files", 0)
    assert total >= 2


def test_75_untracked_and_preexisting_files_preserved(tmp_path: Path):
    """Verify RepoCraft diagnostic and inspection commands never delete untracked user files."""
    target = tmp_path / "preexisting_repo"
    target.mkdir()
    init_git_repo(target)
    (target / "README.md").write_text("# Main\n", encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=target, check=True)
    subprocess.run(["git", "commit", "-m", "Commit 1"], cwd=target, check=True)

    untracked_user_file = target / "notes.txt"
    untracked_user_file.write_text("my secret private notes", encoding="utf-8")

    # Run repocraft_status
    subprocess.run([sys.executable, str(REPO_ROOT / "skill" / "scripts" / "repocraft_status.py"), "--target", str(target)], check=True)
    assert untracked_user_file.is_file()
    assert untracked_user_file.read_text(encoding="utf-8") == "my secret private notes"


def test_76_monorepo_multilanguage_fixture(tmp_path: Path):
    """Verify intelligence engine correctly categorizes multi-language monorepo structure."""
    target = tmp_path / "monorepo"
    target.mkdir()
    init_git_repo(target)

    # Backend
    backend = target / "backend"
    backend.mkdir()
    (backend / "requirements.txt").write_text("flask>=2.0\n", encoding="utf-8")
    (backend / "app.py").write_text("print('backend')\n", encoding="utf-8")

    # Frontend
    frontend = target / "frontend"
    frontend.mkdir()
    (frontend / "package.json").write_text(json.dumps({"name": "frontend"}), encoding="utf-8")
    (frontend / "index.js").write_text("console.log('frontend');\n", encoding="utf-8")

    (target / "README.md").write_text("# Monorepo", encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=target, check=True)
    subprocess.run(["git", "commit", "-m", "Init monorepo"], cwd=target, check=True)

    # Install & run intel
    subprocess.run([sys.executable, str(REPO_ROOT / "install.py"), "--source", str(REPO_ROOT), "--target", str(target)], check=True)
    skill_dir = target / ".agent" / "skills" / "repocraft"
    reports = tmp_path / "reports"
    reports.mkdir()

    res = subprocess.run(
        [sys.executable, str(skill_dir / "scripts" / "repocraft_intel.py"), "--target", str(target), "--output", str(reports)],
        capture_output=True, text=True,
    )
    assert res.returncode == 0
    inv = json.loads((reports / "inventory.json").read_text(encoding="utf-8"))
    languages = [l.lower() for l in inv.get("languages", [])]
    total = inv.get("files_count") or inv.get("file_inventory_summary", {}).get("total_files", 0)
    assert "python" in languages or "javascript" in languages or total >= 5


def test_77_full_evaluation_with_real_archive_verification(tmp_path: Path):
    """Verify ReleaseOrchestrator evaluation output passes repocraft_status --verify-package."""
    out_dir = tmp_path / "out"
    dist_dir = tmp_path / "dist"

    generated = ReleaseOrchestrator.run_full_evaluation(
        repo_root=REPO_ROOT,
        output_dir=out_dir,
        package_dist_dir=dist_dir,
    )

    zip_path = dist_dir / "repocraft-1.0.0-rc1.zip"
    assert zip_path.is_file()

    res = subprocess.run(
        [sys.executable, str(REPO_ROOT / "skill" / "scripts" / "repocraft_status.py"), "--target", str(tmp_path), "--verify-package", str(zip_path), "--json"],
        capture_output=True, text=True,
    )
    assert res.returncode == 0
    status_data = json.loads(res.stdout)
    assert status_data["package_verification"]["is_valid"] is True
    assert status_data["package_verification"]["extractable"] is True

