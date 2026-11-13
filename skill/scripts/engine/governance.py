"""Governance and documentation discovery module for RepoCraft.

Identifies presence, size, completeness, and structure of README, LICENSE,
CONTRIBUTING, CODE_OF_CONDUCT, SECURITY, templates, and CI/CD governance files.
"""
from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional, Set

from .discovery import safe_read_text
from .types import EvidenceLevel, FileInventoryItem, GovernanceItem

GOVERNANCE_TARGETS = {
    "readme": ["readme.md", "readme.rst", "readme.txt", "readme"],
    "license": ["license", "license.md", "licence", "licence.md", "copying", "license.txt"],
    "contributing": ["contributing.md", "contributing.rst", ".github/contributing.md"],
    "code_of_conduct": ["code_of_conduct.md", ".github/code_of_conduct.md"],
    "security_policy": ["security.md", ".github/security.md"],
    "changelog": ["changelog.md", "history.md", "news.md", "releases.md"],
    "pull_request_template": [
        "pull_request_template.md",
        ".github/pull_request_template.md",
        ".github/pull_request_template/pull_request_template.md",
    ],
    "funding": ["funding.yml", ".github/funding.yml"],
    "citation": ["citation.cff"],
}


class GovernanceAnalyzer:
    """Discovers governance and documentation status."""

    def __init__(self, repo_root: Path, inventory: List[FileInventoryItem]):
        self.repo_root = repo_root
        self.inventory = inventory
        self.path_map: Dict[str, FileInventoryItem] = {
            item.relative_path.lower(): item for item in inventory
        }

    def analyze(self) -> Dict[str, GovernanceItem]:
        results: Dict[str, GovernanceItem] = {}

        for item_key, candidates in GOVERNANCE_TARGETS.items():
            found_item: Optional[GovernanceItem] = None
            for candidate in candidates:
                cand_lower = candidate.lower()
                if cand_lower in self.path_map:
                    inv_item = self.path_map[cand_lower]
                    full_path = self.repo_root / inv_item.relative_path
                    size = inv_item.size_bytes
                    is_empty = size == 0

                    notes = None
                    conf = EvidenceLevel.VERIFIED
                    if is_empty:
                        notes = "File exists but is completely empty (0 bytes)."
                    elif size < 50:
                        notes = f"File exists but is very short ({size} bytes) and likely incomplete."
                    else:
                        notes = f"File present ({size} bytes)."

                    found_item = GovernanceItem(
                        item_type=item_key,
                        relative_path=inv_item.relative_path,
                        exists=True,
                        is_empty=is_empty,
                        size_bytes=size,
                        confidence=conf,
                        notes=notes,
                    )
                    break

            if found_item:
                results[item_key] = found_item
            else:
                results[item_key] = GovernanceItem(
                    item_type=item_key,
                    relative_path=None,
                    exists=False,
                    is_empty=True,
                    size_bytes=0,
                    confidence=EvidenceLevel.VERIFIED,
                    notes=f"No standard {item_key} document detected in repository root or .github/.",
                )

        # Issue templates check
        issue_template_files = [
            item.relative_path
            for item in self.inventory
            if item.relative_path.lower().startswith(".github/issue_template/")
        ]
        if issue_template_files:
            results["issue_templates"] = GovernanceItem(
                item_type="issue_templates",
                relative_path=".github/ISSUE_TEMPLATE/",
                exists=True,
                is_empty=False,
                size_bytes=sum(
                    self.path_map[p.lower()].size_bytes
                    for p in issue_template_files
                    if p.lower() in self.path_map
                ),
                confidence=EvidenceLevel.VERIFIED,
                notes=f"Found {len(issue_template_files)} issue template file(s).",
            )
        else:
            single_issue_tmpl = [
                item.relative_path
                for item in self.inventory
                if item.relative_path.lower() in ("issue_template.md", ".github/issue_template.md")
            ]
            if single_issue_tmpl:
                results["issue_templates"] = GovernanceItem(
                    item_type="issue_templates",
                    relative_path=single_issue_tmpl[0],
                    exists=True,
                    is_empty=False,
                    size_bytes=self.path_map[single_issue_tmpl[0].lower()].size_bytes,
                    confidence=EvidenceLevel.VERIFIED,
                    notes="Single issue template markdown file present.",
                )
            else:
                results["issue_templates"] = GovernanceItem(
                    item_type="issue_templates",
                    relative_path=None,
                    exists=False,
                    is_empty=True,
                    size_bytes=0,
                    confidence=EvidenceLevel.VERIFIED,
                    notes="No issue templates detected.",
                )

        # Documentation directory
        docs_files = [
            item.relative_path
            for item in self.inventory
            if item.relative_path.lower().startswith(("docs/", "doc/"))
        ]
        if docs_files:
            results["documentation_directory"] = GovernanceItem(
                item_type="documentation_directory",
                relative_path="docs/",
                exists=True,
                is_empty=False,
                size_bytes=sum(
                    self.path_map[p.lower()].size_bytes
                    for p in docs_files
                    if p.lower() in self.path_map
                ),
                confidence=EvidenceLevel.VERIFIED,
                notes=f"Dedicated documentation directory with {len(docs_files)} file(s).",
            )
        else:
            results["documentation_directory"] = GovernanceItem(
                item_type="documentation_directory",
                relative_path=None,
                exists=False,
                is_empty=True,
                size_bytes=0,
                confidence=EvidenceLevel.VERIFIED,
                notes="No dedicated docs/ or doc/ directory present.",
            )

        return results

