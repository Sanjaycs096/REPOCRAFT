"""Module L — Repair Report Generator for RepoCraft Phase 4.

Generates the 7 required Phase 4 artifacts:
1. repair-findings.json
2. repair-plan.json
3. approval-manifest.json
4. repair-execution.json
5. regression-comparison.json
6. rollback-report.json
7. phase4-report.md
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from .repair_types import (
    NormalizedFinding,
    RegressionComparisonItem,
    RepairStatus,
    RepairTask,
    ValidationResult,
)


def generate_repair_reports(
    output_dir: str,
    target_dir: str,
    mode: str,
    findings: List[NormalizedFinding],
    tasks: List[RepairTask],
    execution_results: List[Dict[str, Any]],
    validation_results: List[ValidationResult],
    regression_items: List[RegressionComparisonItem],
    rollback_results: List[Dict[str, Any]],
    attempt_history: Dict[str, Any],
    ingestion_warnings: List[str],
) -> Dict[str, str]:
    """Generate all 7 Phase 4 artifacts in output_dir."""
    out_path = Path(output_dir).resolve()
    out_path.mkdir(parents=True, exist_ok=True)
    generated: Dict[str, str] = {}

    # 1. repair-findings.json
    findings_data = {
        "total_findings": len(findings),
        "ingestion_warnings": ingestion_warnings,
        "findings": [f.to_dict() for f in findings],
    }
    p1 = out_path / "repair-findings.json"
    p1.write_text(json.dumps(findings_data, indent=2) + "\n", encoding="utf-8")
    generated["repair-findings.json"] = str(p1)

    # 2. repair-plan.json
    plan_data = {
        "total_tasks": len(tasks),
        "tasks": [t.to_dict() for t in tasks],
    }
    p2 = out_path / "repair-plan.json"
    p2.write_text(json.dumps(plan_data, indent=2) + "\n", encoding="utf-8")
    generated["repair-plan.json"] = str(p2)

    # 3. approval-manifest.json
    # (Generated or preserved by ApprovalManager; write/ensure presence)
    p3 = out_path / "approval-manifest.json"
    if not p3.exists():
        manifest_data = {
            "version": "1.0",
            "tasks": [
                {
                    "repair_id": t.repair_id,
                    "title": t.title,
                    "risk_level": t.risk_level.value,
                    "affected_files": t.affected_files,
                    "approval_required": t.approval_required,
                    "approved": False if t.approval_required else True,
                }
                for t in tasks
            ],
        }
        p3.write_text(json.dumps(manifest_data, indent=2) + "\n", encoding="utf-8")
    generated["approval-manifest.json"] = str(p3)

    # 4. repair-execution.json
    exec_data = {
        "mode": mode,
        "total_executions": len(execution_results),
        "executions": execution_results,
    }
    p4 = out_path / "repair-execution.json"
    p4.write_text(json.dumps(exec_data, indent=2) + "\n", encoding="utf-8")
    generated["repair-execution.json"] = str(p4)

    # 5. regression-comparison.json
    reg_data = {
        "total_comparisons": len(regression_items),
        "has_new_failures": any(r.outcome.value == "NEW_FAILURE" for r in regression_items),
        "comparisons": [r.to_dict() for r in regression_items],
    }
    p5 = out_path / "regression-comparison.json"
    p5.write_text(json.dumps(reg_data, indent=2) + "\n", encoding="utf-8")
    generated["regression-comparison.json"] = str(p5)

    # 6. rollback-report.json
    rb_data = {
        "rollbacks_attempted": len(rollback_results),
        "rollbacks": rollback_results,
    }
    p6 = out_path / "rollback-report.json"
    p6.write_text(json.dumps(rb_data, indent=2) + "\n", encoding="utf-8")
    generated["rollback-report.json"] = str(p6)

    # 7. phase4-report.md
    p7 = out_path / "phase4-report.md"
    p7_content = _build_phase4_markdown_report(
        target_dir=target_dir,
        mode=mode,
        findings=findings,
        tasks=tasks,
        execution_results=execution_results,
        validation_results=validation_results,
        regression_items=regression_items,
        rollback_results=rollback_results,
        attempt_history=attempt_history,
        ingestion_warnings=ingestion_warnings,
    )
    p7.write_text(p7_content, encoding="utf-8")
    generated["phase4-report.md"] = str(p7)

    return generated


def _build_phase4_markdown_report(
    target_dir: str,
    mode: str,
    findings: List[NormalizedFinding],
    tasks: List[RepairTask],
    execution_results: List[Dict[str, Any]],
    validation_results: List[ValidationResult],
    regression_items: List[RegressionComparisonItem],
    rollback_results: List[Dict[str, Any]],
    attempt_history: Dict[str, Any],
    ingestion_warnings: List[str],
) -> str:
    applied_count = sum(1 for e in execution_results if e.get("success"))
    blocked_count = sum(1 for e in execution_results if not e.get("success"))

    lines = [
        "# RepoCraft Phase 4 — Bounded Repair & Regression Report",
        "",
        "> [!IMPORTANT]",
        f"> **Execution Mode**: `{mode.upper()}`  ",
        "> **Core Engineering Principle**: Controlled, verifiable improvements only. No unconstrained rewrites.",
        "",
        "## 1. Executive Summary & Scorecard",
        "",
        f"- **Target Project**: `{target_dir}`",
        f"- **Total Ingested Findings**: {len(findings)}",
        f"- **Planned Repair Tasks**: {len(tasks)}",
        f"- **Repairs Applied**: {applied_count}",
        f"- **Repairs Blocked / Skipped**: {blocked_count}",
        f"- **Rollback Operations**: {len(rollback_results)}",
        "",
        "## 2. Input Artifact Coverage & Ingestion",
        "",
    ]

    if ingestion_warnings:
        lines.append("### Ingestion Notes & Warnings")
        for w in ingestion_warnings:
            lines.append(f"- {w}")
        lines.append("")

    lines.extend([
        "## 3. Prioritized Repair Plan",
        "",
        "| ID | Priority | Category | Risk Level | Disposition | Affected Files | Status |",
        "| :--- | :--- | :--- | :--- | :--- | :--- | :--- |",
    ])

    for t in tasks:
        files_str = ", ".join(t.affected_files) if t.affected_files else "-"
        lines.append(
            f"| `{t.repair_id}` | {t.priority} | {t.category.value} | **{t.risk_level.value}** | `{t.disposition.value}` | `{files_str}` | `{t.status.value}` |"
        )

    lines.extend([
        "",
        "## 4. Repair Execution Summary",
        "",
    ])

    if not execution_results:
        lines.append(f"*No repairs applied in '{mode}' mode. Target project files remain completely untouched.*")
    else:
        lines.extend([
            "| Repair ID | Success | Modified Files | Message |",
            "| :--- | :--- | :--- | :--- |",
        ])
        for er in execution_results:
            mfiles = ", ".join(er.get("modified_files", [])) or "-"
            lines.append(
                f"| `{er.get('repair_id')}` | {'**YES**' if er.get('success') else 'NO'} | `{mfiles}` | {er.get('message')} |"
            )

    lines.extend([
        "",
        "## 5. Regression & Validation Analysis",
        "",
    ])

    if not regression_items:
        lines.append("*No dynamic regression tests executed in current mode.*")
    else:
        lines.extend([
            "| Check ID | Description | Baseline | Post-Repair | Outcome |",
            "| :--- | :--- | :--- | :--- | :--- |",
        ])
        for reg in regression_items:
            lines.append(
                f"| `{reg.check_id}` | `{reg.description}` | `{reg.baseline_state.value}` | `{reg.post_repair_state.value}` | **{reg.outcome.value}** |"
            )

    lines.extend([
        "",
        "## 6. Root-Cause Attempt Tracking & Rollbacks",
        "",
        f"- **3-Attempt Policy Active**: Maximum 3 repair attempts per unique root cause across all runs.",
        f"- **Tracked Root Causes**: {len(attempt_history)}",
        f"- **Rollbacks Executed**: {len(rollback_results)}",
        "",
    ])

    if rollback_results:
        for rb in rollback_results:
            lines.append(f"- **Rollback for `{rb.get('repair_id')}`**: State `{rb.get('overall_state')}` ({rb.get('reason')})")

    lines.extend([
        "",
        "## 7. Remaining Risks & Manual Recommendations",
        "",
        "1. **High/Critical Security Risks**: Secrets and cryptography logic must be rotated and refactored by human developers.",
        "2. **Dead Code / Unused Files**: Review candidates manually before deleting any file.",
        "3. **CI/CD Permissions**: Restrict workflow write permissions manually in GitHub repository settings.",
        "",
        "---",
        "*Report automatically generated by RepoCraft Phase 4 Repair & Regression Engine.*",
    ])

    return "\n".join(lines) + "\n"

