"""Data models and enums for RepoCraft Phase 3 Security, Testing & CI/CD Validation Engine."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class SecretConfidence(str, Enum):
    CONFIRMED_SECRET = "CONFIRMED_SECRET"
    LIKELY_SECRET = "LIKELY_SECRET"
    POSSIBLE_SECRET = "POSSIBLE_SECRET"
    SENSITIVE_FILE_EXPOSURE = "SENSITIVE_FILE_EXPOSURE"
    NO_MATCH_FOUND = "NO_MATCH_FOUND"


class VulnerabilityStatus(str, Enum):
    VULNERABLE = "VULNERABLE"
    NO_KNOWN_MATCH = "NO_KNOWN_MATCH"
    UNVERIFIED = "UNVERIFIED"
    UNSUPPORTED = "UNSUPPORTED"
    ANALYSIS_ERROR = "ANALYSIS_ERROR"


class TestExecutionState(str, Enum):
    __test__ = False
    NOT_RUN = "NOT_RUN"
    PASSED = "PASSED"
    FAILED = "FAILED"
    TIMED_OUT = "TIMED_OUT"
    BLOCKED_BY_POLICY = "BLOCKED_BY_POLICY"
    MISSING_DEPENDENCIES = "MISSING_DEPENDENCIES"
    EXECUTION_ERROR = "EXECUTION_ERROR"


class SecuritySeverity(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"


@dataclass
class SecretFinding:
    finding_id: str
    rule_id: str
    category: str
    confidence: SecretConfidence
    severity: SecuritySeverity
    file_path: str
    line_number: Optional[int]
    redacted_evidence: str
    explanation: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "finding_id": self.finding_id,
            "rule_id": self.rule_id,
            "category": self.category,
            "confidence": self.confidence.value,
            "severity": self.severity.value,
            "file_path": self.file_path,
            "line_number": self.line_number,
            "redacted_evidence": self.redacted_evidence,
            "explanation": self.explanation,
        }


@dataclass
class DependencyItem:
    name: str
    version_constraint: str
    resolved_version: Optional[str] = None
    is_dev: bool = False
    ecosystem: str = "unknown"
    source: str = "registry"
    is_unpinned: bool = False
    is_suspicious_source: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class DependencyAuditResult:
    manifest_path: str
    lockfile_path: Optional[str]
    lockfile_present: bool
    ecosystem: str
    dependencies: List[DependencyItem]
    unpinned_count: int
    suspicious_sources_count: int
    vulnerability_status: VulnerabilityStatus
    vulnerabilities: List[Dict[str, Any]] = field(default_factory=list)
    notes: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "manifest_path": self.manifest_path,
            "lockfile_path": self.lockfile_path,
            "lockfile_present": self.lockfile_present,
            "ecosystem": self.ecosystem,
            "dependencies": [d.to_dict() for d in self.dependencies],
            "unpinned_count": self.unpinned_count,
            "suspicious_sources_count": self.suspicious_sources_count,
            "vulnerability_status": self.vulnerability_status.value,
            "vulnerabilities": self.vulnerabilities,
            "notes": self.notes,
        }


@dataclass
class SecurityPatternFinding:
    finding_id: str
    rule_id: str
    category: str
    severity: SecuritySeverity
    confidence: str  # HIGH, MEDIUM, LOW
    file_path: str
    line_number: Optional[int]
    redacted_evidence: str
    explanation: str
    potential_impact: str
    recommended_remediation: str
    requires_manual_verification: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "finding_id": self.finding_id,
            "rule_id": self.rule_id,
            "category": self.category,
            "severity": self.severity.value,
            "confidence": self.confidence,
            "file_path": self.file_path,
            "line_number": self.line_number,
            "redacted_evidence": self.redacted_evidence,
            "explanation": self.explanation,
            "potential_impact": self.potential_impact,
            "recommended_remediation": self.recommended_remediation,
            "requires_manual_verification": self.requires_manual_verification,
        }


@dataclass
class ConfigurationFinding:
    finding_id: str
    category: str
    severity: SecuritySeverity
    file_path: str
    line_number: Optional[int]
    issue: str
    explanation: str
    recommended_action: str
    requires_approval: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "finding_id": self.finding_id,
            "category": self.category,
            "severity": self.severity.value,
            "file_path": self.file_path,
            "line_number": self.line_number,
            "issue": self.issue,
            "explanation": self.explanation,
            "recommended_action": self.recommended_action,
            "requires_approval": self.requires_approval,
        }


@dataclass
class SupplyChainFinding:
    finding_id: str
    category: str
    severity: SecuritySeverity
    workflow_path: str
    line_number: Optional[int]
    issue: str
    explanation: str
    recommendation: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "finding_id": self.finding_id,
            "category": self.category,
            "severity": self.severity.value,
            "workflow_path": self.workflow_path,
            "line_number": self.line_number,
            "issue": self.issue,
            "explanation": self.explanation,
            "recommendation": self.recommendation,
        }


@dataclass
class TestDiscoveryItem:
    __test__ = False
    framework: str
    command: str
    source_file: str
    test_type: str  # unit, integration, e2e, lint, typecheck, build
    test_files_count: int

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class TestExecutionResult:
    __test__ = False
    command: str
    state: TestExecutionState
    exit_code: Optional[int] = None
    duration_seconds: float = 0.0
    tests_passed: Optional[int] = None
    tests_failed: Optional[int] = None
    tests_skipped: Optional[int] = None
    raw_output_redacted: str = ""
    error_summary: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "command": self.command,
            "state": self.state.value,
            "exit_code": self.exit_code,
            "duration_seconds": round(self.duration_seconds, 2),
            "tests_passed": self.tests_passed,
            "tests_failed": self.tests_failed,
            "tests_skipped": self.tests_skipped,
            "raw_output_redacted": self.raw_output_redacted,
            "error_summary": self.error_summary,
        }


@dataclass
class CicdWorkflowAudit:
    workflow_file: str
    triggers: List[str]
    jobs_count: int
    has_test_step: bool
    has_build_step: bool
    has_lint_step: bool
    has_unpinned_actions: bool
    has_broad_permissions: bool
    has_risky_pr_triggers: bool
    issues: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
