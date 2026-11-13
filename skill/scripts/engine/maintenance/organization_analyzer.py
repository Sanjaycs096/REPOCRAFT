"""Codebase organization analyzer for RepoCraft.

Identifies structural hygiene issues, duplicate files, naming inconsistencies,
unnecessary nesting, and misplaced assets or source files.
"""
from __future__ import annotations

import hashlib
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple


class OrganizationFinding:
    def __init__(
        self,
        finding_id: str,
        current_path: str,
        proposed_path: str | None,
        reason: str,
        evidence: str,
        import_impact: str,
        risk_level: str,  # LOW, MEDIUM, HIGH, CRITICAL
        requires_approval: bool = True,
        validation_steps: str = "",
    ):
        self.finding_id = finding_id
        self.current_path = current_path
        self.proposed_path = proposed_path
        self.reason = reason
        self.evidence = evidence
        self.import_impact = import_impact
        self.risk_level = risk_level
        self.requires_approval = requires_approval
        self.validation_steps = validation_steps

    def to_dict(self) -> Dict[str, Any]:
        return {
            "finding_id": self.finding_id,
            "current_path": self.current_path,
            "proposed_path": self.proposed_path,
            "reason": self.reason,
            "evidence": self.evidence,
            "import_impact": self.import_impact,
            "risk_level": self.risk_level,
            "requires_approval": self.requires_approval,
            "validation_steps": self.validation_steps,
        }


