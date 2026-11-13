"""Comprehensive fixture-based test suite for RepoCraft Repository Intelligence Engine.

Covers all 20 required fixture scenarios plus CLI execution and immutability validation.
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

# Add skill/scripts to sys.path so engine can be imported directly
REPO_ROOT = Path(__file__).resolve().parents[1]
SKILL_SCRIPTS = REPO_ROOT / "skill" / "scripts"
if str(SKILL_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SKILL_SCRIPTS))

from engine.orchestrator import IntelligenceEngine
from engine.types import EvidenceLevel, FileCategory, Severity


def init_git_repo(path: Path) -> None:
    """Initialize a disposable git repository with an initial commit."""
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
    """Calculate sha256 of all files in directory to verify immutability."""
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


# 1. Empty repository
def test_01_empty_repository(tmp_path: Path):
    target = tmp_path / "empty-repo"
    target.mkdir()
    out = tmp_path / "reports"

    engine = IntelligenceEngine(target_dir=target, output_dir=out)
    report, files = engine.run()

    assert report.file_inventory_summary["total_files"] == 0
    assert report.languages == []
    assert report.frameworks == []
    assert files["inventory.json"].is_file()
    assert files["repository-overview.md"].is_file()
    assert files["repository-audit.md"].is_file()
    assert files["recommendations.json"].is_file()


# 2. JavaScript / TypeScript project
def test_02_javascript_typescript_project(tmp_path: Path):
    target = tmp_path / "ts-project"
    target.mkdir()
    (target / "package.json").write_text(
        json.dumps({
            "name": "sample-next-app",
            "dependencies": {"next": "^14.0.0", "react": "^18.2.0", "tailwindcss": "^3.0.0"},
            "devDependencies": {"typescript": "^5.0.0", "vitest": "^1.0.0", "eslint": "^8.0.0"},
            "scripts": {"dev": "next dev", "build": "next build", "test": "vitest", "lint": "eslint ."},
        })
    )
    (target / "tsconfig.json").write_text('{"compilerOptions": {}}')
    app_dir = target / "app"
    app_dir.mkdir()
    (app_dir / "page.tsx").write_text("export default function Page() { return <h1>Hello</h1>; }")
    (app_dir / "layout.tsx").write_text("export default function RootLayout({ children }: any) { return children; }")
    comp_dir = target / "components"
    comp_dir.mkdir()
    (comp_dir / "Button.tsx").write_text("export const Button = () => <button>Click</button>;")

    out = tmp_path / "reports"
    engine = IntelligenceEngine(target_dir=target, output_dir=out)
    report, files = engine.run()

    assert "TypeScript" in report.languages
    assert "Next.js" in report.frameworks
    assert "React" in report.frameworks
    assert "npm" in report.package_managers
    assert report.architecture["frontend"].classification.startswith("Next.js App Router")
    assert report.architecture["frontend"].evidence_level == EvidenceLevel.VERIFIED

    # Check discovered commands
    cmd_gates = {c.gate_name for c in report.discovered_commands}
    assert "Automated Tests" in cmd_gates or "Quality Check" in cmd_gates
    assert "Production Build" in cmd_gates
    assert "Type Checking" in cmd_gates


# 3. Python project
def test_03_python_project(tmp_path: Path):
    target = tmp_path / "py-project"
    target.mkdir()
    (target / "pyproject.toml").write_text(
        '[project]\nname = "fastapi-service"\nversion = "0.1.0"\n'
        '[tool.pytest.ini_options]\ntestpaths = ["tests"]\n'
        '[tool.ruff]\nline-length = 88\n'
    )
    (target / "main.py").write_text(
        "from fastapi import FastAPI\napp = FastAPI()\n@app.get('/')\ndef root(): return {'status': 'ok'}\n"
    )
    test_dir = target / "tests"
    test_dir.mkdir()
    (test_dir / "test_api.py").write_text("def test_ok(): assert True\n")

    out = tmp_path / "reports"
    engine = IntelligenceEngine(target_dir=target, output_dir=out)
    report, files = engine.run()

    assert "Python" in report.languages
    assert "FastAPI" in report.frameworks
    assert report.architecture["backend"].classification.startswith("FastAPI")
    assert any("pytest" in c.command for c in report.discovered_commands)
    assert any("ruff" in c.command for c in report.discovered_commands)


# 4. Java project
def test_04_java_project(tmp_path: Path):
    target = tmp_path / "java-project"
    target.mkdir()
    (target / "pom.xml").write_text(
        '<project xmlns="http://maven.apache.org/POM/4.0.0">\n'
        '  <modelVersion>4.0.0</modelVersion>\n'
        '  <groupId>com.example</groupId>\n'
        '  <artifactId>demo</artifactId>\n'
        '  <dependencies>\n'
        '    <dependency><groupId>org.springframework.boot</groupId><artifactId>spring-boot-starter-web</artifactId></dependency>\n'
        '    <dependency><groupId>org.junit.jupiter</groupId><artifactId>junit-jupiter</artifactId></dependency>\n'
        '  </dependencies>\n'
        '</project>\n'
    )
    src_dir = target / "src" / "main" / "java" / "com" / "example"
    src_dir.mkdir(parents=True)
    (src_dir / "DemoApplication.java").write_text(
        "package com.example;\nimport org.springframework.boot.autoconfigure.SpringBootApplication;\n"
        "@SpringBootApplication\npublic class DemoApplication {}\n"
    )

    out = tmp_path / "reports"
    engine = IntelligenceEngine(target_dir=target, output_dir=out)
    report, files = engine.run()

    assert "Java" in report.languages
    assert "Spring Boot" in report.frameworks
    assert "maven" in report.package_managers
    assert any("mvn test" in c.command for c in report.discovered_commands)


# 5. Multi-language repository
def test_05_multi_language_repository(tmp_path: Path):
    target = tmp_path / "multi-lang"
    target.mkdir()
    # Backend
    be_dir = target / "backend"
    be_dir.mkdir()
    (be_dir / "main.py").write_text("print('backend')")
    (target / "requirements.txt").write_text("fastapi==0.100.0\n")
    # Frontend
    fe_dir = target / "frontend"
    fe_dir.mkdir()
    (fe_dir / "index.ts").write_text("console.log('frontend');")

    out = tmp_path / "reports"
    engine = IntelligenceEngine(target_dir=target, output_dir=out)
    report, _ = engine.run()

    assert "Python" in report.languages
    assert "TypeScript" in report.languages


# 6. Monorepository
def test_06_monorepository(tmp_path: Path):
    target = tmp_path / "monorepo"
    target.mkdir()
    (target / "pnpm-workspace.yaml").write_text("packages:\n  - 'packages/*'\n  - 'apps/*'\n")
    pkg1 = target / "packages" / "ui"
    pkg1.mkdir(parents=True)
    (pkg1 / "package.json").write_text('{"name": "@mono/ui"}')
    (pkg1 / "index.ts").write_text("export const UI = 1;")

    app1 = target / "apps" / "web"
    app1.mkdir(parents=True)
    (app1 / "package.json").write_text('{"name": "@mono/web"}')
    (app1 / "index.ts").write_text("export const App = 1;")

    out = tmp_path / "reports"
    engine = IntelligenceEngine(target_dir=target, output_dir=out)
    report, _ = engine.run()

    assert report.is_monorepo is True
    assert "Monorepository" in report.detected_types
    assert "packages/ui" in report.monorepo_packages
    assert "apps/web" in report.monorepo_packages


# 7. Nested source directories
def test_07_nested_source_directories(tmp_path: Path):
    target = tmp_path / "nested-source"
    deep_dir = target / "src" / "core" / "services" / "v1" / "auth"
    deep_dir.mkdir(parents=True)
    (deep_dir / "token_handler.py").write_text("# Deep nested source\n")

    out = tmp_path / "reports"
    engine = IntelligenceEngine(target_dir=target, output_dir=out)
    report, _ = engine.run()

    assert "src" in report.source_directories
    inv_item = next(i for i in report.file_inventory_summary.get("category_counts", {}) if i == "source")
    assert report.file_inventory_summary["category_counts"]["source"] >= 1


# 8. Missing README
def test_08_missing_readme(tmp_path: Path):
    target = tmp_path / "no-readme"
    target.mkdir()
    (target / "main.py").write_text("print(1)")

    out = tmp_path / "reports"
    engine = IntelligenceEngine(target_dir=target, output_dir=out)
    report, _ = engine.run()

    readme_gov = report.governance["readme"]
    assert readme_gov.exists is False
    assert any(f.finding_id.startswith("FINDING-DOC") and "README" in f.evidence for f in report.findings)


# 9. Missing license
def test_09_missing_license(tmp_path: Path):
    target = tmp_path / "no-license"
    target.mkdir()
    (target / "README.md").write_text("# My Project\nDetailed explanation of the project.")
    (target / "main.py").write_text("print(1)")

    out = tmp_path / "reports"
    engine = IntelligenceEngine(target_dir=target, output_dir=out)
    report, _ = engine.run()

    lic_gov = report.governance["license"]
    assert lic_gov.exists is False
    assert any("LICENSE" in f.evidence for f in report.findings)


# 10. Missing test configuration
def test_10_missing_test_configuration(tmp_path: Path):
    target = tmp_path / "no-tests"
    target.mkdir()
    (target / "src").mkdir()
    (target / "src" / "app.py").write_text("def run(): pass")

    out = tmp_path / "reports"
    engine = IntelligenceEngine(target_dir=target, output_dir=out)
    report, _ = engine.run()

    assert any(f.category == "Quality Assurance" and f.severity == Severity.HIGH for f in report.findings)


# 11. Git repository with clean worktree
def test_11_git_clean_worktree(tmp_path: Path):
    target = tmp_path / "git-clean"
    target.mkdir()
    (target / "README.md").write_text("# Clean")
    init_git_repo(target)
    git_commit_all(target, "first commit")

    out = tmp_path / "reports"
    engine = IntelligenceEngine(target_dir=target, output_dir=out)
    report, _ = engine.run()

    assert report.git_baseline.is_git_repository is True
    assert report.git_baseline.pre_existing_modifications_count == 0
    assert len(report.git_baseline.staged_files) == 0
    assert len(report.git_baseline.unstaged_files) == 0
    assert len(report.git_baseline.untracked_files) == 0


# 12. Git repository with existing modifications
def test_12_git_existing_modifications(tmp_path: Path):
    target = tmp_path / "git-dirty"
    target.mkdir()
    (target / "file1.txt").write_text("base")
    (target / "file2.txt").write_text("base")
    init_git_repo(target)
    git_commit_all(target, "initial")

    # Staged change
    (target / "file1.txt").write_text("modified staged")
    git_bin = shutil.which("git")
    subprocess.run([git_bin, "add", "file1.txt"], cwd=str(target), check=True)

    # Unstaged change
    (target / "file2.txt").write_text("modified unstaged")

    out = tmp_path / "reports"
    engine = IntelligenceEngine(target_dir=target, output_dir=out)
    report, _ = engine.run()

    assert report.git_baseline.pre_existing_modifications_count >= 2
    assert "file1.txt" in report.git_baseline.staged_files
    assert "file2.txt" in report.git_baseline.unstaged_files
    assert report.git_baseline.warning is not None
    # Verify pre-existing content remained untouched
    assert (target / "file1.txt").read_text() == "modified staged"
    assert (target / "file2.txt").read_text() == "modified unstaged"


# 13. Git repository with untracked files
def test_13_git_untracked_files(tmp_path: Path):
    target = tmp_path / "git-untracked"
    target.mkdir()
    (target / "tracked.txt").write_text("tracked")
    init_git_repo(target)
    git_commit_all(target, "base")

    (target / "untracked_user_file.txt").write_text("user notes")

    out = tmp_path / "reports"
    engine = IntelligenceEngine(target_dir=target, output_dir=out)
    report, _ = engine.run()

    assert "untracked_user_file.txt" in report.git_baseline.untracked_files
    # Must remain intact
    assert (target / "untracked_user_file.txt").read_text() == "user notes"


# 14. Sensitive filenames such as .env (NO SECRET DISCLOSURE)
def test_14_sensitive_filenames_no_leak(tmp_path: Path):
    target = tmp_path / "sensitive-repo"
    target.mkdir()
    secret_marker_1 = "SUPER_SECRET_TOKEN_XYZ_987654321"
    secret_marker_2 = "SUPER_SECRET_PRIVATE_KEY_ABCD_1234"

    (target / ".env").write_text(f"API_KEY={secret_marker_1}\n")
    (target / ".env.production").write_text("DATABASE_URL=postgres://user:pass@db:5432/prod\n")
    (target / "id_rsa").write_text(f"-----BEGIN RSA PRIVATE KEY-----\n{secret_marker_2}\n-----END RSA PRIVATE KEY-----\n")
    (target / "main.py").write_text("print('hello')")

    out = tmp_path / "reports"
    engine = IntelligenceEngine(target_dir=target, output_dir=out)
    report, files = engine.run()

    # Verify sensitive files were detected with warning
    assert report.file_inventory_summary["sensitive_files_detected"] >= 2

    # Check ALL generated artifact files to verify secrets are NEVER exposed
    for art_name, art_path in files.items():
        content = art_path.read_text(encoding="utf-8")
        assert secret_marker_1 not in content, f"Secret leaked in {art_name}!"
        assert secret_marker_2 not in content, f"Secret leaked in {art_name}!"
        assert "postgres://user:pass" not in content, f"Database credential leaked in {art_name}!"


# 15. Generated directories exclusion
def test_15_generated_directories_exclusion(tmp_path: Path):
    target = tmp_path / "gen-dirs"
    target.mkdir()
    (target / "main.py").write_text("print(1)")
    # Generated build dirs
    (target / "dist").mkdir()
    (target / "dist" / "bundle.js").write_text("console.log('dist');")
    (target / "build").mkdir()
    (target / "build" / "output.js").write_text("console.log('build');")
    (target / ".next").mkdir()
    (target / ".next" / "cache.json").write_text("{}")
    (target / "coverage").mkdir()
    (target / "coverage" / "lcov.info").write_text("TN:")

    out = tmp_path / "reports"
    engine = IntelligenceEngine(target_dir=target, output_dir=out)
    report, _ = engine.run()

    excluded = report.file_inventory_summary["excluded_directories"]
    assert "dist" in excluded
    assert "build" in excluded
    assert ".next" in excluded
    assert "coverage" in excluded
    # Ensure generated files were not counted in regular inventory
    assert not any("dist/bundle.js" in p for p in report.configuration_files)


# 16. Vendor directories exclusion
def test_16_vendor_directories_exclusion(tmp_path: Path):
    target = tmp_path / "vendor-repo"
    target.mkdir()
    (target / "main.py").write_text("print(1)")
    # Vendor dirs
    (target / "node_modules" / "express").mkdir(parents=True)
    (target / "node_modules" / "express" / "index.js").write_text("module.exports = {};")
    (target / "vendor" / "bundle").mkdir(parents=True)
    (target / "vendor" / "bundle" / "lib.rb").write_text("class Lib; end")

    out = tmp_path / "reports"
    engine = IntelligenceEngine(target_dir=target, output_dir=out)
    report, _ = engine.run()

    excluded = report.file_inventory_summary["excluded_directories"]
    assert "node_modules" in excluded
    assert "vendor" in excluded


# 17. Symlinks and unusual file structures
def test_17_symlinks_and_unusual_structures(tmp_path: Path):
    target = tmp_path / "symlink-repo"
    target.mkdir()
    (target / "real_file.py").write_text("print('real')")

    # Try creating a symlink (if OS permissions allow)
    link_file = target / "symlink_file.py"
    try:
        link_file.symlink_to(target / "real_file.py")
    except (OSError, NotImplementedError):
        pass  # Windows developer mode might be disabled; non-fatal

    out = tmp_path / "reports"
    engine = IntelligenceEngine(target_dir=target, output_dir=out)
    report, _ = engine.run()
    assert report.file_inventory_summary["total_files"] >= 1


# 18. Malformed or incomplete manifests
def test_18_malformed_manifests(tmp_path: Path):
    target = tmp_path / "malformed-repo"
    target.mkdir()
    # Malformed package.json
    (target / "package.json").write_text("{ this is not valid json : [ }")
    (target / "pyproject.toml").write_text("")
    (target / "main.py").write_text("print('still works')")

    out = tmp_path / "reports"
    engine = IntelligenceEngine(target_dir=target, output_dir=out)
    report, _ = engine.run()

    # Engine must not crash and should still identify Python
    assert "Python" in report.languages


# 19. Large file inventories
def test_19_large_file_inventory(tmp_path: Path):
    target = tmp_path / "large-repo"
    target.mkdir()
    # Generate 500 files across multiple subdirectories
    for i in range(10):
        sub = target / f"dir_{i}"
        sub.mkdir()
        for j in range(50):
            (sub / f"module_{j}.py").write_text(f"x = {j}\n")

    out = tmp_path / "reports"
    engine = IntelligenceEngine(target_dir=target, output_dir=out)
    report, _ = engine.run()

    assert report.file_inventory_summary["total_files"] == 500
    assert report.file_inventory_summary["category_counts"]["source"] == 500


# 20. Output directory outside the target repository
def test_20_output_directory_outside_target_repository(tmp_path: Path):
    target = tmp_path / "project-dir"
    target.mkdir()
    (target / "app.py").write_text("print('hello')")

    # Custom outside location
    custom_out = tmp_path / "custom-external-reports"
    engine1 = IntelligenceEngine(target_dir=target, output_dir=custom_out)
    _, files1 = engine1.run()

    assert custom_out.is_dir()
    assert (custom_out / "inventory.json").is_file()
    # Ensure nothing was written into project-dir
    assert not (target / "inventory.json").exists()
    assert not (target / "repository-overview.md").exists()

    # Default outside location (target.parent / repocraft-reports)
    engine2 = IntelligenceEngine(target_dir=target)
    _, files2 = engine2.run()
    default_out = tmp_path / "repocraft-reports"
    assert default_out.is_dir()
    assert (default_out / "inventory.json").is_file()
    assert not (target / "repocraft-reports").exists()


# 21. CLI invocation end-to-end
def test_21_cli_invocation_end_to_end(tmp_path: Path):
    target = tmp_path / "cli-test-project"
    target.mkdir()
    (target / "README.md").write_text("# CLI Test App\nSimple test project for RepoCraft.")
    (target / "main.py").write_text("print('cli')")

    out = tmp_path / "cli-reports"
    cli_script = REPO_ROOT / "skill" / "scripts" / "repocraft_intel.py"

    proc = subprocess.run(
        [sys.executable, str(cli_script), "--target", str(target), "--output", str(out)],
        capture_output=True,
        text=True,
        check=False,
    )

    assert proc.returncode == 0
    assert "RepoCraft Repository Intelligence Report: cli-test-project" in proc.stdout
    assert "Static inspection complete" in proc.stdout
    assert (out / "inventory.json").is_file()
    assert (out / "repository-overview.md").is_file()
    assert (out / "repository-audit.md").is_file()
    assert (out / "recommendations.json").is_file()


# 22. Target project immutability
def test_22_target_project_unmodified(tmp_path: Path):
    target = tmp_path / "immutable-project"
    target.mkdir()
    (target / "README.md").write_text("# Immutability Test\nOriginal content.")
    (target / "app.py").write_text("import os\nprint('untouched')\n")
    (target / "config.json").write_text('{"setting": "original"}')

    hashes_before = hash_directory(target)

    out = tmp_path / "immutability-reports"
    engine = IntelligenceEngine(target_dir=target, output_dir=out)
    engine.run()

    hashes_after = hash_directory(target)

    assert hashes_before == hashes_after, "Target project files were modified during intelligence run!"

