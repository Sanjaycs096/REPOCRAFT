"""Dependency and supply chain vulnerability auditor for RepoCraft.

Parses package manifests and lockfiles across Node.js, Python, Java, Rust, and Go.
Identifies missing lockfiles, unpinned dependencies, and suspicious sources.
Strictly zero network access by default; reports vulnerability verification as UNVERIFIED
when no authoritative local database is present.
"""
from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from .types import DependencyAuditResult, DependencyItem, VulnerabilityStatus


class DependencyAuditor:
    """Audits project manifests and lockfiles for pinning, integrity, and vulnerabilities."""

    def __init__(self, repo_root: Path, file_paths: List[str]):
        self.repo_root = repo_root
        self.file_paths = file_paths
        self.paths_set: Set[str] = set(file_paths)

    def audit(self) -> List[DependencyAuditResult]:
        results: List[DependencyAuditResult] = []

        # 1. Node.js (package.json)
        for p in [f for f in self.file_paths if f.endswith("package.json")]:
            res = self._audit_node_manifest(p)
            if res:
                results.append(res)

        # 2. Python (pyproject.toml, requirements.txt, Pipfile)
        for p in [f for f in self.file_paths if f.endswith(("pyproject.toml", "requirements.txt", "Pipfile"))]:
            res = self._audit_python_manifest(p)
            if res:
                results.append(res)

        # 3. Java (pom.xml, build.gradle)
        for p in [f for f in self.file_paths if f.endswith(("pom.xml", "build.gradle", "build.gradle.kts"))]:
            res = self._audit_java_manifest(p)
            if res:
                results.append(res)

        # 4. Rust (Cargo.toml)
        for p in [f for f in self.file_paths if f.endswith("Cargo.toml")]:
            res = self._audit_rust_manifest(p)
            if res:
                results.append(res)

        # 5. Go (go.mod)
        for p in [f for f in self.file_paths if f.endswith("go.mod")]:
            res = self._audit_go_manifest(p)
            if res:
                results.append(res)

        return results

    def _is_unpinned(self, version: str) -> bool:
        v = version.strip()
        if not v or v in ("*", "latest"):
            return True
        if v.startswith(">=") or v.startswith(">"):
            return True
        return False

    def _is_suspicious_source(self, version: str) -> bool:
        v = version.strip().lower()
        if v.startswith(("git://", "http://", "git+http://", "ssh://")):
            return True
        return False

    def _audit_node_manifest(self, manifest_rel: str) -> Optional[DependencyAuditResult]:
        full_path = self.repo_root / manifest_rel
        try:
            content = full_path.read_text(encoding="utf-8", errors="replace")
            data = json.loads(content)
            if not isinstance(data, dict):
                return DependencyAuditResult(
                    manifest_path=manifest_rel,
                    lockfile_path=None,
                    lockfile_present=False,
                    ecosystem="npm",
                    dependencies=[],
                    unpinned_count=0,
                    suspicious_sources_count=0,
                    vulnerability_status=VulnerabilityStatus.ANALYSIS_ERROR,
                    notes="Manifest root is not a valid JSON object.",
                )

            deps: List[DependencyItem] = []
            manifest_dir = Path(manifest_rel).parent.as_posix()
            manifest_prefix = f"{manifest_dir}/" if manifest_dir != "." else ""

            # Check lockfiles in same directory or root
            lock_candidates = [
                f"{manifest_prefix}package-lock.json",
                f"{manifest_prefix}pnpm-lock.yaml",
                f"{manifest_prefix}yarn.lock",
                "package-lock.json", "pnpm-lock.yaml", "yarn.lock"
            ]
            lockfile_found = next((l for l in lock_candidates if l in self.paths_set), None)

            # Direct dependencies
            for dep_name, version in data.get("dependencies", {}).items():
                v_str = str(version)
                deps.append(
                    DependencyItem(
                        name=dep_name,
                        version_constraint=v_str,
                        is_dev=False,
                        ecosystem="npm",
                        is_unpinned=self._is_unpinned(v_str),
                        is_suspicious_source=self._is_suspicious_source(v_str),
                    )
                )

            # Dev dependencies
            for dep_name, version in data.get("devDependencies", {}).items():
                v_str = str(version)
                deps.append(
                    DependencyItem(
                        name=dep_name,
                        version_constraint=v_str,
                        is_dev=True,
                        ecosystem="npm",
                        is_unpinned=self._is_unpinned(v_str),
                        is_suspicious_source=self._is_suspicious_source(v_str),
                    )
                )

            unpinned_cnt = sum(1 for d in deps if d.is_unpinned)
            suspicious_cnt = sum(1 for d in deps if d.is_suspicious_source)

            if lockfile_found is None:
                note_str = "Missing lockfile; unpinned dependencies cannot be deterministically verified."
            else:
                note_str = "Offline scan mode. Manifest syntax verified; external vulnerability database was not queried."

            return DependencyAuditResult(
                manifest_path=manifest_rel,
                lockfile_path=lockfile_found,
                lockfile_present=lockfile_found is not None,
                ecosystem="npm",
                dependencies=deps,
                unpinned_count=unpinned_cnt,
                suspicious_sources_count=suspicious_cnt,
                vulnerability_status=VulnerabilityStatus.UNVERIFIED,
                notes=note_str,
            )

        except Exception as exc:
            return DependencyAuditResult(
                manifest_path=manifest_rel,
                lockfile_path=None,
                lockfile_present=False,
                ecosystem="npm",
                dependencies=[],
                unpinned_count=0,
                suspicious_sources_count=0,
                vulnerability_status=VulnerabilityStatus.ANALYSIS_ERROR,
                notes=f"Failed to parse manifest: {str(exc)}",
            )

    def _audit_python_manifest(self, manifest_rel: str) -> Optional[DependencyAuditResult]:
        full_path = self.repo_root / manifest_rel
        try:
            content = full_path.read_text(encoding="utf-8", errors="replace")
            deps: List[DependencyItem] = []

            # Check ecosystem-specific lockfiles
            if manifest_rel.endswith("requirements.txt"):
                lock_candidates = ["requirements.lock", "requirements-lock.txt"]
            elif manifest_rel.endswith("Pipfile"):
                lock_candidates = ["Pipfile.lock"]
            else:
                lock_candidates = ["poetry.lock", "pdm.lock", "uv.lock"]
            lockfile_found = next((l for l in lock_candidates if l in self.paths_set), None)

            if manifest_rel.endswith("requirements.txt"):
                for line in content.splitlines():
                    clean = line.strip().split("#")[0].strip()
                    if not clean or clean.startswith(("-r", "-i", "--")):
                        continue

                    # Match name==1.0 or name>=1.0
                    m = re.match(r"^([a-zA-Z0-9_\-\.]+)\s*([=><!~^].*)?$", clean)
                    if m:
                        name = m.group(1)
                        constraint = m.group(2) or "*"
                        deps.append(
                            DependencyItem(
                                name=name,
                                version_constraint=constraint,
                                ecosystem="pypi",
                                is_unpinned=self._is_unpinned(constraint),
                                is_suspicious_source=self._is_suspicious_source(constraint),
                            )
                        )

            elif manifest_rel.endswith("Pipfile"):
                in_packages = False
                for line in content.splitlines():
                    l_str = line.strip()
                    if l_str.startswith("[packages]"):
                        in_packages = True
                        continue
                    if in_packages and l_str.startswith("["):
                        in_packages = False
                        continue
                    if in_packages and "=" in l_str:
                        parts = l_str.split("=", 1)
                        name = parts[0].strip()
                        ver = parts[1].strip().strip('"\'')
                        deps.append(
                            DependencyItem(
                                name=name,
                                version_constraint=ver,
                                ecosystem="pypi",
                                is_unpinned=self._is_unpinned(ver),
                                is_suspicious_source=self._is_suspicious_source(ver),
                            )
                        )

            elif manifest_rel.endswith("pyproject.toml"):
                # Extract dependencies under [project.dependencies] or [tool.poetry.dependencies]
                in_deps = False
                in_poetry = False
                for line in content.splitlines():
                    l_str = line.strip()
                    if l_str.startswith("dependencies = ["):
                        in_deps = True
                        continue
                    if in_deps:
                        if l_str.startswith("]"):
                            in_deps = False
                            continue
                        dep_line = l_str.strip('",\'')
                        m = re.match(r"^([a-zA-Z0-9_\-\.]+)\s*([=><!~^].*)?$", dep_line)
                        if m:
                            name = m.group(1)
                            constraint = m.group(2) or "*"
                            deps.append(
                                DependencyItem(
                                    name=name,
                                    version_constraint=constraint,
                                    ecosystem="pypi",
                                    is_unpinned=self._is_unpinned(constraint),
                                    is_suspicious_source=self._is_suspicious_source(constraint),
                                )
                            )

                    if l_str.startswith("[tool.poetry.dependencies]"):
                        in_poetry = True
                        continue
                    if in_poetry and l_str.startswith("["):
                        in_poetry = False
                        continue
                    if in_poetry and "=" in l_str:
                        parts = l_str.split("=", 1)
                        name = parts[0].strip()
                        if name.lower() != "python":
                            ver = parts[1].strip().strip('"\'')
                            deps.append(
                                DependencyItem(
                                    name=name,
                                    version_constraint=ver,
                                    ecosystem="pypi",
                                    is_unpinned=self._is_unpinned(ver),
                                    is_suspicious_source=self._is_suspicious_source(ver),
                                )
                            )

            unpinned_cnt = sum(1 for d in deps if d.is_unpinned)
            suspicious_cnt = sum(1 for d in deps if d.is_suspicious_source)

            return DependencyAuditResult(
                manifest_path=manifest_rel,
                lockfile_path=lockfile_found,
                lockfile_present=lockfile_found is not None,
                ecosystem="pypi",
                dependencies=deps,
                unpinned_count=unpinned_cnt,
                suspicious_sources_count=suspicious_cnt,
                vulnerability_status=VulnerabilityStatus.UNVERIFIED,
                notes="Offline mode: Python manifest parsed without external API calls.",
            )

        except Exception as exc:
            return DependencyAuditResult(
                manifest_path=manifest_rel,
                lockfile_path=None,
                lockfile_present=False,
                ecosystem="pypi",
                dependencies=[],
                unpinned_count=0,
                suspicious_sources_count=0,
                vulnerability_status=VulnerabilityStatus.ANALYSIS_ERROR,
                notes=f"Error reading Python manifest: {str(exc)}",
            )

    def _audit_java_manifest(self, manifest_rel: str) -> Optional[DependencyAuditResult]:
        full_path = self.repo_root / manifest_rel
        try:
            content = full_path.read_text(encoding="utf-8", errors="replace")
            deps: List[DependencyItem] = []

            # Match <groupId>...</groupId><artifactId>...</artifactId>
            artifact_matches = re.findall(r"<artifactId>([^<]+)</artifactId>", content)
            for art in artifact_matches:
                deps.append(
                    DependencyItem(
                        name=art.strip(),
                        version_constraint="declared",
                        ecosystem="maven",
                        is_unpinned=False,
                    )
                )

            return DependencyAuditResult(
                manifest_path=manifest_rel,
                lockfile_path=None,
                lockfile_present=False,
                ecosystem="maven",
                dependencies=deps,
                unpinned_count=0,
                suspicious_sources_count=0,
                vulnerability_status=VulnerabilityStatus.UNVERIFIED,
                notes="Offline mode: Java POM/Gradle manifest parsed.",
            )
        except Exception as exc:
            return DependencyAuditResult(
                manifest_path=manifest_rel,
                lockfile_path=None,
                lockfile_present=False,
                ecosystem="maven",
                dependencies=[],
                unpinned_count=0,
                suspicious_sources_count=0,
                vulnerability_status=VulnerabilityStatus.ANALYSIS_ERROR,
                notes=str(exc),
            )

    def _audit_rust_manifest(self, manifest_rel: str) -> Optional[DependencyAuditResult]:
        full_path = self.repo_root / manifest_rel
        try:
            content = full_path.read_text(encoding="utf-8", errors="replace")
            deps: List[DependencyItem] = []
            has_lock = "Cargo.lock" in self.paths_set

            in_deps = False
            for line in content.splitlines():
                l = line.strip()
                if l.startswith("[dependencies]") or l.startswith("[dev-dependencies]"):
                    in_deps = True
                    continue
                if in_deps and l.startswith("["):
                    in_deps = False
                    continue
                if in_deps and "=" in l:
                    parts = l.split("=", 1)
                    dep_name = parts[0].strip()
                    ver = parts[1].strip().strip('"\'')
                    deps.append(
                        DependencyItem(
                            name=dep_name,
                            version_constraint=ver,
                            ecosystem="cargo",
                            is_unpinned=self._is_unpinned(ver),
                            is_suspicious_source=self._is_suspicious_source(ver),
                        )
                    )

            return DependencyAuditResult(
                manifest_path=manifest_rel,
                lockfile_path="Cargo.lock" if has_lock else None,
                lockfile_present=has_lock,
                ecosystem="cargo",
                dependencies=deps,
                unpinned_count=sum(1 for d in deps if d.is_unpinned),
                suspicious_sources_count=sum(1 for d in deps if d.is_suspicious_source),
                vulnerability_status=VulnerabilityStatus.UNVERIFIED,
                notes="Offline Cargo audit.",
            )
        except Exception as exc:
            return None

    def _audit_go_manifest(self, manifest_rel: str) -> Optional[DependencyAuditResult]:
        full_path = self.repo_root / manifest_rel
        try:
            content = full_path.read_text(encoding="utf-8", errors="replace")
            deps: List[DependencyItem] = []
            has_lock = "go.sum" in self.paths_set

            for line in content.splitlines():
                l = line.strip()
                if l.startswith("require (") or l.startswith(")"):
                    continue
                if l.startswith("require "):
                    parts = l[8:].strip().split()
                    if len(parts) >= 2:
                        deps.append(DependencyItem(name=parts[0], version_constraint=parts[1], ecosystem="go"))
                elif "/" in l and len(l.split()) >= 2:
                    parts = l.split()
                    deps.append(DependencyItem(name=parts[0], version_constraint=parts[1], ecosystem="go"))

            return DependencyAuditResult(
                manifest_path=manifest_rel,
                lockfile_path="go.sum" if has_lock else None,
                lockfile_present=has_lock,
                ecosystem="go",
                dependencies=deps,
                unpinned_count=0,
                suspicious_sources_count=0,
                vulnerability_status=VulnerabilityStatus.UNVERIFIED,
                notes="Offline Go modules audit.",
            )
        except Exception:
            return None


def audit_dependencies(target_dir: str) -> List[DependencyAuditResult]:
    """Scan and audit package manifests and lockfiles in the target repository."""
    root = Path(target_dir).resolve()
    file_paths: List[str] = []
    for current_dir, dirs, files in os.walk(root):
        dirs[:] = [
            d
            for d in dirs
            if d not in {".git", "node_modules", "venv", ".venv", "__pycache__", "build", "dist", "target"}
        ]
        for f in files:
            full = Path(current_dir) / f
            file_paths.append(full.relative_to(root).as_posix())

    auditor = DependencyAuditor(root, file_paths)
    return auditor.audit()

