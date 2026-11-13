"""Module B — Repair Classifier & Risk Assessor for RepoCraft Phase 4.

Classifies normalized findings into RepairCategory and RepairRiskLevel,
and determines execution disposition (AUTONOMOUS_CANDIDATE, APPROVAL_REQUIRED,
MANUAL_REMEDIATION, NOT_ACTIONABLE, BLOCKED).
"""
from __future__ import annotations

from typing import Tuple

from .repair_types import ExecutionDisposition, NormalizedFinding, RepairCategory, RepairRiskLevel

# Categories that represent critical risk operations
CRITICAL_CATEGORIES = {
    "SECRET_EXPOSURE",
    "CRYPTOGRAPHY",
    "AUTH_AND_AUTHZ",
    "PRODUCTION_DEPLOYMENT",
    "LICENSE_AND_LEGAL",
}

# Categories that represent high risk operations
HIGH_CATEGORIES = {
    "APPLICATION_SECURITY",
    "SUPPLY_CHAIN",
    "DOCKERFILE",
    "CICD_WORKFLOW_IMPROVEMENT",
    "DEPENDENCY_VULNERABILITY",
}

# Categories that represent medium risk operations
MEDIUM_CATEGORIES = {
    "CONFIGURATION",
    "DEPENDENCY_CONFIGURATION",
    "NAMING_AND_ORGANIZATION",
    "TEST_FAILURE_CORRECTION",
}

# Categories that represent low risk operations
LOW_CATEGORIES = {
    "DOCUMENTATION_CORRECTION",
    "README_IMPROVEMENT",
    "CODE_FORMATTING",
    "DEAD_CODE_REVIEW",
    "GITHUB_PRESENTATION",
}


