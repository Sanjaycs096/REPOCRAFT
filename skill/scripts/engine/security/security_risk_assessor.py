"""Module J — Security & Quality Risk Assessor for RepoCraft Phase 3.

Synthesizes findings across:
- Secret scanning
- Dependency & supply chain auditing
- Code security patterns
- Configuration & Docker security
- Test discovery & execution results
- CI/CD workflow security

Enforces core safety principles:
- Never claims a repository is '100% secure'
- Explicitly separates verified vs inferred vs unverified items
- Flags high-risk findings requiring human approval
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from .types import (
    CicdWorkflowAudit,
    ConfigurationFinding,
    DependencyAuditResult,
    SecretConfidence,
    SecretFinding,
    SecurityPatternFinding,
    SecuritySeverity,
    SupplyChainFinding,
    TestExecutionResult,
)


def assess_overall_security_risk(
    secrets: List[SecretFinding],
    dependencies: List[DependencyAuditResult],
    patterns: List[SecurityPatternFinding],
    configurations: List[ConfigurationFinding],
    supply_chain: List[SupplyChainFinding],
    test_results: List[TestExecutionResult],
    cicd_audits: List[CicdWorkflowAudit],
) -> Dict[str, Any]:
    """Calculate overall risk assessment and aggregate posture summary."""
    # Count severities across all findings
    counts = {
        "critical": 0,
        "high": 0,
        "medium": 0,
        "low": 0,
        "info": 0,
    }

    # Secret counts
    for s in secrets:
        counts[s.severity.value.lower()] += 1

    # Pattern counts
    for p in patterns:
        counts[p.severity.value.lower()] += 1

    # Config counts
    for c in configurations:
        counts[c.severity.value.lower()] += 1

    # Supply chain counts
    for sc in supply_chain:
        counts[sc.severity.value.lower()] += 1

    # Dependency hygiene issues
    total_unpinned = sum(d.unpinned_count for d in dependencies)
    missing_lockfiles = sum(1 for d in dependencies if not d.lockfile_present)

    # Test status
    tests_failed_count = 0
    tests_passed_count = 0
    for t in test_results:
        if t.tests_failed:
            tests_failed_count += t.tests_failed
        if t.tests_passed:
            tests_passed_count += t.tests_passed

    # Determine risk level
    if counts["critical"] > 0:
        risk_level = "CRITICAL"
    elif counts["high"] > 0 or tests_failed_count > 0:
        risk_level = "HIGH"
    elif counts["medium"] > 0 or missing_lockfiles > 0 or total_unpinned > 5:
        risk_level = "MEDIUM"
    elif counts["low"] > 0:
        risk_level = "LOW"
    else:
        risk_level = "MINIMAL_DETECTED_RISK"

    # Distinguish verified, inferred, unverified, and human approval boundaries
    return {
        "overall_risk_level": risk_level,
        "is_safe_claim_allowed": False,  # Engine policy: Never claim 100% safe
        "safety_disclaimer": "Absence of detected security patterns does NOT guarantee security. This audit reflects static heuristics and local execution results only.",
        "severity_summary": counts,
        "secrets_count": len(secrets),
        "code_pattern_findings_count": len(patterns),
        "configuration_findings_count": len(configurations),
        "supply_chain_findings_count": len(supply_chain),
        "dependency_audits_count": len(dependencies),
        "total_unpinned_dependencies": total_unpinned,
        "missing_lockfiles_count": missing_lockfiles,
        "test_suites_evaluated": len(test_results),
        "tests_passed_total": tests_passed_count,
        "tests_failed_total": tests_failed_count,
        "cicd_workflows_count": len(cicd_audits),
        "boundaries": {
            "verified": "Pattern matches in local static files, lockfile existence, and executed test runner return codes.",
            "inferred": "Likelihood of secret exposures based on regex entropy, framework conventions, and CI trigger risks.",
            "unverified": "Third-party CVE databases and live network vulnerability status (evaluated offline by default).",
            "requires_human_approval": "Secret revocation/rotation, dependency updates, and CI workflow permission changes.",
        },
    }

