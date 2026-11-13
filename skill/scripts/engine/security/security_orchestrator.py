"""Security Orchestrator for RepoCraft Phase 3.

Main execution coordinator for:
- Secret scanning
- Dependency & supply chain auditing
- Security code patterns
- Configuration & Docker security
- Test discovery, readiness, and safe execution
- CI/CD workflow security
- Risk synthesis and report generation
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

from .cicd_analyzer import audit_cicd
from .configuration_auditor import audit_configuration
from .dependency_auditor import audit_dependencies
from .secret_scanner import scan_secrets
from .security_pattern_analyzer import scan_security_patterns
from .security_report_generator import generate_security_reports
from .security_risk_assessor import assess_overall_security_risk
from .supply_chain_analyzer import audit_supply_chain
from .test_readiness import assess_test_readiness
from .test_runner import execute_test_command
from .types import (
    CicdWorkflowAudit,
    ConfigurationFinding,
    DependencyAuditResult,
    SecretFinding,
    SecurityPatternFinding,
    SupplyChainFinding,
    TestExecutionResult,
    TestExecutionState,
)


def run_security_pipeline(
    target_dir: str,
    reports_dir: str,
    allow_execution: bool = False,
    mode: str = "audit",
) -> Dict[str, Any]:
    """Execute complete Phase 3 security and quality audit pipeline."""
    target_path = Path(target_dir).resolve()
    reports_path = Path(reports_dir).resolve()
    reports_path.mkdir(parents=True, exist_ok=True)

    # 1. Secret Scanning
    secrets = scan_secrets(str(target_path))

    # 2. Dependency Auditing
    dependencies = audit_dependencies(str(target_path))

    # 3. Security Pattern Scanning
    patterns = scan_security_patterns(str(target_path))

    # 4. Configuration & Deployment Auditing
    configurations = audit_configuration(str(target_path))

    # 5. Supply Chain & Integrity Auditing
    supply_chain = audit_supply_chain(str(target_path))

    # 6. Test Discovery & Readiness
    test_analysis = assess_test_readiness(str(target_path))

    # 7. Test Execution (Safe and Controlled)
    test_results: List[TestExecutionResult] = []
    candidate_commands = test_analysis.get("candidate_commands", [])

    if candidate_commands:
        for cmd in candidate_commands:
            res = execute_test_command(
                command=cmd,
                target_dir=str(target_path),
                allow_execution=allow_execution,
            )
            test_results.append(res)
    else:
        test_results.append(
            TestExecutionResult(
                command="none",
                state=TestExecutionState.NOT_RUN,
                exit_code=None,
                duration_seconds=0.0,
                tests_passed=None,
                tests_failed=None,
                tests_skipped=None,
                raw_output_redacted="No test commands or frameworks discovered in repository.",
                error_summary=None,
            )
        )

    # 8. CI/CD Pipeline Auditing
    cicd_audits = audit_cicd(str(target_path))

    # 9. Risk Synthesis
    risk_assessment = assess_overall_security_risk(
        secrets=secrets,
        dependencies=dependencies,
        patterns=patterns,
        configurations=configurations,
        supply_chain=supply_chain,
        test_results=test_results,
        cicd_audits=cicd_audits,
    )

    # 10. Generate Reports & Artifacts
    generated_files = generate_security_reports(
        output_dir=str(reports_path),
        target_dir=str(target_path),
        secrets=secrets,
        dependencies=dependencies,
        patterns=patterns,
        configurations=configurations,
        supply_chain=supply_chain,
        test_analysis=test_analysis,
        test_results=test_results,
        cicd_audits=cicd_audits,
        risk_assessment=risk_assessment,
    )

    return {
        "target_dir": str(target_path),
        "reports_dir": str(reports_path),
        "mode": mode,
        "allow_execution": allow_execution,
        "risk_assessment": risk_assessment,
        "generated_files": generated_files,
        "secrets_count": len(secrets),
        "dependencies_count": len(dependencies),
        "patterns_count": len(patterns),
        "configurations_count": len(configurations),
        "supply_chain_count": len(supply_chain),
        "test_results_count": len(test_results),
        "cicd_audits_count": len(cicd_audits),
    }

