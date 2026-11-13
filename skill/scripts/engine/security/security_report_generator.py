"""Security Report Generator for RepoCraft Phase 3.

Generates the 7 required artifacts:
1. security-findings.json
2. dependency-audit.json
3. test-analysis.json
4. test-execution-report.json
5. cicd-audit.json
6. security-quality-report.md
7. phase3-report.md
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from .types import (
    CicdWorkflowAudit,
    ConfigurationFinding,
    DependencyAuditResult,
    SecretFinding,
    SecurityPatternFinding,
    SupplyChainFinding,
    TestDiscoveryItem,
    TestExecutionResult,
)


def generate_security_reports(
    output_dir: str,
    target_dir: str,
    secrets: List[SecretFinding],
    dependencies: List[DependencyAuditResult],
    patterns: List[SecurityPatternFinding],
    configurations: List[ConfigurationFinding],
    supply_chain: List[SupplyChainFinding],
    test_analysis: Dict[str, Any],
    test_results: List[TestExecutionResult],
    cicd_audits: List[CicdWorkflowAudit],
    risk_assessment: Dict[str, Any],
) -> Dict[str, str]:
    """Generate all 7 Phase 3 artifacts in output_dir."""
    out_path = Path(output_dir).resolve()
    out_path.mkdir(parents=True, exist_ok=True)
    generated_files: Dict[str, str] = {}

    # 1. security-findings.json
    sec_findings_data = {
        "summary": risk_assessment["severity_summary"],
        "secrets": [s.to_dict() for s in secrets],
        "code_patterns": [p.to_dict() for p in patterns],
        "configuration": [c.to_dict() for c in configurations],
        "supply_chain": [sc.to_dict() for sc in supply_chain],
    }
    p1 = out_path / "security-findings.json"
    p1.write_text(json.dumps(sec_findings_data, indent=2), encoding="utf-8")
    generated_files["security-findings.json"] = str(p1)

    # 2. dependency-audit.json
    dep_data = {
        "manifests_audited": len(dependencies),
        "total_unpinned": risk_assessment["total_unpinned_dependencies"],
        "missing_lockfiles": risk_assessment["missing_lockfiles_count"],
        "results": [d.to_dict() for d in dependencies],
    }
    p2 = out_path / "dependency-audit.json"
    p2.write_text(json.dumps(dep_data, indent=2), encoding="utf-8")
    generated_files["dependency-audit.json"] = str(p2)

    # 3. test-analysis.json
    p3 = out_path / "test-analysis.json"
    p3.write_text(json.dumps(test_analysis, indent=2), encoding="utf-8")
    generated_files["test-analysis.json"] = str(p3)

    # 4. test-execution-report.json
    test_exec_data = {
        "test_suites_evaluated": len(test_results),
        "results": [t.to_dict() for t in test_results],
    }
    p4 = out_path / "test-execution-report.json"
    p4.write_text(json.dumps(test_exec_data, indent=2), encoding="utf-8")
    generated_files["test-execution-report.json"] = str(p4)

    # 5. cicd-audit.json
    cicd_data = {
        "total_workflows": len(cicd_audits),
        "workflows": [w.to_dict() for w in cicd_audits],
    }
    p5 = out_path / "cicd-audit.json"
    p5.write_text(json.dumps(cicd_data, indent=2), encoding="utf-8")
    generated_files["cicd-audit.json"] = str(p5)

    # 6. security-quality-report.md
    p6 = out_path / "security-quality-report.md"
    p6_content = _build_security_quality_md(
        target_dir,
        risk_assessment,
        secrets,
        dependencies,
        patterns,
        configurations,
        supply_chain,
        test_analysis,
        test_results,
        cicd_audits,
    )
    p6.write_text(p6_content, encoding="utf-8")
    generated_files["security-quality-report.md"] = str(p6)

    # 7. phase3-report.md
    p7 = out_path / "phase3-report.md"
    p7_content = _build_phase3_executive_report(
        target_dir,
        risk_assessment,
        secrets,
        dependencies,
        patterns,
        configurations,
        supply_chain,
        test_results,
        cicd_audits,
    )
    p7.write_text(p7_content, encoding="utf-8")
    generated_files["phase3-report.md"] = str(p7)

    return generated_files


def _build_security_quality_md(
    target_dir: str,
    risk: Dict[str, Any],
    secrets: List[SecretFinding],
    deps: List[DependencyAuditResult],
    patterns: List[SecurityPatternFinding],
    configs: List[ConfigurationFinding],
    sc: List[SupplyChainFinding],
    test_analysis: Dict[str, Any],
    test_results: List[TestExecutionResult],
    cicd: List[CicdWorkflowAudit],
) -> str:
    lines = [
        "# RepoCraft Security & Quality Validation Report",
        "",
        "> [!IMPORTANT]",
        f"> **Overall Risk Assessment**: `{risk['overall_risk_level']}`  ",
        f"> {risk['safety_disclaimer']}",
        "",
        "## 1. Executive Summary & Posture",
        "",
        "| Severity | Findings Count |",
        "| :--- | :--- |",
        f"| **CRITICAL** | {risk['severity_summary']['critical']} |",
        f"| **HIGH** | {risk['severity_summary']['high']} |",
        f"| **MEDIUM** | {risk['severity_summary']['medium']} |",
        f"| **LOW** | {risk['severity_summary']['low']} |",
        f"| **INFO** | {risk['severity_summary']['info']} |",
        "",
        "### Operational Boundaries",
        f"- **Verified Facts**: {risk['boundaries']['verified']}",
        f"- **Inferred Risks**: {risk['boundaries']['inferred']}",
        f"- **Unverified Status**: {risk['boundaries']['unverified']}",
        f"- **Human Approval Required**: {risk['boundaries']['requires_human_approval']}",
        "",
        "## 2. Secret & Sensitive Data Findings",
        "",
    ]

    if not secrets:
        lines.append("*No hardcoded secrets or exposed private credentials detected by static scanner.*")
    else:
        lines.extend([
            "| ID | Rule | Category | Severity | File | Line | Redacted Evidence |",
            "| :--- | :--- | :--- | :--- | :--- | :--- | :--- |",
        ])
        for s in secrets:
            line_str = str(s.line_number) if s.line_number else "-"
            lines.append(
                f"| `{s.finding_id}` | `{s.rule_id}` | {s.category} | **{s.severity.value}** | `{s.file_path}` | {line_str} | `{s.redacted_evidence}` |"
            )

    lines.extend([
        "",
        "## 3. Dependency & Supply Chain Integrity",
        "",
    ])

    if not deps:
        lines.append("*No dependency manifests found in repository.*")
    else:
        lines.extend([
            "| Ecosystem | Manifest | Lockfile Present | Total Dependencies | Unpinned | Status |",
            "| :--- | :--- | :--- | :--- | :--- | :--- |",
        ])
        for d in deps:
            lock_str = "Yes" if d.lockfile_present else "**MISSING**"
            lines.append(
                f"| {d.ecosystem} | `{d.manifest_path}` | {lock_str} | {len(d.dependencies)} | {d.unpinned_count} | `{d.vulnerability_status.value}` |"
            )

    lines.extend([
        "",
        "## 4. Application Security Patterns",
        "",
    ])

    if not patterns:
        lines.append("*No high-risk code patterns (SQLi, command injection, eval, etc.) detected.*")
    else:
        lines.extend([
            "| ID | Category | Severity | File | Line | Impact |",
            "| :--- | :--- | :--- | :--- | :--- | :--- |",
        ])
        for p in patterns:
            line_str = str(p.line_number) if p.line_number else "-"
            lines.append(
                f"| `{p.finding_id}` | {p.category} | **{p.severity.value}** | `{p.file_path}` | {line_str} | {p.potential_impact} |"
            )

    lines.extend([
        "",
        "## 5. Configuration & Deployment Hygiene",
        "",
    ])

    if not configs:
        lines.append("*No configuration or container hygiene issues detected.*")
    else:
        lines.extend([
            "| ID | Category | Severity | File | Issue | Recommended Action |",
            "| :--- | :--- | :--- | :--- | :--- | :--- |",
        ])
        for c in configs:
            lines.append(
                f"| `{c.finding_id}` | {c.category} | **{c.severity.value}** | `{c.file_path}` | {c.issue} | {c.recommended_action} |"
            )

    lines.extend([
        "",
        "## 6. Supply Chain & CI/CD Workflow Security",
        "",
    ])

    if not sc:
        lines.append("*No workflow supply chain security risks detected.*")
    else:
        lines.extend([
            "| ID | Category | Severity | File | Issue |",
            "| :--- | :--- | :--- | :--- | :--- |",
        ])
        for s in sc:
            lines.append(
                f"| `{s.finding_id}` | {s.category} | **{s.severity.value}** | `{s.workflow_path}` | {s.issue} |"
            )

    lines.extend([
        "",
        "## 7. Test Suite Health & Execution Validation",
        "",
        f"- **Total Discovered Test Files**: {test_analysis.get('total_test_files', 0)}",
        f"- **Empty Test Files**: {test_analysis.get('empty_test_files_count', 0)}",
        f"- **Candidate Commands**: {', '.join(test_analysis.get('candidate_commands', [])) or 'None'}",
        f"- **Execution Ready**: {'Yes' if test_analysis.get('is_ready_for_execution') else 'No'}",
        "",
        "### Test Execution Results",
        "",
    ])

    if not test_results:
        lines.append("*No test execution results recorded.*")
    else:
        lines.extend([
            "| Command | State | Exit Code | Duration | Passed | Failed | Skipped |",
            "| :--- | :--- | :--- | :--- | :--- | :--- | :--- |",
        ])
        for tr in test_results:
            p_cnt = str(tr.tests_passed) if tr.tests_passed is not None else "-"
            f_cnt = str(tr.tests_failed) if tr.tests_failed is not None else "-"
            s_cnt = str(tr.tests_skipped) if tr.tests_skipped is not None else "-"
            ec_str = str(tr.exit_code) if tr.exit_code is not None else "-"
            lines.append(
                f"| `{tr.command}` | **{tr.state.value}** | {ec_str} | {tr.duration_seconds:.2f}s | {p_cnt} | {f_cnt} | {s_cnt} |"
            )

    lines.extend([
        "",
        "## 8. CI/CD Pipeline Audit",
        "",
    ])

    if not cicd:
        lines.append("*No CI/CD configuration files identified.*")
    else:
        lines.extend([
            "| Workflow | Triggers | Jobs | Test Step | Build Step | Unpinned Actions | Issues |",
            "| :--- | :--- | :--- | :--- | :--- | :--- | :--- |",
        ])
        for w in cicd:
            trig_str = ", ".join(w.triggers) if w.triggers else "-"
            lines.append(
                f"| `{w.workflow_file}` | {trig_str} | {w.jobs_count} | {'Yes' if w.has_test_step else '**NO**'} | {'Yes' if w.has_build_step else 'No'} | {'**YES**' if w.has_unpinned_actions else 'No'} | {len(w.issues)} |"
            )

    return "\n".join(lines) + "\n"


def _build_phase3_executive_report(
    target_dir: str,
    risk: Dict[str, Any],
    secrets: List[SecretFinding],
    deps: List[DependencyAuditResult],
    patterns: List[SecurityPatternFinding],
    configs: List[ConfigurationFinding],
    sc: List[SupplyChainFinding],
    test_results: List[TestExecutionResult],
    cicd: List[CicdWorkflowAudit],
) -> str:
    lines = [
        "# RepoCraft Phase 3 — Executive Validation Report",
        "",
        "> [!NOTE]",
        "> RepoCraft Phase 3 Validation completed. All findings have been cataloged with strict boundary separation.",
        "",
        "## Summary Scorecard",
        "",
        f"- **Assessed Risk Level**: `{risk['overall_risk_level']}`",
        f"- **Discovered Secrets**: {len(secrets)}",
        f"- **Vulnerable / Unpinned Dependencies**: {risk['total_unpinned_dependencies']} unpinned across {len(deps)} manifests",
        f"- **Code Pattern Findings**: {len(patterns)}",
        f"- **Configuration Findings**: {len(configs)}",
        f"- **Supply Chain Findings**: {len(sc)}",
        f"- **Test Suites Evaluated**: {len(test_results)}",
        f"- **CI/CD Pipelines Audited**: {len(cicd)}",
        "",
        "## Next Steps & Human Verification Required",
        "",
        "1. **Secret Remediation**: If secrets were discovered, revoke and rotate keys immediately; purge git history if committed.",
        "2. **Lockfile Generation**: Generate and commit lockfiles for any manifests currently missing them.",
        "3. **GitHub Actions Pinning**: Pin third-party GitHub Actions to immutable 40-character commit SHAs.",
        "4. **Automated Testing**: Ensure automated tests run on all pull requests and pushes to master/main.",
        "",
        "---",
        "*Report generated automatically by RepoCraft Phase 3 Engine.*",
    ]
    return "\n".join(lines) + "\n"

