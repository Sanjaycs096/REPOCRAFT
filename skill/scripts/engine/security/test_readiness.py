"""Module F2 — Test Readiness Assessor for RepoCraft Phase 3.

Evaluates test suite health and execution readiness:
- Detects missing test suite (no test files found)
- Identifies empty test files
- Checks dependency presence (e.g. node_modules, venv)
- Determines if test execution is blocked or ready
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from .test_discovery import discover_tests, find_test_files
from .types import TestDiscoveryItem


def assess_test_readiness(target_dir: str) -> Dict[str, Any]:
    """Assess readiness of the test suite in target repository."""
    root = Path(target_dir).resolve()
    test_files, empty_test_files = find_test_files(target_dir)
    discovered_tests = discover_tests(target_dir)

    has_test_files = len(test_files) > 0
    has_test_framework = len(discovered_tests) > 0

    # Check dependencies presence
    missing_dependencies: List[str] = []

    # Node check
    if (root / "package.json").exists():
        if not (root / "node_modules").is_dir():
            missing_dependencies.append("Node.js 'node_modules' directory is missing; dependencies not installed.")

    # Python check
    if any(f.endswith(".py") for f in test_files) or (root / "pyproject.toml").exists():
        has_venv = any((root / v).is_dir() for v in [".venv", "venv", "env"])
        if not has_venv and not os.environ.get("VIRTUAL_ENV"):
            # Informational note: no local venv found in repo
            pass

    # Overall readiness determination
    is_ready = True
    blockers: List[str] = []

    if not has_test_files and not has_test_framework:
        is_ready = False
        blockers.append("No test files or test framework configuration discovered in repository.")
    elif not has_test_files and has_test_framework:
        is_ready = False
        blockers.append("Test framework is configured but zero test files were found.")

    if missing_dependencies:
        # If node_modules is missing for node tests, it blocks execution
        for d in missing_dependencies:
            blockers.append(d)

    return {
        "is_ready_for_execution": is_ready and len(blockers) == 0,
        "total_test_files": len(test_files),
        "test_files": test_files,
        "empty_test_files_count": len(empty_test_files),
        "empty_test_files": empty_test_files,
        "discovered_frameworks": [item.to_dict() for item in discovered_tests],
        "candidate_commands": [item.command for item in discovered_tests],
        "missing_dependencies": missing_dependencies,
        "blockers": blockers,
    }

