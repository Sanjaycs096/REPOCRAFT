"""Documentation and governance auditor for RepoCraft.

Audits repository documentation files for broken internal links, missing local images,
outdated commands, and missing governance policies (CONTRIBUTING, CODE_OF_CONDUCT, SECURITY, CHANGELOG).
"""
from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple


class BrokenLink:
    def __init__(self, doc_path: str, link_target: str, link_text: str, is_image: bool = False):
        self.doc_path = doc_path
        self.link_target = link_target
        self.link_text = link_text
        self.is_image = is_image

    def to_dict(self) -> Dict[str, Any]:
        return {
            "doc_path": self.doc_path,
            "link_target": self.link_target,
            "link_text": self.link_text,
            "is_image": self.is_image,
        }


class DocumentationAuditResult:
    def __init__(
        self,
        docs_inventory: List[str],
        broken_links: List[BrokenLink],
        missing_images: List[BrokenLink],
        missing_governance: List[str],
        contradictory_commands: List[str],
        drafts_available: Dict[str, str],
    ):
        self.docs_inventory = docs_inventory
        self.broken_links = broken_links
        self.missing_images = missing_images
        self.missing_governance = missing_governance
        self.contradictory_commands = contradictory_commands
        self.drafts_available = drafts_available

    def to_dict(self) -> Dict[str, Any]:
        return {
            "docs_inventory": self.docs_inventory,
            "broken_links": [b.to_dict() for b in self.broken_links],
            "missing_images": [m.to_dict() for m in self.missing_images],
            "missing_governance": self.missing_governance,
            "contradictory_commands": self.contradictory_commands,
            "drafts_available": list(self.drafts_available.keys()),
        }


class DocumentationAuditor:
    """Audits markdown documentation, governance files, links, and command consistency."""

    def __init__(self, repo_root: Path, file_paths: List[str], package_managers: List[str]):
        self.repo_root = repo_root
        self.file_paths = file_paths
        self.package_managers = package_managers
        self.paths_set: Set[str] = set(file_paths)
        self.paths_set_lower: Set[str] = {p.lower() for p in file_paths}

    def audit(self) -> DocumentationAuditResult:
        doc_files = [p for p in self.file_paths if p.lower().endswith((".md", ".rst", ".adoc"))]
        broken_links: List[BrokenLink] = []
        missing_images: List[BrokenLink] = []
        contradictory_commands: List[str] = []

        for df in doc_files:
            full_path = self.repo_root / df
            try:
                content = full_path.read_text(encoding="utf-8", errors="replace")
                doc_dir = Path(df).parent.as_posix()
                if doc_dir == ".":
                    doc_dir = ""

                # Check images: ![alt](target)
                img_matches = re.findall(r"""!\[([^\]]*)\]\(([^)]+)\)""", content)
                for alt, target in img_matches:
                    clean_target = target.split("?")[0].split("#")[0].strip()
                    if clean_target.startswith(("http://", "https://", "data:")):
                        continue
                    if not self._target_exists(doc_dir, clean_target):
                        missing_images.append(
                            BrokenLink(doc_path=df, link_target=clean_target, link_text=alt, is_image=True)
                        )

                # Check links: [text](target)
                link_matches = re.findall(r"""(?<!!)\[([^\]]+)\]\(([^)]+)\)""", content)
                for text, target in link_matches:
                    clean_target = target.split("?")[0].split("#")[0].strip()
                    if clean_target.startswith(("http://", "https://", "mailto:", "#", "javascript:")):
                        continue
                    if not self._target_exists(doc_dir, clean_target):
                        broken_links.append(
                            BrokenLink(doc_path=df, link_target=clean_target, link_text=text, is_image=False)
                        )

                # Check for contradictory commands
                self._check_command_contradictions(df, content, contradictory_commands)

            except Exception:
                continue

        # Missing governance policies
        missing_gov = []
        for gov_target in ("CONTRIBUTING.md", "CODE_OF_CONDUCT.md", "SECURITY.md", "CHANGELOG.md"):
            if not any(p.lower() == gov_target.lower() or p.lower().endswith("/" + gov_target.lower()) for p in self.file_paths):
                missing_gov.append(gov_target)

        # Generate drafts for missing governance
        drafts = self._generate_governance_drafts(missing_gov)

        return DocumentationAuditResult(
            docs_inventory=doc_files,
            broken_links=broken_links,
            missing_images=missing_images,
            missing_governance=missing_gov,
            contradictory_commands=contradictory_commands,
            drafts_available=drafts,
        )

    def _target_exists(self, doc_dir: str, target: str) -> bool:
        # Check direct relative to root
        norm_root = os.path.normpath(target).replace("\\", "/").lstrip("/")
        if norm_root in self.paths_set or norm_root.lower() in self.paths_set_lower:
            return True

        # Check relative to doc_dir
        if doc_dir:
            joined = os.path.normpath(os.path.join(doc_dir, target)).replace("\\", "/").lstrip("/")
            if joined in self.paths_set or joined.lower() in self.paths_set_lower:
                return True
        return False

    def _check_command_contradictions(self, doc_path: str, content: str, contradictory: List[str]) -> None:
        # If repo is purely pnpm, but docs suggest npm install or yarn
        has_pnpm_lock = any("pnpm-lock.yaml" in p for p in self.file_paths)
        has_yarn_lock = any("yarn.lock" in p for p in self.file_paths)

        if has_pnpm_lock and not has_yarn_lock:
            if "yarn install" in content:
                contradictory.append(
                    f"{doc_path} references 'yarn install' but project uses pnpm (pnpm-lock.yaml present)."
                )

        # Check for legacy python setup.py install vs pyproject.toml
        if any("pyproject.toml" in p for p in self.file_paths):
            if "python setup.py install" in content:
                contradictory.append(
                    f"{doc_path} recommends deprecated 'python setup.py install' instead of 'pip install -e .'."
                )

    def _generate_governance_drafts(self, missing_gov: List[str]) -> Dict[str, str]:
        drafts = {}
        project_name = self.repo_root.name

        if "CONTRIBUTING.md" in missing_gov:
            drafts["CONTRIBUTING.md"] = (
                f"# Contributing to {project_name}\n\n"
                "Thank you for considering contributing! Please follow these standards:\n\n"
                "1. Fork and create a dedicated feature branch.\n"
                "2. Ensure all tests and lint checks pass before opening a PR.\n"
                "3. Follow existing code style and naming conventions.\n"
                "4. Submit clear pull requests with descriptive commit messages.\n"
            )

        if "SECURITY.md" in missing_gov:
            drafts["SECURITY.md"] = (
                f"# Security Policy for {project_name}\n\n"
                "## Reporting Vulnerabilities\n\n"
                "If you discover a potential security vulnerability, please report it privately.\n"
                "Do NOT open a public issue. Contact project maintainers directly.\n"
            )

        if "CODE_OF_CONDUCT.md" in missing_gov:
            drafts["CODE_OF_CONDUCT.md"] = (
                f"# Contributor Code of Conduct for {project_name}\n\n"
                "We are committed to providing a welcoming, inclusive, and harassment-free environment for everyone.\n"
            )

        if "CHANGELOG.md" in missing_gov:
            drafts["CHANGELOG.md"] = (
                f"# Changelog - {project_name}\n\n"
                "All notable changes to this project will be documented in this file.\n\n"
                "## [Unreleased]\n\n"
                "- Initial project baseline and structure.\n"
            )

        return drafts