def classify_finding(finding: NormalizedFinding) -> Tuple[RepairCategory, RepairRiskLevel, ExecutionDisposition]:
    """Classify normalized finding into category, risk level, and execution disposition."""
    cat_str = finding.category.lower()
    desc_lower = finding.description.lower()

    # 1. Determine RepairCategory
    category = RepairCategory.SAFE_CONFIGURATION_CORRECTION
    if "doc" in cat_str:
        category = RepairCategory.DOCUMENTATION_CORRECTION
    elif "readme" in cat_str:
        category = RepairCategory.README_IMPROVEMENT
    elif "format" in cat_str or "lint" in cat_str:
        category = RepairCategory.CODE_FORMATTING
    elif "org" in cat_str:
        category = RepairCategory.NAMING_AND_ORGANIZATION
    elif "unused" in cat_str or "dead_code" in cat_str:
        category = RepairCategory.DEAD_CODE_REVIEW
    elif "secret" in cat_str:
        category = RepairCategory.SECURITY_HARDENING
    elif "crypto" in cat_str:
        category = RepairCategory.CRYPTOGRAPHY
    elif "auth" in cat_str:
        category = RepairCategory.AUTH_AND_AUTHZ
    elif "dep" in cat_str:
        category = RepairCategory.DEPENDENCY_CONFIGURATION
    elif "ci" in cat_str or "workflow" in cat_str:
        category = RepairCategory.CICD_WORKFLOW_IMPROVEMENT
    elif "docker" in cat_str:
        category = RepairCategory.SAFE_CONFIGURATION_CORRECTION
    elif "test" in cat_str:
        category = RepairCategory.TEST_FAILURE_CORRECTION
    elif "license" in cat_str:
        category = RepairCategory.LICENSE_AND_LEGAL
    elif "presentation" in cat_str or "brand" in cat_str:
        category = RepairCategory.GITHUB_PRESENTATION
    # Secondary heuristics based on description if category was generic
    elif "broken" in desc_lower or "link" in desc_lower:
        category = RepairCategory.DOCUMENTATION_CORRECTION
    elif "readme" in desc_lower:
        category = RepairCategory.README_IMPROVEMENT
    elif "nesting" in desc_lower or "move" in desc_lower:
        category = RepairCategory.NAMING_AND_ORGANIZATION
    elif "unused" in desc_lower:
        category = RepairCategory.DEAD_CODE_REVIEW
    elif "secret" in desc_lower or "credential" in desc_lower:
        category = RepairCategory.SECURITY_HARDENING
    elif "crypto" in desc_lower or "hashlib" in desc_lower:
        category = RepairCategory.CRYPTOGRAPHY
    elif "auth" in desc_lower or "permission" in desc_lower:
        category = RepairCategory.AUTH_AND_AUTHZ
    elif "lockfile" in desc_lower or "package" in desc_lower:
        category = RepairCategory.DEPENDENCY_CONFIGURATION
    elif "action" in desc_lower:
        category = RepairCategory.CICD_WORKFLOW_IMPROVEMENT

    # 2. Determine Risk Level
    # Strict hierarchy:
    # - If secret, crypto, auth/authz, license rewrite, or destructive: CRITICAL
    # - If application security, supply chain, CI/CD, dependency upgrade: HIGH
    # - If organization, file moves, non-prod config: MEDIUM
    # - If documentation, readme command fix, formatting: LOW
    if (
        category in (RepairCategory.CRYPTOGRAPHY, RepairCategory.LICENSE_AND_LEGAL, RepairCategory.AUTH_AND_AUTHZ)
        or finding.severity == "CRITICAL"
        or "secret" in desc_lower
        or "credential" in desc_lower
        or "revoke" in desc_lower
    ):
        risk_level = RepairRiskLevel.CRITICAL
    elif (
        category in (
            RepairCategory.SECURITY_HARDENING,
            RepairCategory.CICD_WORKFLOW_IMPROVEMENT,
            RepairCategory.DEPENDENCY_VULNERABILITY,
        )
        or finding.severity == "HIGH"
        or "docker" in desc_lower
        or "injection" in desc_lower
    ):
        risk_level = RepairRiskLevel.HIGH
    elif (
        category in (
            RepairCategory.NAMING_AND_ORGANIZATION,
            RepairCategory.DEPENDENCY_CONFIGURATION,
            RepairCategory.TEST_FAILURE_CORRECTION,
            RepairCategory.SAFE_CONFIGURATION_CORRECTION,
            RepairCategory.MISSING_CONFIGURATION,
        )
        or finding.severity == "MEDIUM"
        or "move" in desc_lower
        or "rename" in desc_lower
    ):
        risk_level = RepairRiskLevel.MEDIUM
    else:
        risk_level = RepairRiskLevel.LOW

    # 3. Determine Execution Disposition
    if risk_level == RepairRiskLevel.CRITICAL:
        # Never autonomously apply CRITICAL changes
        disposition = ExecutionDisposition.MANUAL_REMEDIATION
    elif risk_level == RepairRiskLevel.HIGH:
        # High risk always requires explicit approval
        disposition = ExecutionDisposition.APPROVAL_REQUIRED
    elif risk_level == RepairRiskLevel.MEDIUM:
        # Medium risk requires approval unless explicitly pre-authorized
        disposition = ExecutionDisposition.APPROVAL_REQUIRED
    else:
        # LOW risk: Check if narrowly scoped, high confidence, and has concrete proposed remediation
        if finding.confidence == "HIGH" and finding.affected_files and finding.proposed_remediation:
            disposition = ExecutionDisposition.AUTONOMOUS_CANDIDATE
        else:
            disposition = ExecutionDisposition.APPROVAL_REQUIRED

    # Special constraints:
    # Dead code / unused files: Never automatically delete!
    if category == RepairCategory.DEAD_CODE_REVIEW:
        disposition = ExecutionDisposition.MANUAL_REMEDIATION

    # License changes: Never autonomously select/replace license
    if category == RepairCategory.LICENSE_AND_LEGAL:
        disposition = ExecutionDisposition.MANUAL_REMEDIATION

    return category, risk_level, disposition
