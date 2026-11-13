"""Phase 2 Maintenance Orchestrator for RepoCraft.

Coordinates codebase organization analysis, unused-file detection, README auditing
and generation, documentation and license audits, media and GitHub presentation review,
and safe maintenance planning. Produces the six required Phase 2 artifacts.
"""
from __future__ import annotations

import json
import os
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ..orchestrator import IntelligenceEngine
from .documentation_auditor import DocumentationAuditor
from .github_presentation import GitHubPresentationAuditor
from .license_auditor import LicenseAuditor
from .maintenance_planner import MaintenancePlanner, MaintenanceTask
from .media_auditor import MediaAuditor
from .organization_analyzer import OrganizationAnalyzer
from .readme_analyzer import ReadmeAnalyzer
from .readme_generator import ReadmeGenerator
from .reference_analyzer import ReferenceAnalyzer
from .unused_file_detector import UnusedFileDetector


class MaintenanceOrchestrator:
    """End-to-end engine for Phase 2 repository maintenance and presentation."""

    def __init__(
        self,
        target_dir: Path,
        reports_dir: Optional[Path] = None,
        mode: str = "audit",  # audit, draft, apply
    ):
        self.target_dir = target_dir.resolve()
        if reports_dir:
            self.reports_dir = reports_dir.resolve()
        else:
            self.reports_dir = (self.target_dir.parent / "repocraft-reports").resolve()
        self.mode = mode.lower() if mode else "audit"
        if self.mode not in ("audit", "draft", "apply"):
            self.mode = "audit"

    def run(self) -> Tuple[Dict[str, Any], Dict[str, Path]]:
        self.reports_dir.mkdir(parents=True, exist_ok=True)

        # 1. Ensure Phase 1 inventory and baseline are available
        inv_file = self.reports_dir / "inventory.json"
        if not inv_file.is_file():
            # Run Phase 1 engine to generate base artifacts
            intel_engine = IntelligenceEngine(target_dir=self.target_dir, output_dir=self.reports_dir)
            intel_engine.run()

        inventory_data = json.loads(inv_file.read_text(encoding="utf-8", errors="replace"))

        # Extract file paths from target repo
        file_paths, file_categories, file_sizes = self._collect_repo_files()

        # 2. Reference & Unused File Analysis
        ref_analyzer = ReferenceAnalyzer(self.target_dir, file_paths)
        ref_map = ref_analyzer.analyze_references()
        referenced_paths = {p for p, refs in ref_map.items() if len(refs) > 0}

        unused_detector = UnusedFileDetector(self.target_dir, file_paths, file_categories, file_sizes)
        unused_candidates = unused_detector.detect_unused_files()

        # 3. Organization Analysis
        org_analyzer = OrganizationAnalyzer(self.target_dir, file_paths, file_categories)
        org_findings, org_stats = org_analyzer.analyze()

        # 4. README Analysis & Draft Generation
        readme_analyzer = ReadmeAnalyzer(self.target_dir)
        readme_audit = readme_analyzer.analyze()

        existing_readme_content = ""
        if readme_analyzer.readme_path and readme_analyzer.readme_path.is_file():
            existing_readme_content = readme_analyzer.readme_path.read_text(encoding="utf-8", errors="replace")

        overview_path = self.reports_dir / "repository-overview.md"
        overview_text = overview_path.read_text(encoding="utf-8", errors="replace") if overview_path.is_file() else ""

        readme_gen = ReadmeGenerator(
            self.target_dir, inventory_data, overview_text, existing_readme_content
        )
        improved_readme_draft = readme_gen.generate_draft()

        # 5. Documentation & License Audits
        pms = inventory_data.get("technologies", {}).get("package_managers", [])
        doc_auditor = DocumentationAuditor(self.target_dir, file_paths, pms)
        doc_audit = doc_auditor.audit()

        license_auditor = LicenseAuditor(self.target_dir, file_paths)
        license_audit = license_auditor.audit()

        # 6. Media & GitHub Presentation Audits
        detected_types = inventory_data.get("repository", {}).get("detected_types", [])
        media_auditor = MediaAuditor(self.target_dir, file_paths, detected_types)
        media_audit = media_auditor.audit(referenced_paths)

        languages = inventory_data.get("technologies", {}).get("languages", [])
        frameworks = inventory_data.get("technologies", {}).get("frameworks", [])
        presentation_auditor = GitHubPresentationAuditor(
            self.target_dir, file_paths, languages, frameworks, detected_types, existing_readme_content
        )
        presentation_audit = presentation_auditor.audit()

        # 7. Synthesize Maintenance Plan
        phase1_recs = []
        recs_file = self.reports_dir / "recommendations.json"
        if recs_file.is_file():
            try:
                recs_data = json.loads(recs_file.read_text(encoding="utf-8", errors="replace"))
                phase1_recs = recs_data.get("findings", [])
            except Exception:
                pass

        planner = MaintenancePlanner(
            phase1_findings=phase1_recs,
            org_findings=org_findings,
            unused_files=unused_candidates,
            readme_audit=readme_audit,
            doc_audit=doc_audit,
            license_audit=license_audit,
            presentation_audit=presentation_audit,
        )
        maintenance_tasks = planner.create_plan()

        # 8. Handle Execution Mode Safeguards
        applied_changes: List[str] = []
        if self.mode == "apply":
            applied_changes = self._apply_safe_changes_with_safeguards(
                readme_audit, improved_readme_draft, inventory_data
            )

        # 9. Emit the 6 Required Artifacts
        artifacts = self._generate_artifacts(
            org_findings=org_findings,
            org_stats=org_stats,
            unused_candidates=unused_candidates,
            ref_map=ref_map,
            readme_audit=readme_audit,
            improved_readme_draft=improved_readme_draft,
            doc_audit=doc_audit,
            license_audit=license_audit,
            media_audit=media_audit,
            presentation_audit=presentation_audit,
            maintenance_tasks=maintenance_tasks,
            inventory_data=inventory_data,
            applied_changes=applied_changes,
        )

        summary_data = {
            "mode": self.mode,
            "target": str(self.target_dir),
            "reports_dir": str(self.reports_dir),
            "total_organization_findings": len(org_findings),
            "unused_file_candidates": len(unused_candidates),
            "readme_score": readme_audit.overall_score,
            "broken_doc_links": len(doc_audit.broken_links),
            "missing_doc_images": len(doc_audit.missing_images),
            "has_license": license_audit.has_license_file,
            "branding_score": presentation_audit.branding_score,
            "total_maintenance_tasks": len(maintenance_tasks),
            "applied_changes_count": len(applied_changes),
        }

        return summary_data, artifacts

    def _collect_repo_files(self) -> Tuple[List[str], Dict[str, str], Dict[str, int]]:
        file_paths = []
        file_categories = {}
        file_sizes = {}

        # Load from file_inventory if possible or scan
        for root, dirs, files in os.walk(str(self.target_dir), followlinks=False):
            # Prune excluded directories
            for d in list(dirs):
                if d in (
                    ".git", "node_modules", ".next", "dist", "build", "coverage",
                    ".venv", "venv", "__pycache__", ".gradle", "vendor", ".turbo",
                ):
                    dirs.remove(d)

            for f in files:
                full_path = Path(root) / f
                try:
                    rel = full_path.relative_to(self.target_dir).as_posix()
                    size = full_path.stat().st_size
                    file_paths.append(rel)
                    file_sizes[rel] = size

                    # Category mapping
                    ext = full_path.suffix.lower()
                    if ext in (".py", ".js", ".ts", ".tsx", ".jsx", ".java", ".go", ".rs", ".c", ".cpp", ".cs"):
                        file_categories[rel] = "source"
                    elif ext in (".md", ".rst", ".txt"):
                        file_categories[rel] = "documentation"
                    elif ext in (".png", ".jpg", ".jpeg", ".svg", ".gif", ".webp", ".ico"):
                        file_categories[rel] = "assets"
                    elif ext in (".json", ".yaml", ".yml", ".toml", ".ini"):
                        file_categories[rel] = "configuration"
                    else:
                        file_categories[rel] = "unknown"
                except Exception:
                    continue

        file_paths.sort()
        return file_paths, file_categories, file_sizes

    def _apply_safe_changes_with_safeguards(
        self,
        readme_audit: Any,
        improved_readme_draft: str,
        inventory_data: Dict[str, Any],
    ) -> List[str]:
        """Applies safe, policy-authorized changes under strict Git and user safeguards."""
        applied: List[str] = []
        from ..git_analyzer import analyze_git_baseline

        current_git = analyze_git_baseline(self.target_dir)
        user_modified_paths = {
            Path(p).as_posix().lower()
            for p in (current_git.staged_files + current_git.unstaged_files + current_git.untracked_files)
        }

        # 1. Apply README only if user authorization applies and original has NO pre-existing changes
        readme_target = self.target_dir / "README.md"
        if not readme_target.is_file():
            # Missing README: safe to create from draft
            readme_target.write_text(improved_readme_draft, encoding="utf-8")
            applied.append("Created missing README.md from evidence-backed draft.")
        else:
            # If original README is in user modified paths, NEVER touch it!
            if "readme.md" in user_modified_paths:
                # Stop: user has active modifications on README
                pass
            else:
                # Preserve backup before touching
                backup_path = readme_target.with_name("README.md.backup")
                suffix = 1
                while backup_path.exists():
                    backup_path = readme_target.with_name(f"README.md.backup-{suffix}")
                    suffix += 1
                shutil.copyfile(readme_target, backup_path)
                readme_target.write_text(improved_readme_draft, encoding="utf-8")
                applied.append(f"Updated README.md (original backed up to {backup_path.name}).")

        return applied

    def _generate_artifacts(
        self,
        org_findings: List[Any],
        org_stats: Dict[str, Any],
        unused_candidates: List[Any],
        ref_map: Dict[str, Set[str]],
        readme_audit: Any,
        improved_readme_draft: str,
        doc_audit: Any,
        license_audit: Any,
        media_audit: Any,
        presentation_audit: Any,
        maintenance_tasks: List[MaintenanceTask],
        inventory_data: Dict[str, Any],
        applied_changes: List[str],
    ) -> Dict[str, Path]:
        artifacts: Dict[str, Path] = {}

        # Artifact A: maintenance-analysis.json
        p_a = self.reports_dir / "maintenance-analysis.json"
        data_a = {
            "version": "1.0.0",
            "repository": self.target_dir.name,
            "organization_statistics": org_stats,
            "organization_findings": [f.to_dict() for f in org_findings],
            "unused_file_candidates": [u.to_dict() for u in unused_candidates],
            "reference_analysis_summary": {
                "total_tracked_files": len(ref_map),
                "unreferenced_files_count": sum(1 for refs in ref_map.values() if len(refs) == 0),
            },
        }
        p_a.write_text(json.dumps(data_a, indent=2) + "\n", encoding="utf-8")
        artifacts["maintenance-analysis.json"] = p_a

        # Artifact B: README-improved.md
        p_b = self.reports_dir / "README-improved.md"
        p_b.write_text(improved_readme_draft, encoding="utf-8")
        artifacts["README-improved.md"] = p_b

        # Artifact C: documentation-audit.md
        p_c = self.reports_dir / "documentation-audit.md"
        lines_c = [
            f"# Documentation & Governance Audit: {self.target_dir.name}",
            "",
            "## 1. Documentation Inventory",
            f"- **Total Documents:** {len(doc_audit.docs_inventory)}",
            f"- **Tracked Documents:** {', '.join(f'`{d}`' for d in doc_audit.docs_inventory) if doc_audit.docs_inventory else 'None'}",
            "",
            "## 2. Link & Image Integrity",
            f"- **Broken Internal Links:** {len(doc_audit.broken_links)}",
            f"- **Missing Local Images:** {len(doc_audit.missing_images)}",
            "",
        ]
        if doc_audit.broken_links:
            lines_c.append("### Broken Links Detail")
            for bl in doc_audit.broken_links:
                lines_c.append(f"- In `{bl.doc_path}`: `[{bl.link_text}]({bl.link_target})` -> Target not found.")
            lines_c.append("")
        if doc_audit.missing_images:
            lines_c.append("### Missing Local Images Detail")
            for mi in doc_audit.missing_images:
                lines_c.append(f"- In `{mi.doc_path}`: `![{mi.link_text}]({mi.link_target})` -> Image file missing.")
            lines_c.append("")

        lines_c.extend([
            "## 3. Governance Policies",
            f"- **Missing Governance Documents:** {', '.join(doc_audit.missing_governance) if doc_audit.missing_governance else 'All standard policies present'}",
            "",
            "## 4. Licensing Audit",
            f"- **License File Present:** {license_audit.has_license_file} (`{license_audit.license_path or 'N/A'}`)",
            f"- **Detected License Type:** `{license_audit.detected_license_type}`",
            f"- **Copyright Holders:** {', '.join(license_audit.copyright_holders) if license_audit.copyright_holders else 'None declared'}",
            f"- **Manifest License Declarations:** {json.dumps(license_audit.manifest_declarations)}",
            f"- **Inconsistencies:** {'; '.join(license_audit.inconsistencies) if license_audit.inconsistencies else 'None'}",
            "",
        ])
        if doc_audit.contradictory_commands:
            lines_c.append("## 5. Contradictory Commands & Outdated Instructions")
            for cc in doc_audit.contradictory_commands:
                lines_c.append(f"- {cc}")
            lines_c.append("")
        p_c.write_text("\n".join(lines_c) + "\n", encoding="utf-8")
        artifacts["documentation-audit.md"] = p_c

        # Artifact D: github-presentation-audit.md
        p_d = self.reports_dir / "github-presentation-audit.md"
        lines_d = [
            f"# GitHub Presentation & Branding Audit: {self.target_dir.name}",
            "",
            "## 1. Branding & Visual Identity",
            f"- **Branding Score:** {presentation_audit.branding_score}/100",
            f"- **Project Logo:** {'Present' if presentation_audit.has_logo else 'Missing'}",
            f"- **OpenGraph Social Preview:** {'Present' if presentation_audit.has_social_preview else 'Missing'}",
            f"- **Total Media Assets:** {len(media_audit.media_files)} ({media_audit.total_media_size_bytes} bytes)",
            f"- **Oversized Media (>2MB):** {len(media_audit.oversized_media)}",
            f"- **Duplicate Media Files:** {len(media_audit.duplicate_media)}",
            "",
            "## 2. Repository Metadata Recommendations",
            f"- **Recommended About Description:** `{presentation_audit.recommended_description}`",
            f"- **Recommended Topics/Tags:** {', '.join(presentation_audit.recommended_topics)}",
            "",
            "## 3. Architecture Visualization",
            presentation_audit.mermaid_architecture_diagram,
            "",
            "## 4. Presentation Action Policy",
            f"- **Remote Metadata Actions Blocked:** {presentation_audit.remote_actions_blocked} (Phase 2 Safety Boundary)",
            "",
        ]
        p_d.write_text("\n".join(lines_d) + "\n", encoding="utf-8")
        artifacts["github-presentation-audit.md"] = p_d

        # Artifact E: maintenance-plan.json
        p_e = self.reports_dir / "maintenance-plan.json"
        data_e = {
            "version": "1.0.0",
            "repository": self.target_dir.name,
            "total_tasks": len(maintenance_tasks),
            "tasks": [t.to_dict() for t in maintenance_tasks],
        }
        p_e.write_text(json.dumps(data_e, indent=2) + "\n", encoding="utf-8")
        artifacts["maintenance-plan.json"] = p_e

        # Artifact F: phase2-report.md
        p_f = self.reports_dir / "phase2-report.md"
        lines_f = [
            f"# Phase 2 Maintenance & Presentation Report: {self.target_dir.name}",
            "",
            "## Executive Summary",
            f"- **Execution Mode:** `{self.mode.upper()}`",
            f"- **Total Maintenance Tasks Identified:** {len(maintenance_tasks)}",
            f"- **README Quality Score:** {readme_audit.overall_score}/100",
            f"- **Branding & Presentation Score:** {presentation_audit.branding_score}/100",
            f"- **Changes Applied to Target:** {len(applied_changes)} file(s)",
            "",
            "## Summary of Findings by Module",
            f"- **Codebase Organization:** {len(org_findings)} finding(s), {len(unused_candidates)} unused-file candidate(s).",
            f"- **README & Docs:** {len(doc_audit.broken_links)} broken link(s), {len(doc_audit.missing_images)} missing image(s).",
            f"- **Licensing:** License type `{license_audit.detected_license_type}`. {len(license_audit.inconsistencies)} inconsistency(ies).",
            f"- **GitHub Presentation:** {len(presentation_audit.recommendations)} recommendation(s). Remote actions safely blocked.",
            "",
            "## Actions Applied in Current Execution",
        ]
        if applied_changes:
            for ac in applied_changes:
                lines_f.append(f"- {ac}")
        else:
            lines_f.append("- *No files in target project were modified (read-only audit/draft mode).*")

        lines_f.extend([
            "",
            "## Generated Phase 2 Artifacts",
            f"- `maintenance-analysis.json`: {p_a}",
            f"- `README-improved.md`: {p_b}",
            f"- `documentation-audit.md`: {p_c}",
            f"- `github-presentation-audit.md`: {p_d}",
            f"- `maintenance-plan.json`: {p_e}",
            f"- `phase2-report.md`: {p_f}",
            "",
            "## Safety & Limitations",
            "- Uncertain files were NOT deleted automatically.",
            "- Pre-existing user modifications were preserved untouched.",
            "- Remote GitHub API calls were blocked in Phase 2.",
        ])
        p_f.write_text("\n".join(lines_f) + "\n", encoding="utf-8")
        artifacts["phase2-report.md"] = p_f

        return artifacts
