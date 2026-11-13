"""Report generation module for RepoCraft Repository Intelligence.

Generates the four mandatory Phase 1 output artifacts:
1. inventory.json (machine-readable)
2. repository-overview.md (human-readable)
3. repository-audit.md (structured audit)
4. recommendations.json (machine-readable findings)
"""
from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, List

from .types import (
    ArchitectureObservation,
    DiscoveredCommand,
    EvidenceLevel,
    FileCategory,
    FileInventoryItem,
    GitBaseline,
    GovernanceItem,
    HealthFinding,
    RepositoryIntelligenceReport,
)


class ReportGenerator:
    """Generates deterministic JSON and Markdown reports."""

    def __init__(self, report: RepositoryIntelligenceReport, output_dir: Path):
        self.report = report
        self.output_dir = output_dir

    def generate_all(self) -> Dict[str, Path]:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        results = {}

        results["inventory.json"] = self._generate_inventory_json()
        results["repository-overview.md"] = self._generate_overview_md()
        results["repository-audit.md"] = self._generate_audit_md()
        results["recommendations.json"] = self._generate_recommendations_json()

        return results

    def _generate_inventory_json(self) -> Path:
        out_path = self.output_dir / "inventory.json"
        data = {
            "version": "1.0.0",
            "repository": {
                "root": str(self.report.repo_root),
                "name": self.report.project_name,
                "detected_types": self.report.detected_types,
                "is_monorepo": self.report.is_monorepo,
                "monorepo_packages": self.report.monorepo_packages,
            },
            "technologies": {
                "languages": self.report.languages,
                "frameworks": self.report.frameworks,
                "package_managers": self.report.package_managers,
                "manifests": self.report.manifests,
                "entry_points": self.report.entry_points,
            },
            "file_inventory_summary": self.report.file_inventory_summary,
            "git_baseline": self.report.git_baseline.to_dict(),
            "governance": {
                k: {
                    "item_type": v.item_type,
                    "relative_path": v.relative_path,
                    "exists": v.exists,
                    "is_empty": v.is_empty,
                    "size_bytes": v.size_bytes,
                    "confidence": v.confidence.value,
                    "notes": v.notes,
                }
                for k, v in self.report.governance.items()
            },
            "test_and_cicd_discovery": {
                "discovered_commands": [
                    {
                        "gate_name": c.gate_name,
                        "command": c.command,
                        "source_file": c.source_file,
                        "verified": c.verified,
                    }
                    for c in self.report.discovered_commands
                ],
                "workflows": self.report.cicd_workflows,
            },
            "safe_warnings": self.report.safe_warnings,
        }
        out_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        return out_path

    def _generate_recommendations_json(self) -> Path:
        out_path = self.output_dir / "recommendations.json"
        data = {
            "version": "1.0.0",
            "repository": self.report.project_name,
            "total_findings": len(self.report.findings),
            "findings": [
                {
                    "finding_id": f.finding_id,
                    "category": f.category,
                    "severity": f.severity.value,
                    "confidence": f.evidence_level.value,
                    "evidence": f.evidence,
                    "explanation": f.explanation,
                    "suggested_action": f.suggested_action,
                    "requires_approval": f.requires_approval,
                    "target_phase": f.target_phase,
                }
                for f in self.report.findings
            ],
        }
        out_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        return out_path

    def _generate_overview_md(self) -> Path:
        out_path = self.output_dir / "repository-overview.md"
        r = self.report
        lines = [
            f"# Repository Overview: {r.project_name}",
            "",
            "## 1. Project Purpose & Classification",
            f"- **Primary Classification:** {', '.join(r.detected_types) if r.detected_types else 'General Software Repository'}",
            f"- **Monorepo:** {'Yes (' + str(len(r.monorepo_packages)) + ' packages)' if r.is_monorepo else 'No'}",
            f"- **Repository Path:** `{r.repo_root}`",
            "",
            "## 2. Technology Stack",
            f"- **Languages:** {', '.join(r.languages) if r.languages else 'None detected'}",
            f"- **Frameworks & Libraries:** {', '.join(r.frameworks) if r.frameworks else 'None detected'}",
            f"- **Package Managers:** {', '.join(r.package_managers) if r.package_managers else 'None detected'}",
            f"- **Manifests Discovered:** {', '.join(r.manifests) if r.manifests else 'None'}",
            "",
            "## 3. Architecture & Structure",
        ]

        for dim_key, obs in r.architecture.items():
            lines.append(f"### {obs.dimension}")
            lines.append(f"- **Classification:** `{obs.classification}` ({obs.evidence_level.value})")
            if obs.details:
                lines.append(f"- **Details:** {obs.details}")
            if obs.evidence_sources:
                lines.append(f"- **Evidence Sources:** {', '.join(obs.evidence_sources)}")
            lines.append("")

        lines.extend([
            "## 4. Key Directories & Entry Points",
            f"- **Source Directories:** {', '.join(r.source_directories) if r.source_directories else 'Root-level'}",
            f"- **Test Directories:** {', '.join(r.test_directories) if r.test_directories else 'None verified'}",
            f"- **Asset Directories:** {', '.join(r.asset_directories) if r.asset_directories else 'None verified'}",
            f"- **Application Entry Points:** {', '.join(r.entry_points) if r.entry_points else 'None verified'}",
            "",
            "## 5. Build, Testing & CI/CD Strategy",
        ])

        if r.discovered_commands:
            lines.append("Discovered build and test commands (unverified in Phase 1):")
            for cmd in r.discovered_commands:
                lines.append(f"- **{cmd.gate_name}:** `{cmd.command}` (source: `{cmd.source_file}`)")
        else:
            lines.append("- *No automated test or build commands discovered in project manifests.*")

        lines.append("")
        if r.cicd_workflows:
            lines.append(f"CI/CD Workflows: {', '.join(r.cicd_workflows)}")
        else:
            lines.append("- *No CI/CD pipeline workflows detected.*")

        lines.append("")
        out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return out_path

    def _generate_audit_md(self) -> Path:
        out_path = self.output_dir / "repository-audit.md"
        r = self.report
        lines = [
            f"# Repository Health & Baseline Audit: {r.project_name}",
            "",
            "## Executive Summary",
            f"- **Project Type:** {', '.join(r.detected_types) if r.detected_types else 'Unclassified'}",
            f"- **Total Tracked/Inventoried Files:** {r.file_inventory_summary.get('total_files', 0)}",
            f"- **Git Status:** {'Git Repository' if r.git_baseline.is_git_repository else 'Non-Git Directory'} "
            f"({r.git_baseline.current_branch or 'N/A'})",
            f"- **Pre-existing User Changes:** {r.git_baseline.pre_existing_modifications_count} file(s)",
            f"- **Total Audit Findings:** {len(r.findings)}",
            "",
            "## 1. Git State & Worktree Safety",
        ]

        if r.git_baseline.is_git_repository:
            lines.extend([
                f"- **Current Branch:** `{r.git_baseline.current_branch}`",
                f"- **HEAD Commit:** `{r.git_baseline.head_commit_short or r.git_baseline.head_commit or 'None'}`",
                f"- **Author / Date:** {r.git_baseline.head_commit_author or 'Unknown'} / {r.git_baseline.head_commit_date or 'Unknown'}",
                f"- **Detached HEAD:** {r.git_baseline.is_detached_head}",
                f"- **Shallow Clone:** {r.git_baseline.is_shallow}",
                f"- **Submodules:** {r.git_baseline.has_submodules}",
                f"- **Remotes:** {', '.join(f'{rm.name} ({rm.url})' for rm in r.git_baseline.remotes) if r.git_baseline.remotes else 'None'}",
                f"- **Staged Changes (User):** {len(r.git_baseline.staged_files)}",
                f"- **Unstaged Changes (User):** {len(r.git_baseline.unstaged_files)}",
                f"- **Untracked Files (User):** {len(r.git_baseline.untracked_files)}",
            ])
            if r.git_baseline.warning:
                lines.append(f"> [!WARNING]\n> {r.git_baseline.warning}")
        else:
            lines.append("- *Target directory is not a Git repository.*")

        lines.extend([
            "",
            "## 2. Documentation & Governance Review",
            "| Resource | Status | Path | Size | Confidence |",
            "| :--- | :--- | :--- | :--- | :--- |",
        ])

        for key, g in sorted(r.governance.items()):
            status_str = "Present" if g.exists and not g.is_empty else ("Empty" if g.exists else "Missing")
            path_str = f"`{g.relative_path}`" if g.relative_path else "N/A"
            size_str = f"{g.size_bytes} B" if g.exists else "0 B"
            lines.append(f"| {g.item_type} | {status_str} | {path_str} | {size_str} | {g.confidence.value} |")

        lines.extend([
            "",
            "## 3. File Inventory Summary",
        ])
        for cat_name, count in sorted(r.file_inventory_summary.get("category_counts", {}).items()):
            lines.append(f"- **{cat_name.capitalize()}:** {count} files")
        if r.file_inventory_summary.get("excluded_directories"):
            lines.append(f"- **Excluded Standard Trees:** {', '.join(r.file_inventory_summary['excluded_directories'])}")

        lines.extend([
            "",
            "## 4. Prioritized Health Findings & Recommendations",
            "| ID | Severity | Category | Confidence | Recommended Action | Approval Required | Target Phase |",
            "| :--- | :--- | :--- | :--- | :--- | :--- | :--- |",
        ])

        if r.findings:
            for f in r.findings:
                lines.append(
                    f"| {f.finding_id} | `{f.severity.value}` | {f.category} | {f.evidence_level.value} | {f.suggested_action} | {f.requires_approval} | Phase {f.target_phase} |"
                )

            lines.append("")
            lines.append("### Finding Details")
            for f in r.findings:
                lines.extend([
                    f"#### {f.finding_id}: {f.suggested_action}",
                    f"- **Severity:** `{f.severity.value}` | **Category:** {f.category} | **Confidence:** `{f.evidence_level.value}`",
                    f"- **Evidence:** {f.evidence}",
                    f"- **Explanation:** {f.explanation}",
                    f"- **Action:** {f.suggested_action}",
                    f"- **Approval Required:** {'Yes' if f.requires_approval else 'No'} | **Target Maintenance Phase:** Phase {f.target_phase}",
                    "",
                ])
        else:
            lines.append("- *No health issues or hygiene concerns detected.*")

        lines.extend([
            "## 5. Unknowns and Limitations",
        ])
        if r.unknowns_and_limitations:
            for item in r.unknowns_and_limitations:
                lines.append(f"- {item}")
        else:
            lines.append("- Static analysis only. Dynamic execution, dependency security audits, and penetration tests were not performed.")

        lines.append("")
        out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return out_path
