"""Testing and CI/CD discovery module for RepoCraft.

Extracts test frameworks, linters, formatters, typecheckers, build tools,
and CI/CD pipelines directly from manifests, scripts, and workflows.
Commands are discovered and recorded as NOT VERIFIED; no commands are run.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, List, Set, Tuple

from .discovery import parse_json_manifest, safe_read_text
from .types import DiscoveredCommand, FileInventoryItem


class TestingAndCIDiscovery:
    """Discovers configured test suites, linting tools, and CI/CD workflows."""

    def __init__(self, repo_root: Path, inventory: List[FileInventoryItem]):
        self.repo_root = repo_root
        self.inventory = inventory
        self.paths_set: Set[str] = {item.relative_path for item in inventory}

    def discover(self) -> Tuple[List[DiscoveredCommand], List[str]]:
        """Discover commands and CI workflow paths without executing them."""
        commands: List[DiscoveredCommand] = []
        workflows: List[str] = []

        # 1. Inspect package.json scripts
        pkg_json = self.repo_root / "package.json"
        if pkg_json.is_file():
            data, _ = parse_json_manifest(pkg_json)
            if data and isinstance(data.get("scripts"), dict):
                scripts = data["scripts"]
                for script_name, cmd_val in scripts.items():
                    if not isinstance(cmd_val, str):
                        continue
                    gate = self._classify_npm_script(script_name, cmd_val)
                    if gate:
                        commands.append(
                            DiscoveredCommand(
                                gate_name=gate,
                                command=f"npm run {script_name}",
                                source_file="package.json",
                                verified=False,
                            )
                        )

        # 2. Inspect TypeScript config
        if "tsconfig.json" in self.paths_set:
            commands.append(
                DiscoveredCommand(
                    gate_name="Type Checking",
                    command="npx tsc --noEmit",
                    source_file="tsconfig.json",
                    verified=False,
                )
            )

        # 3. Inspect Python configuration (pytest, ruff, black, mypy, flake8)
        pyproject = self.repo_root / "pyproject.toml"
        if pyproject.is_file():
            txt = safe_read_text(pyproject)
            if "[tool.pytest" in txt or "pytest" in txt:
                commands.append(
                    DiscoveredCommand(
                        gate_name="Unit / Integration Tests",
                        command="pytest",
                        source_file="pyproject.toml",
                        verified=False,
                    )
                )
            if "[tool.ruff" in txt:
                commands.append(
                    DiscoveredCommand(
                        gate_name="Linting & Formatting",
                        command="ruff check .",
                        source_file="pyproject.toml",
                        verified=False,
                    )
                )
            if "[tool.black" in txt:
                commands.append(
                    DiscoveredCommand(
                        gate_name="Formatting",
                        command="black --check .",
                        source_file="pyproject.toml",
                        verified=False,
                    )
                )
            if "[tool.mypy" in txt:
                commands.append(
                    DiscoveredCommand(
                        gate_name="Type Checking",
                        command="mypy .",
                        source_file="pyproject.toml",
                        verified=False,
                    )
                )

        if "pytest.ini" in self.paths_set or "tests" in [p.split("/")[0] for p in self.paths_set if any(p.endswith(ext) for ext in (".py",))]:
            if not any(c.command == "pytest" for c in commands):
                commands.append(
                    DiscoveredCommand(
                        gate_name="Unit / Integration Tests",
                        command="pytest",
                        source_file="pytest.ini" if "pytest.ini" in self.paths_set else "tests/",
                        verified=False,
                    )
                )

        # 4. Inspect Java / Kotlin build tools
        if "pom.xml" in self.paths_set:
            commands.append(
                DiscoveredCommand(
                    gate_name="Build & Tests",
                    command="mvn test",
                    source_file="pom.xml",
                    verified=False,
                )
            )
        if "build.gradle" in self.paths_set or "build.gradle.kts" in self.paths_set:
            gradle_wrapper = "./gradlew" if (self.repo_root / "gradlew").is_file() or (self.repo_root / "gradlew.bat").is_file() else "gradle"
            commands.append(
                DiscoveredCommand(
                    gate_name="Build & Tests",
                    command=f"{gradle_wrapper} test",
                    source_file="build.gradle",
                    verified=False,
                )
            )

        # 5. Inspect Go
        if "go.mod" in self.paths_set:
            commands.append(
                DiscoveredCommand(
                    gate_name="Unit Tests",
                    command="go test ./...",
                    source_file="go.mod",
                    verified=False,
                )
            )

        # 6. Inspect Rust
        if "Cargo.toml" in self.paths_set:
            commands.append(
                DiscoveredCommand(
                    gate_name="Unit & Integration Tests",
                    command="cargo test",
                    source_file="Cargo.toml",
                    verified=False,
                )
            )

        # 7. Inspect Makefile targets
        makefile = self.repo_root / "Makefile"
        if makefile.is_file():
            text = safe_read_text(makefile)
            for target in ("test", "check", "lint", "build", "format"):
                if re.search(rf"^{target}:", text, re.MULTILINE):
                    commands.append(
                        DiscoveredCommand(
                            gate_name=f"Make {target.capitalize()}",
                            command=f"make {target}",
                            source_file="Makefile",
                            verified=False,
                        )
                    )

        # 8. Discover CI/CD Workflows
        for item in self.inventory:
            rel = item.relative_path
            rel_lower = rel.lower()
            if rel_lower.startswith(".github/workflows/") and rel_lower.endswith((".yml", ".yaml")):
                workflows.append(rel)
            elif rel_lower in (
                ".gitlab-ci.yml",
                ".circleci/config.yml",
                "bitbucket-pipelines.yml",
                "azure-pipelines.yml",
                "jenkinsfile",
            ):
                workflows.append(rel)

        return commands, sorted(workflows)

    def _classify_npm_script(self, name: str, cmd: str) -> str:
        nl = name.lower()
        cl = cmd.lower()
        if "test" in nl or "jest" in cl or "vitest" in cl or "mocha" in cl:
            return "Automated Tests"
        if "lint" in nl or "eslint" in cl or "biome" in cl:
            return "Linting"
        if "format" in nl or "prettier" in cl:
            return "Code Formatting"
        if "typecheck" in nl or "type-check" in nl or "tsc" in cl:
            return "Type Checking"
        if "build" in nl:
            return "Production Build"
        if "check" in nl:
            return "Quality Check"
        return ""