class OrganizationAnalyzer:
    """Analyzes codebase directory structure, duplicate files, and naming conventions."""

    def __init__(
        self,
        repo_root: Path,
        file_paths: List[str],
        file_categories: Dict[str, str],
    ):
        self.repo_root = repo_root
        self.file_paths = file_paths
        self.file_categories = file_categories
        self.findings: List[OrganizationFinding] = []
        self._counter = 1

    def _next_id(self) -> str:
        fid = f"FINDING-ORG-{self._counter:03d}"
        self._counter += 1
        return fid

    def analyze(self) -> Tuple[List[OrganizationFinding], Dict[str, Any]]:
        self.findings.clear()
        duplicate_files = self._detect_duplicate_files()
        naming_issues = self._detect_naming_inconsistencies()
        misplaced_files = self._detect_misplaced_files()
        nesting_issues = self._detect_unnecessary_nesting()

        stats = {
            "duplicate_groups_count": len(duplicate_files),
            "naming_issue_count": len(naming_issues),
            "misplaced_file_count": len(misplaced_files),
            "nesting_issue_count": len(nesting_issues),
            "total_findings": len(self.findings),
        }
        return self.findings, stats

    def _detect_duplicate_files(self) -> List[List[str]]:
        """Finds identical files using sha256 checksums."""
        hashes: Dict[str, List[str]] = {}
        for p in self.file_paths:
            full_path = self.repo_root / p
            try:
                # Only check files < 5MB
                if full_path.stat().st_size > 5 * 1024 * 1024 or full_path.stat().st_size == 0:
                    continue
                h = hashlib.sha256(full_path.read_bytes()).hexdigest()
                hashes.setdefault(h, []).append(p)
            except Exception:
                continue

        dup_groups = []
        for h, paths in sorted(hashes.items()):
            if len(paths) > 1:
                dup_groups.append(paths)
                self.findings.append(
                    OrganizationFinding(
                        finding_id=self._next_id(),
                        current_path=paths[1],
                        proposed_path=None,
                        reason="Duplicate identical file detected.",
                        evidence=f"File content is bit-for-bit identical to '{paths[0]}' (SHA-256: {h[:12]}...).",
                        import_impact="High. If removed, callers must import from the primary canonical path.",
                        risk_level="MEDIUM",
                        requires_approval=True,
                        validation_steps=f"Verify all imports of '{paths[1]}' are consolidated to '{paths[0]}'.",
                    )
                )
        return dup_groups

    def _detect_naming_inconsistencies(self) -> List[str]:
        """Detects mixed casing styles (kebab-case, camelCase, snake_case) within the same directory."""
        dir_files: Dict[str, List[str]] = {}
        for p in self.file_paths:
            parts = p.split("/")
            if len(parts) > 1:
                parent = "/".join(parts[:-1])
                dir_files.setdefault(parent, []).append(parts[-1])

        issues = []
        for d, filenames in sorted(dir_files.items()):
            stems = [Path(fn).stem for fn in filenames if not fn.startswith(".") and len(fn) > 3]
            has_kebab = any("-" in s and not "_" in s for s in stems)
            has_snake = any("_" in s and not "-" in s for s in stems)
            has_camel = any(re.search(r"^[a-z]+[A-Z]", s) for s in stems)
            has_pascal = any(re.search(r"^[A-Z][a-zA-Z0-9]+$", s) for s in stems)

            styles = []
            if has_kebab:
                styles.append("kebab-case")
            if has_snake:
                styles.append("snake_case")
            if has_camel:
                styles.append("camelCase")
            if has_pascal:
                styles.append("PascalCase")

            if len(styles) >= 3 or (has_kebab and has_snake):
                issues.append(d)
                self.findings.append(
                    OrganizationFinding(
                        finding_id=self._next_id(),
                        current_path=d,
                        proposed_path=None,
                        reason=f"Inconsistent file naming conventions in '{d}'.",
                        evidence=f"Detected mixed naming styles ({', '.join(styles)}) in directory: {', '.join(filenames[:5])}.",
                        import_impact="Medium. Renaming files alters import paths across the project.",
                        risk_level="LOW",
                        requires_approval=True,
                        validation_steps="Standardize file naming across the directory and update all corresponding imports.",
                    )
                )
        return issues

    def _detect_misplaced_files(self) -> List[str]:
        """Identifies files located in inappropriate directories."""
        misplaced = []
        has_src_dir = any(p.startswith("src/") for p in self.file_paths)

        for p in self.file_paths:
            cat = self.file_categories.get(p, "unknown")
            parts = p.split("/")
            name = parts[-1]

            # 1. Source files in root directory when a dedicated src/ directory exists
            if has_src_dir and len(parts) == 1 and cat == "source":
                if name not in ("setup.py", "wsgi.py", "asgi.py", "conftest.py"):
                    misplaced.append(p)
                    self.findings.append(
                        OrganizationFinding(
                            finding_id=self._next_id(),
                            current_path=p,
                            proposed_path=f"src/{name}",
                            reason="Application source file located in repository root instead of src/ directory.",
                            evidence=f"Repository maintains a 'src/' tree, but '{name}' is sitting loose in the root.",
                            import_impact="High. External entrypoints or tests importing this file will need path updates.",
                            risk_level="MEDIUM",
                            requires_approval=True,
                            validation_steps=f"Move '{p}' to 'src/{name}' and test entrypoint imports.",
                        )
                    )

            # 2. Asset files loose in source directories
            if len(parts) > 1 and parts[0] == "src" and cat == "assets":
                if Path(p).suffix.lower() in (".png", ".jpg", ".svg", ".ico") and "assets" not in parts and "public" not in parts:
                    misplaced.append(p)
                    self.findings.append(
                        OrganizationFinding(
                            finding_id=self._next_id(),
                            current_path=p,
                            proposed_path=f"src/assets/{name}",
                            reason="Asset media file stored directly in source module directory.",
                            evidence=f"Image file '{p}' found outside dedicated assets/ or public/ directories.",
                            import_impact="Low to Medium. Asset imports/URLs must be redirected.",
                            risk_level="LOW",
                            requires_approval=True,
                            validation_steps=f"Move asset to dedicated assets directory and verify UI rendering.",
                        )
                    )

        return misplaced

    def _detect_unnecessary_nesting(self) -> List[str]:
        """Detects chains of directories with only a single subfolder and file."""
        nesting_issues = []
        dir_tree: Dict[str, Set[str]] = {}
        dir_files: Dict[str, List[str]] = {}

        for p in self.file_paths:
            # Java/Kotlin standard package hierarchies require deep directory trees by specification
            if "java/" in p or "kotlin/" in p:
                continue
            parts = p.split("/")
            if len(parts) > 4:  # Deeply nested (e.g. a/b/c/d/file.py)
                for i in range(1, len(parts)):
                    parent = "/".join(parts[:i])
                    child = "/".join(parts[: i + 1])
                    dir_tree.setdefault(parent, set()).add(child)
                dir_files.setdefault("/".join(parts[:-1]), []).append(parts[-1])

        for parent, children in dir_tree.items():
            # If a folder has exactly 1 child folder and 0 direct files, and that child has 1 child folder...
            if len(children) == 1:
                child = list(children)[0]
                if parent.count("/") >= 3 and len(dir_files.get(parent, [])) == 0 and len(dir_tree.get(child, set())) == 1:
                    if parent not in nesting_issues:
                        nesting_issues.append(parent)
                        self.findings.append(
                            OrganizationFinding(
                                finding_id=self._next_id(),
                                current_path=child,
                                proposed_path=parent,
                                reason="Potentially unnecessary deep directory nesting with single-child hierarchy.",
                                evidence=f"Directory hierarchy '{parent}' contains single-branch directory chain without siblings.",
                                import_impact="High. Flattens module import paths.",
                                risk_level="MEDIUM",
                                requires_approval=True,
                                validation_steps="Evaluate whether flattening the package structure improves developer ergonomics.",
                            )
                        )
        return nesting_issues
