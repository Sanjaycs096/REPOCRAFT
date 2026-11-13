"""RepoCraft Phase 3: Security, Testing & CI/CD Validation Engine."""
from __future__ import annotations

from .cicd_analyzer import audit_cicd
from .configuration_auditor import audit_configuration
from .dependency_auditor import audit_dependencies
from .secret_scanner import is_binary_file, redact_string, scan_secrets
from .security_orchestrator import run_security_pipeline
from .security_pattern_analyzer import scan_security_patterns
from .security_report_generator import generate_security_reports
from .security_risk_assessor import assess_overall_security_risk
from .supply_chain_analyzer import audit_supply_chain
from .test_discovery import discover_tests, find_test_files
from .test_readiness import assess_test_readiness
from .test_result_analyzer import analyze_test_output
from .test_runner import execute_test_command, is_command_safe
from .types import (
    CicdWorkflowAudit,
    ConfigurationFinding,
    DependencyAuditResult,
    DependencyItem,
    SecretConfidence,
    SecretFinding,
    SecurityPatternFinding,
    SecuritySeverity,
    SupplyChainFinding,
    TestDiscoveryItem,
    TestExecutionResult,
    TestExecutionState,
    VulnerabilityStatus,
)

__all__ = [
    "SecretConfidence",
    "VulnerabilityStatus",
    "TestExecutionState",
    "SecuritySeverity",
    "SecretFinding",
    "DependencyItem",
    "DependencyAuditResult",
    "SecurityPatternFinding",
    "ConfigurationFinding",
    "SupplyChainFinding",
    "TestDiscoveryItem",
    "TestExecutionResult",
    "CicdWorkflowAudit",
    "scan_secrets",
    "audit_dependencies",
    "scan_security_patterns",
    "audit_configuration",
    "audit_supply_chain",
    "find_test_files",
    "discover_tests",
    "assess_test_readiness",
    "analyze_test_output",
    "is_command_safe",
    "execute_test_command",
    "audit_cicd",
    "assess_overall_security_risk",
    "generate_security_reports",
    "run_security_pipeline",
    "redact_string",
    "is_binary_file",
]

