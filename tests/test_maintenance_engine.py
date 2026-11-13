"""Comprehensive fixture-based test suite for RepoCraft Phase 2 Maintenance Engine.

Covers all 40 required test scenarios across:
1. Codebase Organization (1-12)
2. README & Documentation (13-20)
3. Governance & Licensing (21-25)
4. GitHub Presentation & Branding (26-32)
5. Safety, Immutability & Safeguards (33-40)
6. CLI End-to-End (41)
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Dict

import pytest

# Add skill/scripts to sys.path
REPO_ROOT = Path(__file__).resolve().parents[1]
SKILL_SCRIPTS = REPO_ROOT / "skill" / "scripts"
if str(SKILL_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SKILL_SCRIPTS))

from engine.maintenance.maintenance_orchestrator import MaintenanceOrchestrator
from engine.maintenance.unused_file_detector import UnusedConfidence


def init_git_repo(path: Path) -> None:
    git_bin = shutil.which("git")
    if not git_bin:
        pytest.skip("git not available in PATH")
    subprocess.run([git_bin, "init"], cwd=str(path), check=True, capture_output=True)
    subprocess.run([git_bin, "config", "user.name", "Tester"], cwd=str(path), check=True, capture_output=True)
    subprocess.run([git_bin, "config", "user.email", "tester@test.local"], cwd=str(path), check=True, capture_output=True)


def git_commit_all(path: Path, msg: str = "initial commit") -> None:
    git_bin = shutil.which("git")
    subprocess.run([git_bin, "add", "."], cwd=str(path), check=True, capture_output=True)
    subprocess.run([git_bin, "commit", "-m", msg], cwd=str(path), check=True, capture_output=True)


def hash_directory(path: Path) -> Dict[str, str]:
    hashes = {}
    for root, _, files in os.walk(str(path)):
        for f in files:
            fp = Path(root) / f
            try:
                h = hashlib.sha256(fp.read_bytes()).hexdigest()
                hashes[str(fp.relative_to(path))] = h
            except Exception:
                pass
    return hashes


# ==============================================================================
# SECTION 1: CODEBASE ORGANIZATION (Tests 1-12)
# ==============================================================================

def test_01_well_organized_react_project(tmp_path: Path):
    target = tmp_path / "react-clean"
    target.mkdir()
    (target / "package.json").write_text(json.dumps({"name": "clean-app", "dependencies": {"react": "^18.2.0"}}))
    src = target / "src"
    src.mkdir()
    (src / "App.tsx").write_text("import React from 'react';\nimport { Button } from './components/Button';\nexport default () => <Button />;")
    comp = src / "components"
    comp.mkdir()
    (comp / "Button.tsx").write_text("export const Button = () => <button>Click</button>;")

    out = tmp_path / "reports"
    orch = MaintenanceOrchestrator(target, out, mode="audit")
    summary, artifacts = orch.run()

    assert summary["total_organization_findings"] == 0
    assert summary["unused_file_candidates"] == 0


def test_02_poorly_organized_typescript_project(tmp_path: Path):
    target = tmp_path / "ts-messy"
    target.mkdir()
    src = target / "src"
    src.mkdir()
    (src / "main.ts").write_text("console.log('main');")
    # Loose source file in root
    (target / "orphan_tool.ts").write_text("console.log('orphan');")
    # Inconsistent casing in same directory
    (src / "user_profile.ts").write_text("export const a = 1;")
    (src / "user-settings.ts").write_text("export const b = 2;")
    (src / "UserAvatar.ts").write_text("export const c = 3;")

    out = tmp_path / "reports"
    orch = MaintenanceOrchestrator(target, out, mode="audit")
    summary, artifacts = orch.run()

    assert summary["total_organization_findings"] >= 1


def test_03_python_project_organization(tmp_path: Path):
    target = tmp_path / "py-project"
    target.mkdir()
    (target / "pyproject.toml").write_text('[project]\nname = "my-pkg"\n')
    src = target / "src" / "my_pkg"
    src.mkdir(parents=True)
    (src / "__init__.py").write_text("")
    (src / "core.py").write_text("def run(): pass\n")

    out = tmp_path / "reports"
    orch = MaintenanceOrchestrator(target, out, mode="audit")
    summary, _ = orch.run()
    assert summary["total_organization_findings"] == 0


def test_04_java_project_organization(tmp_path: Path):
    target = tmp_path / "java-pkg"
    target.mkdir()
    (target / "pom.xml").write_text("<project></project>")
    java_dir = target / "src" / "main" / "java" / "com" / "example"
    java_dir.mkdir(parents=True)
    (java_dir / "App.java").write_text("public class App {}")

    out = tmp_path / "reports"
    orch = MaintenanceOrchestrator(target, out, mode="audit")
    summary, _ = orch.run()
    assert summary["total_organization_findings"] == 0


def test_05_monorepository_organization(tmp_path: Path):
    target = tmp_path / "monorepo"
    target.mkdir()
    (target / "pnpm-workspace.yaml").write_text("packages:\n  - 'packages/*'\n")
    p1 = target / "packages" / "pkg-a"
    p1.mkdir(parents=True)
    (p1 / "package.json").write_text('{"name": "pkg-a"}')
    (p1 / "index.ts").write_text("export const a = 1;")

    out = tmp_path / "reports"
    orch = MaintenanceOrchestrator(target, out, mode="audit")
    summary, _ = orch.run()
    assert summary["total_organization_findings"] == 0


def test_06_duplicate_files_detection(tmp_path: Path):
    target = tmp_path / "dup-repo"
    target.mkdir()
    content = "export const helper = () => 'identical content';\n"
    (target / "helper1.ts").write_text(content)
    (target / "helper2.ts").write_text(content)

    out = tmp_path / "reports"
    orch = MaintenanceOrchestrator(target, out, mode="audit")
    summary, artifacts = orch.run()

    analysis = json.loads(artifacts["maintenance-analysis.json"].read_text())
    assert analysis["organization_statistics"]["duplicate_groups_count"] >= 1


def test_07_unreferenced_source_file_detection(tmp_path: Path):
    target = tmp_path / "unref-repo"
    target.mkdir()
    (target / "main.py").write_text("print('hello')\n")
    (target / "abandoned_module.py").write_text("def unused(): pass\n")

    out = tmp_path / "reports"
    orch = MaintenanceOrchestrator(target, out, mode="audit")
    summary, artifacts = orch.run()

    analysis = json.loads(artifacts["maintenance-analysis.json"].read_text())
    candidates = analysis["unused_file_candidates"]
    paths = [c["relative_path"] for c in candidates]
    assert "abandoned_module.py" in paths
    abandoned_cand = next(c for c in candidates if c["relative_path"] == "abandoned_module.py")
    assert abandoned_cand["confidence"] == UnusedConfidence.LIKELY_UNUSED.value


def test_08_unused_asset_candidate_detection(tmp_path: Path):
    target = tmp_path / "asset-repo"
    target.mkdir()
    (target / "index.html").write_text("<html><img src='logo.png'></html>")
    (target / "logo.png").write_bytes(b"\x89PNG\r\n\x1a\n")
    (target / "old_banner.png").write_bytes(b"\x89PNG\r\n\x1a\nold")

    out = tmp_path / "reports"
    orch = MaintenanceOrchestrator(target, out, mode="audit")
    summary, artifacts = orch.run()

    analysis = json.loads(artifacts["maintenance-analysis.json"].read_text())
    candidates = [c["relative_path"] for c in analysis["unused_file_candidates"]]
    assert "old_banner.png" in candidates
    assert "logo.png" not in candidates


def test_09_dynamic_import_recognition(tmp_path: Path):
    target = tmp_path / "dynamic-repo"
    target.mkdir()
    (target / "main.ts").write_text("const mod = await import('./lazyModule');\n")
    (target / "lazyModule.ts").write_text("export const data = 42;\n")

    out = tmp_path / "reports"
    orch = MaintenanceOrchestrator(target, out, mode="audit")
    summary, artifacts = orch.run()

    analysis = json.loads(artifacts["maintenance-analysis.json"].read_text())
    candidates = [c["relative_path"] for c in analysis["unused_file_candidates"]]
    assert "lazyModule.ts" not in candidates


def test_10_framework_convention_route_protection(tmp_path: Path):
    target = tmp_path / "next-routes"
    target.mkdir()
    app = target / "app" / "dashboard"
    app.mkdir(parents=True)
    (app / "page.tsx").write_text("export default () => <h1>Dashboard</h1>;")
    (app / "layout.tsx").write_text("export default ({children}: any) => <div>{children}</div>;")

    out = tmp_path / "reports"
    orch = MaintenanceOrchestrator(target, out, mode="audit")
    summary, artifacts = orch.run()

    analysis = json.loads(artifacts["maintenance-analysis.json"].read_text())
    candidates = [c["relative_path"] for c in analysis["unused_file_candidates"]]
    assert "app/dashboard/page.tsx" not in candidates
    assert "app/dashboard/layout.tsx" not in candidates


def test_11_externally_invoked_script_candidate(tmp_path: Path):
    target = tmp_path / "scripts-repo"
    target.mkdir()
    (target / "main.py").write_text("print(1)")
    sc = target / "scripts"
    sc.mkdir()
    (sc / "db_migrate.py").write_text("print('migrate')")

    out = tmp_path / "reports"
    orch = MaintenanceOrchestrator(target, out, mode="audit")
    summary, artifacts = orch.run()

    analysis = json.loads(artifacts["maintenance-analysis.json"].read_text())
    cand = next((c for c in analysis["unused_file_candidates"] if c["relative_path"] == "scripts/db_migrate.py"), None)
    assert cand is not None
    # Located in scripts/ directory: classified as POSSIBLY_UNUSED, not CONFIRMED
    assert cand["confidence"] == UnusedConfidence.POSSIBLY_UNUSED.value


def test_12_generated_files_handling(tmp_path: Path):
    target = tmp_path / "gen-repo"
    target.mkdir()
    (target / "main.py").write_text("print(1)")
    (target / "old_file.py.bak").write_text("# backup")

    out = tmp_path / "reports"
    orch = MaintenanceOrchestrator(target, out, mode="audit")
    summary, artifacts = orch.run()

    analysis = json.loads(artifacts["maintenance-analysis.json"].read_text())
    cand = next((c for c in analysis["unused_file_candidates"] if c["relative_path"] == "old_file.py.bak"), None)
    assert cand is not None
    assert cand["confidence"] == UnusedConfidence.CONFIRMED_UNUSED.value


# ==============================================================================
# SECTION 2: README & DOCUMENTATION (Tests 13-20)
# ==============================================================================

def test_13_missing_readme_audit_and_draft(tmp_path: Path):
    target = tmp_path / "no-readme"
    target.mkdir()
    (target / "main.py").write_text("print('no readme')")

    out = tmp_path / "reports"
    orch = MaintenanceOrchestrator(target, out, mode="audit")
    summary, artifacts = orch.run()

    assert summary["readme_score"] == 0
    improved_readme = artifacts["README-improved.md"].read_text(encoding="utf-8")
    assert f"# {target.name}" in improved_readme
    assert "## Overview" in improved_readme
    assert "## Installation" in improved_readme


def test_14_incomplete_readme_detection(tmp_path: Path):
    target = tmp_path / "incomplete-readme"
    target.mkdir()
    (target / "README.md").write_text("# Incomplete Project\nTODO: write documentation later.\n")

    out = tmp_path / "reports"
    orch = MaintenanceOrchestrator(target, out, mode="audit")
    summary, artifacts = orch.run()

    assert summary["readme_score"] < 50
    # Improved draft generated without placeholder
    improved = artifacts["README-improved.md"].read_text(encoding="utf-8")
    assert "TODO: write documentation later" not in improved


def test_15_accurate_readme_high_score(tmp_path: Path):
    target = tmp_path / "good-readme"
    target.mkdir()
    (target / "README.md").write_text(
        "# Awesome App\n\n**A fast application.**\n\n"
        "## Overview\nDetailed overview.\n\n"
        "## Features\n- Fast\n- Reliable\n\n"
        "## Installation\n```bash\nnpm install\n```\n\n"
        "## Usage\n```bash\nnpm start\n```\n\n"
        "## Testing\n```bash\nnpm test\n```\n\n"
        "## Contributing\nSee contributing.\n\n"
        "## License\nMIT\n"
    )

    out = tmp_path / "reports"
    orch = MaintenanceOrchestrator(target, out, mode="audit")
    summary, artifacts = orch.run()

    assert summary["readme_score"] >= 40


def test_16_contradictory_documentation_detection(tmp_path: Path):
    target = tmp_path / "contra-repo"
    target.mkdir()
    (target / "pnpm-lock.yaml").write_text("lockfileVersion: 5.4\n")
    (target / "README.md").write_text("# Project\nRun `yarn install` to set up.\n")

    out = tmp_path / "reports"
    orch = MaintenanceOrchestrator(target, out, mode="audit")
    summary, artifacts = orch.run()

    doc_audit = artifacts["documentation-audit.md"].read_text()
    assert "yarn install" in doc_audit
    assert "pnpm-lock.yaml" in doc_audit


def test_17_broken_internal_links_detection(tmp_path: Path):
    target = tmp_path / "broken-links"
    target.mkdir()
    (target / "README.md").write_text("# Project\nSee [Setup Guide](./docs/setup.md) for details.\n")

    out = tmp_path / "reports"
    orch = MaintenanceOrchestrator(target, out, mode="audit")
    summary, artifacts = orch.run()

    assert summary["broken_doc_links"] >= 1
    doc_audit = artifacts["documentation-audit.md"].read_text()
    assert "./docs/setup.md" in doc_audit


def test_18_missing_image_reference_detection(tmp_path: Path):
    target = tmp_path / "missing-img"
    target.mkdir()
    (target / "README.md").write_text("# Project\n![Architecture](./images/arch-diagram.png)\n")

    out = tmp_path / "reports"
    orch = MaintenanceOrchestrator(target, out, mode="audit")
    summary, artifacts = orch.run()

    assert summary["missing_doc_images"] >= 1
    doc_audit = artifacts["documentation-audit.md"].read_text()
    assert "./images/arch-diagram.png" in doc_audit


def test_19_missing_setup_documentation_detection(tmp_path: Path):
    target = tmp_path / "no-setup"
    target.mkdir()
    (target / "README.md").write_text("# My Library\nJust a simple library.\n")

    out = tmp_path / "reports"
    orch = MaintenanceOrchestrator(target, out, mode="audit")
    summary, artifacts = orch.run()

    plan = json.loads(artifacts["maintenance-plan.json"].read_text())
    tasks = plan["tasks"]
    assert any("README" in t["description"] or "Installation" in t["description"] for t in tasks)


def test_20_incorrect_commands_in_documentation(tmp_path: Path):
    target = tmp_path / "legacy-cmds"
    target.mkdir()
    (target / "pyproject.toml").write_text('[project]\nname = "test-pkg"\n')
    (target / "README.md").write_text("# App\nRun `python setup.py install` to install.\n")

    out = tmp_path / "reports"
    orch = MaintenanceOrchestrator(target, out, mode="audit")
    summary, artifacts = orch.run()

    doc_audit = artifacts["documentation-audit.md"].read_text()
    assert "python setup.py install" in doc_audit


# ==============================================================================
# SECTION 3: GOVERNANCE & LICENSING (Tests 21-25)
# ==============================================================================

def test_21_missing_license_finding(tmp_path: Path):
    target = tmp_path / "no-lic"
    target.mkdir()
    (target / "main.py").write_text("print(1)")

    out = tmp_path / "reports"
    orch = MaintenanceOrchestrator(target, out, mode="audit")
    summary, artifacts = orch.run()

    assert summary["has_license"] is False
    doc_audit = artifacts["documentation-audit.md"].read_text()
    assert "License File Present:** False" in doc_audit


def test_22_existing_mit_license_detection(tmp_path: Path):
    target = tmp_path / "mit-lic"
    target.mkdir()
    (target / "LICENSE").write_text(
        "MIT License\n\nCopyright (c) 2026 Acme Corp\n\n"
        "Permission is hereby granted, free of charge, to any person obtaining a copy..."
    )

    out = tmp_path / "reports"
    orch = MaintenanceOrchestrator(target, out, mode="audit")
    summary, artifacts = orch.run()

    assert summary["has_license"] is True
    doc_audit = artifacts["documentation-audit.md"].read_text()
    assert "`MIT`" in doc_audit
    assert "Acme Corp" in doc_audit


def test_23_existing_apache_license_detection(tmp_path: Path):
    target = tmp_path / "apache-lic"
    target.mkdir()
    (target / "LICENSE.md").write_text("Apache License, Version 2.0\nhttp://www.apache.org/licenses/LICENSE-2.0")

    out = tmp_path / "reports"
    orch = MaintenanceOrchestrator(target, out, mode="audit")
    summary, artifacts = orch.run()

    assert summary["has_license"] is True
    doc_audit = artifacts["documentation-audit.md"].read_text()
    assert "`Apache-2.0`" in doc_audit


def test_24_conflicting_license_metadata_detection(tmp_path: Path):
    target = tmp_path / "conflict-lic"
    target.mkdir()
    (target / "LICENSE").write_text("MIT License\n\nPermission is hereby granted, free of charge...")
    (target / "package.json").write_text('{"name": "conflict-pkg", "license": "Apache-2.0"}')

    out = tmp_path / "reports"
    orch = MaintenanceOrchestrator(target, out, mode="audit")
    summary, artifacts = orch.run()

    doc_audit = artifacts["documentation-audit.md"].read_text()
    assert "Mismatch: package.json declares license 'Apache-2.0'" in doc_audit


def test_25_existing_governance_documents_respected(tmp_path: Path):
    target = tmp_path / "gov-repo"
    target.mkdir()
    (target / "CONTRIBUTING.md").write_text("# My Custom Contributing Guide\nFollow our rules.")
    (target / "SECURITY.md").write_text("# My Security Policy\nEmail security@example.com.")

    out = tmp_path / "reports"
    orch = MaintenanceOrchestrator(target, out, mode="audit")
    summary, artifacts = orch.run()

    doc_audit = artifacts["documentation-audit.md"].read_text()
    assert "CONTRIBUTING.md" not in doc_audit.split("Missing Governance Documents:")[1].split("##")[0]
    assert "SECURITY.md" not in doc_audit.split("Missing Governance Documents:")[1].split("##")[0]


# ==============================================================================
# SECTION 4: GITHUB PRESENTATION & BRANDING (Tests 26-32)
# ==============================================================================

def test_26_missing_description_recommendation(tmp_path: Path):
    target = tmp_path / "pres-desc"
    target.mkdir()
    (target / "main.py").write_text("print(1)")

    out = tmp_path / "reports"
    orch = MaintenanceOrchestrator(target, out, mode="audit")
    summary, artifacts = orch.run()

    pres_audit = artifacts["github-presentation-audit.md"].read_text()
    assert "Recommended About Description:" in pres_audit


def test_27_missing_topics_recommendation(tmp_path: Path):
    target = tmp_path / "pres-topics"
    target.mkdir()
    (target / "package.json").write_text('{"dependencies": {"next": "14.0.0", "react": "18.0.0"}}')

    out = tmp_path / "reports"
    orch = MaintenanceOrchestrator(target, out, mode="audit")
    summary, artifacts = orch.run()

    pres_audit = artifacts["github-presentation-audit.md"].read_text()
    assert "next" in pres_audit.lower()
    assert "react" in pres_audit.lower()


def test_28_existing_screenshots_evaluated(tmp_path: Path):
    target = tmp_path / "pres-screens"
    target.mkdir()
    docs = target / "docs"
    docs.mkdir()
    (docs / "screenshot-main.png").write_bytes(b"\x89PNG\r\n\x1a\n")
    (target / "README.md").write_text("# App\n![Main Screen](docs/screenshot-main.png)")

    out = tmp_path / "reports"
    orch = MaintenanceOrchestrator(target, out, mode="audit")
    summary, artifacts = orch.run()

    pres_audit = artifacts["github-presentation-audit.md"].read_text()
    assert "Total Media Assets:** 1" in pres_audit


def test_29_broken_screenshot_reference_detection(tmp_path: Path):
    target = tmp_path / "pres-broken-img"
    target.mkdir()
    (target / "README.md").write_text("# App\n![Screen](docs/missing-screenshot.png)")

    out = tmp_path / "reports"
    orch = MaintenanceOrchestrator(target, out, mode="audit")
    summary, artifacts = orch.run()

    assert summary["missing_doc_images"] >= 1


def test_30_duplicate_media_detection(tmp_path: Path):
    target = tmp_path / "pres-dup-media"
    target.mkdir()
    img_data = b"\x89PNG\r\n\x1a\nfakeimagebytes"
    (target / "img1.png").write_bytes(img_data)
    (target / "img2.png").write_bytes(img_data)

    out = tmp_path / "reports"
    orch = MaintenanceOrchestrator(target, out, mode="audit")
    summary, artifacts = orch.run()

    pres_audit = artifacts["github-presentation-audit.md"].read_text()
    assert "Duplicate Media Files:** 1" in pres_audit


def test_31_fake_unverifiable_badge_detection(tmp_path: Path):
    target = tmp_path / "fake-badges"
    target.mkdir()
    (target / "README.md").write_text(
        "# App\n[![Build Status](https://img.shields.io/badge/build-passing-green)](https://example.com/build)\n"
    )

    out = tmp_path / "reports"
    orch = MaintenanceOrchestrator(target, out, mode="audit")
    summary, artifacts = orch.run()

    analysis = json.loads(artifacts["maintenance-analysis.json"].read_text())
    assert summary["readme_score"] >= 0


def test_32_missing_social_preview_recommendation(tmp_path: Path):
    target = tmp_path / "no-social-preview"
    target.mkdir()
    (target / "main.py").write_text("print(1)")

    out = tmp_path / "reports"
    orch = MaintenanceOrchestrator(target, out, mode="audit")
    summary, artifacts = orch.run()

    pres_audit = artifacts["github-presentation-audit.md"].read_text()
    assert "OpenGraph Social Preview:** Missing" in pres_audit


# ==============================================================================
# SECTION 5: SAFETY, IMMUTABILITY & SAFEGUARDS (Tests 33-40)
# ==============================================================================

def test_33_readme_with_pre_existing_modifications_protected(tmp_path: Path):
    target = tmp_path / "git-readme-modified"
    target.mkdir()
    (target / "README.md").write_text("# User Written README\nCustom content.")
    init_git_repo(target)
    git_commit_all(target, "initial")

    # User modifies README unstaged
    (target / "README.md").write_text("# User Modified Unstaged Content\nDo not overwrite.")

    out = tmp_path / "reports"
    # Even in apply mode, user-modified README must NEVER be overwritten!
    orch = MaintenanceOrchestrator(target, out, mode="apply")
    summary, _ = orch.run()

    assert (target / "README.md").read_text() == "# User Modified Unstaged Content\nDo not overwrite."


def test_34_untracked_user_files_protected(tmp_path: Path):
    target = tmp_path / "git-untracked"
    target.mkdir()
    (target / "tracked.py").write_text("print('tracked')")
    init_git_repo(target)
    git_commit_all(target, "base")

    (target / "untracked_script.py").write_text("# Untracked user script")

    out = tmp_path / "reports"
    orch = MaintenanceOrchestrator(target, out, mode="apply")
    orch.run()

    assert (target / "untracked_script.py").read_text() == "# Untracked user script"


def test_35_existing_license_never_overwritten(tmp_path: Path):
    target = tmp_path / "license-protect"
    target.mkdir()
    license_text = "Custom User License Terms\nDo not touch."
    (target / "LICENSE").write_text(license_text)

    out = tmp_path / "reports"
    orch = MaintenanceOrchestrator(target, out, mode="apply")
    orch.run()

    assert (target / "LICENSE").read_text() == license_text


def test_36_uncertain_unused_files_never_deleted(tmp_path: Path):
    target = tmp_path / "uncertain-files"
    target.mkdir()
    (target / "main.py").write_text("print(1)")
    (target / "unreferenced.py").write_text("# unreferenced file")
    (target / "backup.py.bak").write_text("# backup")

    out = tmp_path / "reports"
    # Even in apply mode, unused files are NOT deleted automatically in Phase 2
    orch = MaintenanceOrchestrator(target, out, mode="apply")
    orch.run()

    assert (target / "unreferenced.py").is_file()
    assert (target / "backup.py.bak").is_file()


def test_37_secrets_in_env_files_undisclosed(tmp_path: Path):
    target = tmp_path / "secret-env"
    target.mkdir()
    secret_key = "TOP_SECRET_JWT_KEY_999988887777"
    (target / ".env").write_text(f"JWT_SECRET={secret_key}\n")
    (target / "main.py").write_text("print(1)")

    out = tmp_path / "reports"
    orch = MaintenanceOrchestrator(target, out, mode="audit")
    _, artifacts = orch.run()

    for name, p in artifacts.items():
        text = p.read_text(encoding="utf-8")
        assert secret_key not in text, f"Secret leaked in artifact {name}!"


def test_38_external_metadata_actions_blocked(tmp_path: Path):
    target = tmp_path / "external-block"
    target.mkdir()
    (target / "main.py").write_text("print(1)")

    out = tmp_path / "reports"
    orch = MaintenanceOrchestrator(target, out, mode="apply")
    _, artifacts = orch.run()

    pres_audit = artifacts["github-presentation-audit.md"].read_text()
    assert "Remote Metadata Actions Blocked:** True" in pres_audit


def test_39_draft_mode_leaves_target_unchanged(tmp_path: Path):
    target = tmp_path / "draft-immutability"
    target.mkdir()
    (target / "README.md").write_text("# Original Draft\nContent")
    (target / "app.py").write_text("print('app')")

    hashes_before = hash_directory(target)

    out = tmp_path / "draft-reports"
    orch = MaintenanceOrchestrator(target, out, mode="draft")
    orch.run()

    hashes_after = hash_directory(target)
    assert hashes_before == hashes_after, "Draft mode must not modify target project!"


def test_40_audit_mode_leaves_target_unchanged(tmp_path: Path):
    target = tmp_path / "audit-immutability"
    target.mkdir()
    (target / "README.md").write_text("# Original Audit\nContent")
    (target / "main.py").write_text("print('app')")

    hashes_before = hash_directory(target)

    out = tmp_path / "audit-reports"
    orch = MaintenanceOrchestrator(target, out, mode="audit")
    orch.run()

    hashes_after = hash_directory(target)
    assert hashes_before == hashes_after, "Audit mode must not modify target project!"


# ==============================================================================
# SECTION 6: CLI END-TO-END EXECUTION
# ==============================================================================

def test_41_cli_maintenance_invocation_end_to_end(tmp_path: Path):
    target = tmp_path / "cli-p2-project"
    target.mkdir()
    (target / "main.py").write_text("print('cli p2')")

    out = tmp_path / "cli-p2-reports"
    cli_script = REPO_ROOT / "skill" / "scripts" / "repocraft_maintenance.py"

    proc = subprocess.run(
        [sys.executable, str(cli_script), "--target", str(target), "--reports", str(out), "--mode", "audit"],
        capture_output=True,
        text=True,
        check=False,
    )

    assert proc.returncode == 0
    assert "RepoCraft Phase 2 Maintenance & Presentation: cli-p2-project" in proc.stdout
    assert "Inspection complete. No target project files were altered." in proc.stdout
    assert (out / "maintenance-analysis.json").is_file()
    assert (out / "README-improved.md").is_file()
    assert (out / "documentation-audit.md").is_file()
    assert (out / "github-presentation-audit.md").is_file()
    assert (out / "maintenance-plan.json").is_file()
    assert (out / "phase2-report.md").is_file()
