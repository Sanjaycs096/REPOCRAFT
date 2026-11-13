"""Module F1 — Test Discovery for RepoCraft Phase 3.

Discovers:
- Test frameworks (pytest, unittest, jest, vitest, mocha, cargo test, go test, maven, gradle)
- Test files and directories
- Empty test files
- Test commands configured in project manifests
"""
from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple

from .types import TestDiscoveryItem

IGNORE_DIRS = {
    ".git",
    "node_modules",
    "vendor",
    "venv",
    ".venv",
    "dist",
    "build",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
}

TEST_FILE_PATTERNS = [
    re.compile(r"^test_.*\.py$"),
    re.compile(r".*_test\.py$"),
    re.compile(r".*\.(?:test|spec)\.(?:js|jsx|ts|tsx)$"),
    re.compile(r".*_test\.go$"),
    re.compile(r".*Test\.java$"),
    re.compile(r".*Spec\.scala$"),
    re.compile(r".*_test\.rs$"),
]


def find_test_files(target_dir: str) -> Tuple[List[str], List[str]]:
    """Scan for test files and detect empty test files.

    Returns:
        (test_files, empty_test_files) relative to target_dir with forward slashes.
    """
    root = Path(target_dir).resolve()
    test_files: List[str] = []
    empty_test_files: List[str] = []

    for current_dir, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS and not d.startswith(".")]

        for file in files:
            file_path = Path(current_dir) / file
            rel_path = file_path.relative_to(root).as_posix()

            is_test = False
            # Check pattern match
            if any(p.match(file) for p in TEST_FILE_PATTERNS):
                is_test = True
            elif "/tests/" in f"/{rel_path}/" or "/test/" in f"/{rel_path}/" or "/__tests__/" in f"/{rel_path}/":
                if file.endswith((".py", ".js", ".ts", ".go", ".rs", ".java")):
                    is_test = True

            if is_test:
                test_files.append(rel_path)
                try:
                    content = file_path.read_text(encoding="utf-8", errors="replace").strip()
                    # Filter out comments to check if truly empty
                    code_lines = [
                        line for line in content.splitlines()
                        if line.strip() and not line.strip().startswith(("#", "//", "/*", "*"))
                    ]
                    if not code_lines:
                        empty_test_files.append(rel_path)
                except Exception:
                    pass

    return sorted(test_files), sorted(empty_test_files)


def discover_tests(target_dir: str) -> List[TestDiscoveryItem]:
    """Discover configured test runners, frameworks, and commands."""
    items: List[TestDiscoveryItem] = []
    root = Path(target_dir).resolve()
    test_files, _ = find_test_files(target_dir)
    file_count = len(test_files)

    # 1. Python ecosystem
    pyproject = root / "pyproject.toml"
    setup_cfg = root / "setup.cfg"
    pytest_ini = root / "pytest.ini"
    has_python_tests = any(f.endswith(".py") for f in test_files)

    if pytest_ini.exists():
        items.append(
            TestDiscoveryItem(
                framework="pytest",
                command="pytest",
                source_file="pytest.ini",
                test_type="unit",
                test_files_count=file_count,
            )
        )
    elif pyproject.exists():
        content = pyproject.read_text(encoding="utf-8", errors="replace")
        if "tool.pytest" in content or "pytest" in content:
            items.append(
                TestDiscoveryItem(
                    framework="pytest",
                    command="pytest",
                    source_file="pyproject.toml",
                    test_type="unit",
                    test_files_count=file_count,
                )
            )
    elif setup_cfg.exists() and "pytest" in setup_cfg.read_text(encoding="utf-8", errors="replace"):
        items.append(
            TestDiscoveryItem(
                framework="pytest",
                command="pytest",
                source_file="setup.cfg",
                test_type="unit",
                test_files_count=file_count,
            )
        )
    elif has_python_tests:
        # Default Python test framework
        items.append(
            TestDiscoveryItem(
                framework="pytest",
                command="pytest",
                source_file="tests/",
                test_type="unit",
                test_files_count=file_count,
            )
        )

    # 2. Node.js ecosystem
    pkg_json = root / "package.json"
    if pkg_json.exists():
        try:
            data = json.loads(pkg_json.read_text(encoding="utf-8", errors="replace"))
            scripts = data.get("scripts", {})
            dev_deps = data.get("devDependencies", {})
            deps = data.get("dependencies", {})
            all_deps = {**deps, **dev_deps}

            if "test" in scripts:
                cmd = scripts["test"]
                framework = "custom"
                if "jest" in cmd or "jest" in all_deps:
                    framework = "jest"
                elif "vitest" in cmd or "vitest" in all_deps:
                    framework = "vitest"
                elif "mocha" in cmd or "mocha" in all_deps:
                    framework = "mocha"

                items.append(
                    TestDiscoveryItem(
                        framework=framework,
                        command="npm test",
                        source_file="package.json",
                        test_type="unit",
                        test_files_count=file_count,
                    )
                )
            elif any(f in all_deps for f in ["jest", "vitest", "mocha"]):
                fw = "jest" if "jest" in all_deps else ("vitest" if "vitest" in all_deps else "mocha")
                items.append(
                    TestDiscoveryItem(
                        framework=fw,
                        command="npm test",
                        source_file="package.json",
                        test_type="unit",
                        test_files_count=file_count,
                    )
                )
        except Exception:
            pass

    # 3. Rust ecosystem
    if (root / "Cargo.toml").exists():
        items.append(
            TestDiscoveryItem(
                framework="cargo",
                command="cargo test",
                source_file="Cargo.toml",
                test_type="unit",
                test_files_count=file_count,
            )
        )

    # 4. Go ecosystem
    if (root / "go.mod").exists() or any(f.endswith(".go") for f in test_files):
        items.append(
            TestDiscoveryItem(
                framework="go test",
                command="go test ./...",
                source_file="go.mod" if (root / "go.mod").exists() else "main.go",
                test_type="unit",
                test_files_count=file_count,
            )
        )

    # 5. Java ecosystem
    if (root / "pom.xml").exists():
        items.append(
            TestDiscoveryItem(
                framework="maven",
                command="mvn test",
                source_file="pom.xml",
                test_type="unit",
                test_files_count=file_count,
            )
        )
    elif (root / "build.gradle").exists() or (root / "build.gradle.kts").exists():
        items.append(
            TestDiscoveryItem(
                framework="gradle",
                command="./gradlew test",
                source_file="build.gradle",
                test_type="unit",
                test_files_count=file_count,
            )
        )

    return items

