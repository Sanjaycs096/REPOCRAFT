"""Unused file detection module for RepoCraft.

Identifies unreferenced files and classifies them with confidence levels:
CONFIRMED_UNUSED, LIKELY_UNUSED, POSSIBLY_UNUSED, UNKNOWN.
Strictly enforces the rule: NEVER automatically delete files in Phase 2.
"""
from __future__ import annotations

import os
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Set

from .reference_analyzer import ReferenceAnalyzer


class UnusedConfidence(str, Enum):
    CONFIRMED_UNUSED = "CONFIRMED_UNUSED"
    LIKELY_UNUSED = "LIKELY_UNUSED"
    POSSIBLY_UNUSED = "POSSIBLY_UNUSED"
    UNKNOWN = "UNKNOWN"


class UnusedFileCandidate:
    def __init__(
        self,
        relative_path: str,
        confidence: UnusedConfidence,
        reason: str,
        evidence: str,
        size_bytes: int,
        category: str,
    ):
        self.relative_path = relative_path
        self.confidence = confidence
        self.reason = reason
        self.evidence = evidence
        self.size_bytes = size_bytes
        self.category = category

    def to_dict(self) -> Dict[str, Any]:
        return {
            "relative_path": self.relative_path,
            "confidence": self.confidence.value,
            "reason": self.reason,
            "evidence": self.evidence,
            "size_bytes": self.size_bytes,
            "category": self.category,
        }


class UnusedFileDetector:
    """Discovers unreferenced files and assigns calibrated confidence levels."""

    def __init__(
        self,
        repo_root: Path,
        file_paths: List[str],
        file_categories: Dict[str, str],
        file_sizes: Dict[str, int],
    ):
        self.repo_root = repo_root
        self.file_paths = file_paths
        self.file_categories = file_categories
        self.file_sizes = file_sizes

    def detect_unused_files(self) -> List[UnusedFileCandidate]:
        candidates: List[UnusedFileCandidate] = []

        ref_analyzer = ReferenceAnalyzer(self.repo_root, self.file_paths)
        references = ref_analyzer.analyze_references()
        framework_conventions = ref_analyzer.identify_framework_conventions()

        for p in self.file_paths:
            # 1. Framework entrypoints, routes, configs, and tests are NEVER unused
            if p in framework_conventions:
                continue

            ref_count = len(references.get(p, set()))
            name = Path(p).name
            ext = Path(p).suffix.lower()
            size = self.file_sizes.get(p, 0)
            cat = self.file_categories.get(p, "unknown")

            # 2. Confirmed unused: Obsolete temp/backup files
            if (
                name.endswith((".bak", ".tmp", ".swp", ".swo", "~", ".orig"))
                or name.startswith(("Copy of ", "Untitled", ".DS_Store", "Thumbs.db"))
            ):
                candidates.append(
                    UnusedFileCandidate(
                        relative_path=p,
                        confidence=UnusedConfidence.CONFIRMED_UNUSED,
                        reason="Obsolete temporary or editor backup file.",
                        evidence=f"Filename pattern '{name}' matches obsolete temporary file heuristics.",
                        size_bytes=size,
                        category=cat,
                    )
                )
                continue

            # If there are references, it's used
            if ref_count > 0:
                continue

            # 3. Dynamic or plugin directory inspection
            parts = p.split("/")
            if any(part in ("plugins", "scripts", "fixtures", "mock", "mocks", "examples") for part in parts):
                candidates.append(
                    UnusedFileCandidate(
                        relative_path=p,
                        confidence=UnusedConfidence.POSSIBLY_UNUSED,
                        reason="Unreferenced in static analysis, but located in dynamically loaded directory.",
                        evidence=(
                            f"0 static references found across project. May be invoked externally or dynamically via {parts[0]}."
                        ),
                        size_bytes=size,
                        category=cat,
                    )
                )
                continue

            # 4. Source code with 0 references and no framework convention
            if cat == "source":
                candidates.append(
                    UnusedFileCandidate(
                        relative_path=p,
                        confidence=UnusedConfidence.LIKELY_UNUSED,
                        reason="Source file has 0 static or dynamic imports across repository.",
                        evidence=(
                            f"No imports, require calls, or entry point references found for '{p}'."
                        ),
                        size_bytes=size,
                        category=cat,
                    )
                )
            elif cat == "assets":
                candidates.append(
                    UnusedFileCandidate(
                        relative_path=p,
                        confidence=UnusedConfidence.LIKELY_UNUSED,
                        reason="Asset file has 0 references in HTML, CSS, Markdown, or source code.",
                        evidence=f"No URL or path references to '{name}' found in any codebase file.",
                        size_bytes=size,
                        category=cat,
                    )
                )
            elif cat == "documentation":
                # Only if in deep subdirectory and unreferenced
                if len(parts) > 1 and parts[0] not in ("docs", "doc"):
                    candidates.append(
                        UnusedFileCandidate(
                            relative_path=p,
                            confidence=UnusedConfidence.POSSIBLY_UNUSED,
                            reason="Orphaned markdown file outside primary documentation hierarchy.",
                            evidence=f"File '{p}' is unlinked in README or docs/.",
                            size_bytes=size,
                            category=cat,
                        )
                    )

        # Sort deterministically
        candidates.sort(key=lambda c: (c.confidence.value, c.relative_path))
        return candidates

