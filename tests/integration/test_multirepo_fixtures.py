"""Multi-repository type fixture integration and safety test suite.

Validates that RepoCraft functions cleanly, generates evidence-backed reports,
and strictly preserves original user source files across 12 distinct repository types:
1. Minimal Python repository
2. JavaScript / TypeScript repository
3. Java / Kotlin repository
4. Rust / Go repository
5. Static website / documentation repository
6. Monorepo with multiple components
7. Professional structure repository
8. Poor / incomplete documentation repository
9. Repository with uncommitted user modifications
10. Repository with dynamic imports and framework references
11. Repository with hidden config files and unusual naming
12. Repository with missing tests and incomplete CI
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _init_git(target: Path) -> None:
    subprocess.run(["git", "init"], cwd=target, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Fixture User"], cwd=target, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "fixture@example.com"], cwd=target, check=True, capture_output=True)


def _run_repocraft_cycle(target: Path, reports: Path) -> Dict[str, Any]:
    """Execute complete read-only RepoCraft audit cycle on a fixture repository."""
    # 1. Snapshot user files
    user_file_hashes = {}
    for p in target.rglob("*"):
        if p.is_file() and ".git" not in p.parts and ".agent" not in p.parts:
            user_file_hashes[str(p.relative_to(target))] = _sha256(p)

    # 2. Install RepoCraft
    cmd_install = [
        sys.executable, str(REPO_ROOT / "install.py"),
        "--source", str(REPO_ROOT),
        "--agent", "antigravity",
        "--target", str(target),
    ]
    res_inst = subprocess.run(cmd_install, capture_output=True, text=True, check=False)
    assert res_inst.returncode == 0, f"Install failed: {res_inst.stderr}"

    # Verify installation
    cmd_verify = [
        sys.executable, str(REPO_ROOT / "install.py"),
        "--agent", "antigravity",
        "--target", str(target),
        "--verify",
    ]
    res_ver = subprocess.run(cmd_verify, capture_output=True, text=True, check=False)
    assert res_ver.returncode == 0, f"Verify failed: {res_ver.stderr}"

    skill_scripts = target / ".agent" / "skills" / "repocraft" / "scripts"
    reports.mkdir(parents=True, exist_ok=True)

    # 3. Phase 1: Intel
    res_intel = subprocess.run(
        [sys.executable, str(skill_scripts / "repocraft_intel.py"), "--target", str(target), "--output", str(reports)],
        capture_output=True, text=True, check=False,
    )
    assert res_intel.returncode == 0, f"Intel failed: {res_intel.stderr}"

    # 4. Phase 2: Maintenance Audit
    res_maint = subprocess.run(
        [sys.executable, str(skill_scripts / "repocraft_maintenance.py"), "--target", str(target), "--reports", str(reports), "--mode", "audit"],
        capture_output=True, text=True, check=False,
    )
    assert res_maint.returncode == 0, f"Maintenance failed: {res_maint.stderr}"

    # 5. Phase 3: Security Audit
    res_sec = subprocess.run(
        [sys.executable, str(skill_scripts / "repocraft_security.py"), "--target", str(target), "--reports", str(reports), "--mode", "audit"],
        capture_output=True, text=True, check=False,
    )
    assert res_sec.returncode == 0, f"Security failed: {res_sec.stderr}"

    # 6. Phase 4: Repair Plan (read-only plan mode)
    res_repair = subprocess.run(
        [sys.executable, str(skill_scripts / "repocraft_repair.py"), "--target", str(target), "--reports", str(reports), "--mode", "plan"],
        capture_output=True, text=True, check=False,
    )
    assert res_repair.returncode == 0, f"Repair plan failed: {res_repair.stderr}"

    # 7. Phase 5: Git Inspect
    res_git = subprocess.run(
        [sys.executable, str(skill_scripts / "repocraft_git.py"), "inspect", "--target", str(target), "--reports", str(reports)],
        capture_output=True, text=True, check=False,
    )
    assert res_git.returncode == 0, f"Git inspect failed: {res_git.stderr}"

    # 8. Phase 6: Diagnostic Status
    res_status = subprocess.run(
        [sys.executable, str(skill_scripts / "repocraft_status.py"), "--target", str(target), "--reports", str(reports), "--json"],
        capture_output=True, text=True, check=False,
    )
    assert res_status.returncode == 0, f"Status failed: {res_status.stderr}"
    status_data = json.loads(res_status.stdout)

    # 9. Verify Phase output artifacts were generated
    assert (reports / "inventory.json").is_file(), "Missing Phase 1 inventory.json"
    assert (reports / "maintenance-plan.json").is_file(), "Missing Phase 2 maintenance-plan.json"
    assert (reports / "security-findings.json").is_file(), "Missing Phase 3 security-findings.json"
    assert (reports / "repair-plan.json").is_file(), "Missing Phase 4 repair-plan.json"
    assert (reports / "git-state.json").is_file(), "Missing Phase 5 git-state.json"

    # 10. Verify no Git staging occurred on the fixture
    res_staged = subprocess.run(["git", "diff", "--staged"], cwd=target, capture_output=True, text=True, check=True)
    assert res_staged.stdout.strip() == "", "RepoCraft unexpectedly staged files into git index!"

    # 11. Verify ALL original user source files remain 100% UNCHANGED
    for rel_path, expected_hash in user_file_hashes.items():
        user_p = target / rel_path
        assert user_p.is_file(), f"User file disappeared: {rel_path}"
        actual_hash = _sha256(user_p)
        assert actual_hash == expected_hash, f"User file modified: {rel_path}"

    return {
        "user_files_checked": len(user_file_hashes),
        "status": status_data.get("overall_status"),
        "inventory": json.loads((reports / "inventory.json").read_text(encoding="utf-8")),
        "repair_plan": json.loads((reports / "repair-plan.json").read_text(encoding="utf-8")),
    }


def test_fixture_01_minimal_python(tmp_path: Path):
    target = tmp_path / "python_repo"
    target.mkdir()
    _init_git(target)
    (target / "pyproject.toml").write_text("[project]\nname='mini'\nversion='0.1.0'\n", encoding="utf-8")
    (target / "app.py").write_text("def run():\n    return 42\n", encoding="utf-8")
    (target / "README.md").write_text("# Mini Python\nDescription.", encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=target, check=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=target, check=True)

    res = _run_repocraft_cycle(target, tmp_path / "reports")
    assert res["user_files_checked"] == 3


def test_fixture_02_javascript_typescript(tmp_path: Path):
    target = tmp_path / "js_ts_repo"
    target.mkdir()
    _init_git(target)
    (target / "package.json").write_text(json.dumps({"name": "web-pkg", "version": "1.0.0"}), encoding="utf-8")
    (target / "tsconfig.json").write_text(json.dumps({"compilerOptions": {"target": "ES6"}}), encoding="utf-8")
    (target / "index.ts").write_text("export const hello = (): string => 'world';\n", encoding="utf-8")
    (target / "README.md").write_text("# JS/TS Repo\n", encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=target, check=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=target, check=True)

    res = _run_repocraft_cycle(target, tmp_path / "reports")
    assert res["user_files_checked"] == 4


def test_fixture_03_java_kotlin(tmp_path: Path):
    target = tmp_path / "jvm_repo"
    target.mkdir()
    _init_git(target)
    (target / "pom.xml").write_text("<project><modelVersion>4.0.0</modelVersion></project>", encoding="utf-8")
    (target / "build.gradle.kts").write_text("plugins { kotlin(\"jvm\") }\n", encoding="utf-8")
    src = target / "src" / "main" / "java"
    src.mkdir(parents=True)
    (src / "App.java").write_text("public class App { public static void main(String[] args) {} }\n", encoding="utf-8")
    (target / "README.md").write_text("# JVM App\n", encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=target, check=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=target, check=True)

    res = _run_repocraft_cycle(target, tmp_path / "reports")
    assert res["user_files_checked"] == 4


def test_fixture_04_rust_go(tmp_path: Path):
    target = tmp_path / "sys_repo"
    target.mkdir()
    _init_git(target)
    (target / "Cargo.toml").write_text("[package]\nname = \"sys\"\nversion = \"0.1.0\"\n", encoding="utf-8")
    (target / "go.mod").write_text("module example.com/sys\n\ngo 1.20\n", encoding="utf-8")
    (target / "main.go").write_text("package main\nfunc main() {}\n", encoding="utf-8")
    (target / "README.md").write_text("# Rust & Go\n", encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=target, check=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=target, check=True)

    res = _run_repocraft_cycle(target, tmp_path / "reports")
    assert res["user_files_checked"] == 4


def test_fixture_05_static_docs(tmp_path: Path):
    target = tmp_path / "docs_site"
    target.mkdir()
    _init_git(target)
    (target / "index.html").write_text("<!DOCTYPE html><html><body><h1>Docs</h1></body></html>", encoding="utf-8")
    (target / "styles.css").write_text("body { font-family: sans-serif; }\n", encoding="utf-8")
    (target / "mkdocs.yml").write_text("site_name: Project Docs\n", encoding="utf-8")
    (target / "README.md").write_text("# Documentation Site\n", encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=target, check=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=target, check=True)

    res = _run_repocraft_cycle(target, tmp_path / "reports")
    assert res["user_files_checked"] == 4


def test_fixture_06_monorepo(tmp_path: Path):
    target = tmp_path / "monorepo_project"
    target.mkdir()
    _init_git(target)
    backend = target / "services" / "backend"
    backend.mkdir(parents=True)
    (backend / "requirements.txt").write_text("fastapi>=0.95.0\n", encoding="utf-8")
    (backend / "server.py").write_text("print('server')\n", encoding="utf-8")

    frontend = target / "services" / "frontend"
    frontend.mkdir(parents=True)
    (frontend / "package.json").write_text(json.dumps({"name": "fe"}), encoding="utf-8")
    (frontend / "App.tsx").write_text("export default function App() { return null; }\n", encoding="utf-8")

    (target / "README.md").write_text("# Monorepo\n", encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=target, check=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=target, check=True)

    res = _run_repocraft_cycle(target, tmp_path / "reports")
    assert res["user_files_checked"] == 5


def test_fixture_07_professional_structure(tmp_path: Path):
    target = tmp_path / "enterprise_repo"
    target.mkdir()
    _init_git(target)
    workflows = target / ".github" / "workflows"
    workflows.mkdir(parents=True)
    (workflows / "ci.yml").write_text("name: CI\non: push\njobs:\n  test:\n    runs-on: ubuntu-latest\n", encoding="utf-8")
    (target / "CONTRIBUTING.md").write_text("# Contributing\n", encoding="utf-8")
    (target / "SECURITY.md").write_text("# Security\n", encoding="utf-8")
    (target / "LICENSE").write_text("MIT License\n", encoding="utf-8")
    (target / "Makefile").write_text("test:\n\tpytest\n", encoding="utf-8")
    (target / "README.md").write_text("# Enterprise Repo\n", encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=target, check=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=target, check=True)

    res = _run_repocraft_cycle(target, tmp_path / "reports")
    assert res["user_files_checked"] == 6


def test_fixture_08_poor_docs(tmp_path: Path):
    target = tmp_path / "undocumented_repo"
    target.mkdir()
    _init_git(target)
    (target / "README.md").write_text("", encoding="utf-8")  # Empty readme
    (target / "raw_code.py").write_text("x = 1\n", encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=target, check=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=target, check=True)

    res = _run_repocraft_cycle(target, tmp_path / "reports")
    assert res["user_files_checked"] == 2


def test_fixture_09_uncommitted_modifications(tmp_path: Path):
    target = tmp_path / "dirty_repo"
    target.mkdir()
    _init_git(target)
    (target / "committed.txt").write_text("v1\n", encoding="utf-8")
    (target / "README.md").write_text("# Dirty Repo\n", encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=target, check=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=target, check=True)

    # Create uncommitted modifications
    (target / "committed.txt").write_text("v2 uncommitted edit\n", encoding="utf-8")
    (target / "untracked_secret.txt").write_text("user private note\n", encoding="utf-8")

    res = _run_repocraft_cycle(target, tmp_path / "reports")
    assert res["user_files_checked"] == 3
    assert (target / "untracked_secret.txt").read_text(encoding="utf-8") == "user private note\n"
    assert (target / "committed.txt").read_text(encoding="utf-8") == "v2 uncommitted edit\n"


def test_fixture_10_dynamic_imports_framework(tmp_path: Path):
    target = tmp_path / "dynamic_repo"
    target.mkdir()
    _init_git(target)
    (target / "plugins.py").write_text("import importlib\nmod = importlib.import_module('dynamic_worker')\n", encoding="utf-8")
    (target / "dynamic_worker.py").write_text("def work(): return True\n", encoding="utf-8")
    (target / "README.md").write_text("# Dynamic Plugin Repo\n", encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=target, check=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=target, check=True)

    res = _run_repocraft_cycle(target, tmp_path / "reports")
    assert res["user_files_checked"] == 3


def test_fixture_11_hidden_config_unusual_naming(tmp_path: Path):
    target = tmp_path / "unusual_names_repo"
    target.mkdir()
    _init_git(target)
    (target / ".dockerignore").write_text(".git\nnode_modules\n", encoding="utf-8")
    (target / ".env.example").write_text("PORT=8000\n", encoding="utf-8")
    (target / "app-v2.final.config.json").write_text(json.dumps({"env": "staging"}), encoding="utf-8")
    (target / "README.md").write_text("# Unusual Naming Repo\n", encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=target, check=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=target, check=True)

    res = _run_repocraft_cycle(target, tmp_path / "reports")
    assert res["user_files_checked"] == 4


def test_fixture_12_missing_tests_incomplete_ci(tmp_path: Path):
    target = tmp_path / "untested_repo"
    target.mkdir()
    _init_git(target)
    workflows = target / ".github" / "workflows"
    workflows.mkdir(parents=True)
    (workflows / "broken.yml").write_text("name: Broken\non: push\njobs:\n", encoding="utf-8")
    (target / "logic.py").write_text("def calculate(): return 100\n", encoding="utf-8")
    (target / "README.md").write_text("# Untested Repo\n", encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=target, check=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=target, check=True)

    res = _run_repocraft_cycle(target, tmp_path / "reports")
    assert res["user_files_checked"] == 3
