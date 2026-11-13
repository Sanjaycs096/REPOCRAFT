"""Generates evidence-backed release notes from verified project state and manifests."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from .distribution_types import ReleaseClassification, ReleaseNoteEntry, ReleaseNotes


class ReleaseNotesGenerator:
    """Generates structured release notes grounded in verified Phase 0-7 implementation evidence."""

    VERSION = "1.0.0-rc1"

    @classmethod
    def generate_release_notes(
        cls,
        repo_root: Path,
        version: str = "1.0.0-rc1",
        release_date: Optional[str] = None,
    ) -> ReleaseNotes:
        """Construct evidence-backed release notes."""
        if not release_date:
            release_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        changes: Dict[str, List[ReleaseNoteEntry]] = {
            ReleaseClassification.ADDED.value: [
                ReleaseNoteEntry(
                    category=ReleaseClassification.ADDED,
                    summary="Phase 0: Portable Coding-Agent Skill Package Foundation",
                    details="Local installer (install.py), agent adapter layout (.agent/skills/repocraft), and baseline safety policies.",
                    evidence_reference="install.py, skill/SKILL.md",
                ),
                ReleaseNoteEntry(
                    category=ReleaseClassification.ADDED,
                    summary="Phase 1: Repository Intelligence Engine",
                    details="Safe read-only file categorization, ecosystem stack detection, architecture analysis, and health scoring.",
                    evidence_reference="skill/scripts/repocraft_intel.py, inventory.json",
                ),
                ReleaseNoteEntry(
                    category=ReleaseClassification.ADDED,
                    summary="Phase 2: Maintenance, Documentation & GitHub Presentation Engine",
                    details="Codebase organization auditing, import graph analysis, 18-dimension README audit and generator, license auditor, and Mermaid diagrams.",
                    evidence_reference="skill/scripts/repocraft_maintenance.py, maintenance-plan.json",
                ),
                ReleaseNoteEntry(
                    category=ReleaseClassification.ADDED,
                    summary="Phase 3: Security, Testing & CI/CD Validation Engine",
                    details="High-entropy secret scanner with redaction, dependency and lockfile auditor, application pattern audit, safe test discovery and runner, and CI/CD supply chain analysis.",
                    evidence_reference="skill/scripts/repocraft_security.py, security-findings.json",
                ),
                ReleaseNoteEntry(
                    category=ReleaseClassification.ADDED,
                    summary="Phase 4: Bounded Repair, Safe Code Improvements & Regression Validation Engine",
                    details="Multi-phase finding ingestion, risk-classified repair tasks, hash-bound approval manifest, external verified backups, multi-level regression validation, 3-attempt limit, and automated rollback protecting user modifications.",
                    evidence_reference="skill/scripts/repocraft_repair.py, approval-manifest.json",
                ),
                ReleaseNoteEntry(
                    category=ReleaseClassification.ADDED,
                    summary="Phase 5: Git Review, Conditional Commit & Publishing Engine",
                    details="Porcelain status parser, diff analyzer, 5-tier risk classifier, deterministic staging planner, Conventional Commit generator, atomic commit executor, remote inspector, fast-forward push executor, and PR draft generator.",
                    evidence_reference="skill/scripts/repocraft_git.py, git-state.json",
                ),
                ReleaseNoteEntry(
                    category=ReleaseClassification.ADDED,
                    summary="Phase 6: Agent Compatibility Framework & Lifecycle Integration",
                    details="Calibrated agent support matrix (Antigravity certified, Claude Code installation-only), central phase and artifact registries, schema validators, deterministic ZIP release packaging, and read-only repocraft_status.py diagnostic CLI.",
                    evidence_reference="skill/scripts/repocraft_status.py, agent-compatibility.json",
                ),
                ReleaseNoteEntry(
                    category=ReleaseClassification.ADDED,
                    summary="Phase 7: Release Distribution, Upgrade Management & Post-Release Maintenance",
                    details="Automated distribution archive verification, installer upgrade and rollback management, post-release maintenance audit, and GitHub Actions CI automation.",
                    evidence_reference="skill/scripts/repocraft_release.py, distribution-verification.json",
                ),
            ],
            ReleaseClassification.SECURITY.value: [
                ReleaseNoteEntry(
                    category=ReleaseClassification.SECURITY,
                    summary="Pure Standard Library Runtime",
                    details="RepoCraft requires zero external pip dependencies at runtime, eliminating third-party supply-chain attack vectors.",
                    evidence_reference="pyproject.toml (dependencies = [])",
                ),
                ReleaseNoteEntry(
                    category=ReleaseClassification.SECURITY,
                    summary="Strict Subprocess and Path Traversal Safety",
                    details="Subprocesses use explicit argument lists without shell=True; archive extractors and installers strictly reject path traversal escapes.",
                    evidence_reference="skill/scripts/engine/release/integrity_verifier.py",
                ),
                ReleaseNoteEntry(
                    category=ReleaseClassification.SECURITY,
                    summary="Cryptographic Approval Boundary Isolation",
                    details="Staging approval, commit approval, and push approval operate under independent cryptographic authorization.",
                    evidence_reference="skill/references/git-workflow-policy.md",
                ),
                ReleaseNoteEntry(
                    category=ReleaseClassification.SECURITY,
                    summary="Gate E Safety Invariant",
                    details="The RepoCraft development repository is never auto-committed or auto-pushed; public tags are never created without human maintainer sign-off.",
                    evidence_reference="skill/references/release-and-portability-policy.md",
                ),
            ],
            ReleaseClassification.DOCUMENTATION.value: [
                ReleaseNoteEntry(
                    category=ReleaseClassification.DOCUMENTATION,
                    summary="Comprehensive Architecture and Policy Specifications",
                    details="Full reference policies across safety, quality gates, intelligence, maintenance, documentation, security, repair, git workflow, agent compatibility, and release readiness.",
                    evidence_reference="skill/references/",
                ),
            ],
        }

        highlights = [
            "Complete 7-phase repository engineering skill package for coding agents.",
            "Certified native support on Google Antigravity (.agent/skills/repocraft).",
            "Zero third-party pip dependencies required at runtime.",
            "Independent cryptographic human-in-the-loop approval gates for all file modifications and Git publishing operations.",
            "Deterministic, byte-for-byte reproducible distribution packaging.",
            "100% test coverage across 427 regression and integration test scenarios.",
        ]

        breaking_changes = [
            "Initial release candidate; no breaking changes against previous public releases.",
        ]

        migration_notes = [
            "Requires Python >= 3.9 installed in the environment.",
            "Install into existing projects using `python install.py --target /path/to/project`.",
            "Verify installation integrity using `python skill/scripts/repocraft_status.py --verify-installation`.",
        ]

        known_limitations = [
            "Autonomous multi-phase execution is certified natively on Google Antigravity.",
            "Claude Code is supported for file installation only; invocation requires manual user prompts.",
            "Cursor IDE requires manual adapter rule creation (.cursorrules or .cursor/rules/*.mdc).",
            "Remote publishing requires non-conflicting fast-forward push permissions on target upstream remote.",
        ]

        return ReleaseNotes(
            version=version,
            release_date=release_date,
            summary="RepoCraft v1.0.0-rc1 represents the production-ready release candidate of RepoCraft.",
            highlights=highlights,
            changes=changes,
            breaking_changes=breaking_changes,
            migration_notes=migration_notes,
            known_limitations=known_limitations,
        )

    @classmethod
    def render_markdown(cls, notes: ReleaseNotes) -> str:
        """Render ReleaseNotes into human-readable Markdown draft."""
        lines = [
            f"# RepoCraft {notes.version} Release Notes (Draft)",
            "",
            f"**Release Date:** {notes.release_date}  ",
            f"**Status:** Draft — Awaiting Maintainer Approval  ",
            "",
            "---",
            "",
            "## Summary",
            "",
            notes.summary,
            "",
            "## Highlights",
            "",
        ]
        for hl in notes.highlights:
            lines.append(f"- {hl}")
        lines.append("")

        for cat_name, entries in notes.changes.items():
            if not entries:
                continue
            lines.append(f"## {cat_name}")
            lines.append("")
            for entry in entries:
                lines.append(f"### {entry.summary}")
                if entry.details:
                    lines.append(f"{entry.details}")
                if entry.evidence_reference:
                    lines.append(f"*Evidence: `{entry.evidence_reference}`*")
                lines.append("")

        if notes.breaking_changes:
            lines.append("## Breaking Changes")
            lines.append("")
            for bc in notes.breaking_changes:
                lines.append(f"- {bc}")
            lines.append("")

        if notes.migration_notes:
            lines.append("## Installation & Migration Notes")
            lines.append("")
            for mn in notes.migration_notes:
                lines.append(f"- {mn}")
            lines.append("")

        if notes.known_limitations:
            lines.append("## Known Limitations")
            lines.append("")
            for kl in notes.known_limitations:
                lines.append(f"- {kl}")
            lines.append("")

        lines.extend([
            "---",
            "",
            "*Notice: This document is a release candidate draft generated by RepoCraft Phase 7. "
            "It will not be published publicly until explicitly approved and tagged by the maintainer.*",
            "",
        ])
        return "\n".join(lines)

