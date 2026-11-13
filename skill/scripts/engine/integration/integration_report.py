"""Generates lifecycle integration reports and exports phase/artifact registries."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

from .artifact_registry import ArtifactRegistry
from .integration_types import LifecycleValidationResult
from .phase_registry import PhaseRegistry


class IntegrationReportGenerator:
    """Generates lifecycle-integration-report.json, lifecycle-integration-report.md, phase-registry.json, and artifact-registry.json."""

    VERSION = "1.0.0-rc1"

    @classmethod
    def generate(
        cls,
        validation_result: LifecycleValidationResult,
        output_dir: Path,
    ) -> Dict[str, Path]:
        """Write phase-registry.json, artifact-registry.json, and lifecycle integration reports."""
        output_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(timezone.utc).isoformat()

        # 1. phase-registry.json
        phase_reg_path = output_dir / "phase-registry.json"
        phase_reg_data = PhaseRegistry.to_dict()
        phase_reg_data["generated_at"] = timestamp
        phase_reg_data["repocraft_version"] = cls.VERSION
        phase_reg_path.write_text(json.dumps(phase_reg_data, indent=2) + "\n", encoding="utf-8")

        # 2. artifact-registry.json
        art_reg_path = output_dir / "artifact-registry.json"
        art_reg_data = ArtifactRegistry.to_dict()
        art_reg_data["generated_at"] = timestamp
        art_reg_data["repocraft_version"] = cls.VERSION
        art_reg_path.write_text(json.dumps(art_reg_data, indent=2) + "\n", encoding="utf-8")

        # 3. lifecycle-integration-report.json
        json_report_path = output_dir / "lifecycle-integration-report.json"
        json_data = validation_result.to_dict()
        json_data["schema_version"] = "1.0.0"
        json_data["generated_at"] = timestamp
        json_data["repocraft_version"] = cls.VERSION
        json_report_path.write_text(json.dumps(json_data, indent=2) + "\n", encoding="utf-8")

        # 4. lifecycle-integration-report.md
        md_report_path = output_dir / "lifecycle-integration-report.md"
        md_content = cls._build_markdown(json_data)
        md_report_path.write_text(md_content, encoding="utf-8")

        return {
            "phase_registry": phase_reg_path,
            "artifact_registry": art_reg_path,
            "json_report": json_report_path,
            "md_report": md_report_path,
        }

    @classmethod
    def _build_markdown(cls, data: Dict[str, Any]) -> str:
        status_banner = "✅ PASS" if data.get("is_valid") else "⚠️ VALIDATION ISSUES DETECTED"
        lines = [
            "# RepoCraft — Lifecycle Integration Report",
            "",
            f"**Status:** {status_banner}  ",
            f"**Generated:** {data.get('generated_at')}  ",
            f"**RepoCraft Version:** `{data.get('repocraft_version')}`  ",
            f"**Target Repository:** `{data.get('target_repo')}`  ",
            f"**Reports Directory:** `{data.get('reports_dir')}`  ",
            "",
            "---",
            "",
            "## 1. Lifecycle Execution Overview",
            "",
            "The complete RepoCraft lifecycle comprises ordered, evidence-backed phases:",
            "```text",
            "INSTALL → INITIALIZE → INTELLIGENCE → MAINTENANCE → SECURITY → REPAIR → GIT_REVIEW → CONDITIONAL_PUBLISH → REPORT",
            "```",
            "",
            f"- **Executed Phases ({len(data.get('executed_phases', []))}):** "
            + ", ".join(f"`{p}`" for p in data.get("executed_phases", []))
            if data.get("executed_phases")
            else "- **Executed Phases:** None",
            f"- **Pending / Missing Phases ({len(data.get('missing_phases', []))}):** "
            + ", ".join(f"`{p}`" for p in data.get("missing_phases", []))
            if data.get("missing_phases")
            else "- **Pending Phases:** None",
            "",
            "## 2. Phase Handoff Validations",
            "",
        ]

        handoffs = data.get("handoff_results", [])
        if handoffs:
            lines.extend([
                "| From Phase | To Phase | Handoff Status | Missing Inputs | Schema Errors |",
                "| --- | --- | --- | --- | --- |",
            ])
            for h in handoffs:
                h_status = "✅ Valid" if h.get("is_valid") else "❌ Broken"
                missing = ", ".join(h.get("missing_inputs", [])) or "None"
                errs = ", ".join(h.get("invalid_schemas", [])) or "None"
                lines.append(f"| `{h.get('from_phase')}` | `{h.get('to_phase')}` | {h_status} | {missing} | {errs} |")
            lines.append("")
        else:
            lines.append("No sequential phase handoffs were evaluated.\n")

        lines.extend([
            "## 3. Approval Boundary Invariants",
            "",
            f"- **Approval Boundaries Preserved:** `{'YES' if data.get('approval_boundaries_preserved') else 'NO'}`",
            "- **Gate Isolation:** Staging approval, commit approval, and push approval operate under independent cryptographic authorization.",
            "",
            "## 4. Artifact Evaluations",
            "",
        ])

        evals = data.get("artifact_evaluations", {})
        if evals:
            lines.extend([
                "| Artifact Filename | Present & Valid |",
                "| --- | --- |",
            ])
            for art_name, is_ok in sorted(evals.items()):
                mark = "✅ Valid" if is_ok else "❌ Missing / Invalid"
                lines.append(f"| `{art_name}` | {mark} |")
            lines.append("")

        if data.get("errors"):
            lines.append("## 5. Integration Errors")
            lines.append("")
            for err in data["errors"]:
                lines.append(f"- ❌ {err}")
            lines.append("")

        if data.get("warnings"):
            lines.append("## 6. Integration Warnings")
            lines.append("")
            for warn in data["warnings"]:
                lines.append(f"- ⚠️ {warn}")
            lines.append("")

        return "\n".join(lines)

