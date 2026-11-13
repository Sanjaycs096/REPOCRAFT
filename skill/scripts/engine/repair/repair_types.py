"""Data models, enums, and dataclasses for RepoCraft Phase 4 Repair & Regression Engine."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class RepairRiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class RepairCategory(str, Enum):
    DOCUMENTATION_CORRECTION = "DOCUMENTATION_CORRECTION"
    README_IMPROVEMENT = "README_IMPROVEMENT"
    CODE_FORMATTING = "CODE_FORMATTING"
    NAMING_AND_ORGANIZATION = "NAMING_AND_ORGANIZATION"
    DEAD_CODE_REVIEW = "DEAD_CODE_REVIEW"
    MISSING_CONFIGURATION = "MISSING_CONFIGURATION"
    SAFE_CONFIGURATION_CORRECTION = "SAFE_CONFIGURATION_CORRECTION"
    TEST_FAILURE_CORRECTION = "TEST_FAILURE_CORRECTION"
    TYPE_AND_LINT_CORRECTION = "TYPE_AND_LINT_CORRECTION"
    DEPENDENCY_CONFIGURATION = "DEPENDENCY_CONFIGURATION"
    DEPENDENCY_VULNERABILITY = "DEPENDENCY_VULNERABILITY"
    SECURITY_HARDENING = "SECURITY_HARDENING"
    CICD_WORKFLOW_IMPROVEMENT = "CICD_WORKFLOW_IMPROVEMENT"
    AUTH_AND_AUTHZ = "AUTH_AND_AUTHZ"
    CRYPTOGRAPHY = "CRYPTOGRAPHY"
    PRODUCTION_DEPLOYMENT = "PRODUCTION_DEPLOYMENT"
    LICENSE_AND_LEGAL = "LICENSE_AND_LEGAL"
    GITHUB_PRESENTATION = "GITHUB_PRESENTATION"


class RepairStatus(str, Enum):
    FINDING_DETECTED = "FINDING_DETECTED"
    REPAIR_RECOMMENDED = "REPAIR_RECOMMENDED"
    REPAIR_PLANNED = "REPAIR_PLANNED"
    APPROVAL_REQUIRED = "APPROVAL_REQUIRED"
    REPAIR_AUTHORIZED = "REPAIR_AUTHORIZED"
    REPAIR_APPLIED = "REPAIR_APPLIED"
    VALIDATION_PASSED = "VALIDATION_PASSED"
    VALIDATION_FAILED = "VALIDATION_FAILED"
    REPAIR_ROLLED_BACK = "REPAIR_ROLLED_BACK"
    REPAIR_BLOCKED = "REPAIR_BLOCKED"
    MAX_ATTEMPTS_REACHED = "MAX_ATTEMPTS_REACHED"


class ExecutionDisposition(str, Enum):
    AUTONOMOUS_CANDIDATE = "AUTONOMOUS_CANDIDATE"
    APPROVAL_REQUIRED = "APPROVAL_REQUIRED"
    MANUAL_REMEDIATION = "MANUAL_REMEDIATION"
    NOT_ACTIONABLE = "NOT_ACTIONABLE"
    BLOCKED = "BLOCKED"


class ValidationState(str, Enum):
    NOT_RUN = "NOT_RUN"
    PASSED = "PASSED"
    FAILED = "FAILED"
    TIMED_OUT = "TIMED_OUT"
    BLOCKED_BY_POLICY = "BLOCKED_BY_POLICY"
    MISSING_DEPENDENCIES = "MISSING_DEPENDENCIES"
    EXECUTION_ERROR = "EXECUTION_ERROR"


class RegressionOutcome(str, Enum):
    NEW_FAILURE = "NEW_FAILURE"
    PRE_EXISTING_FAILURE = "PRE_EXISTING_FAILURE"
    RESOLVED_FAILURE = "RESOLVED_FAILURE"
    UNCHANGED_FAILURE = "UNCHANGED_FAILURE"
    NEW_WARNING = "NEW_WARNING"
    RESOLVED_WARNING = "RESOLVED_WARNING"
    UNVERIFIED = "UNVERIFIED"


class RollbackState(str, Enum):
    ROLLBACK_COMPLETED = "ROLLBACK_COMPLETED"
    ROLLBACK_NOT_REQUIRED = "ROLLBACK_NOT_REQUIRED"
    ROLLBACK_BLOCKED_USER_MODIFICATION = "ROLLBACK_BLOCKED_USER_MODIFICATION"
    ROLLBACK_FAILED = "ROLLBACK_FAILED"
    ROLLBACK_BACKUP_MISSING = "ROLLBACK_BACKUP_MISSING"


@dataclass
class NormalizedFinding:
    stable_id: str
    source_id: str
    source_phase: str
    category: str
    severity: str
    confidence: str
    description: str
    evidence: str
    affected_files: List[str]
    proposed_remediation: str
    approval_required: bool
    validation_requirements: List[str]
    current_status: RepairStatus = RepairStatus.FINDING_DETECTED

    def to_dict(self) -> Dict[str, Any]:
        return {
            "stable_id": self.stable_id,
            "source_id": self.source_id,
            "source_phase": self.source_phase,
            "category": self.category,
            "severity": self.severity,
            "confidence": self.confidence,
            "description": self.description,
            "evidence": self.evidence,
            "affected_files": self.affected_files,
            "proposed_remediation": self.proposed_remediation,
            "approval_required": self.approval_required,
            "validation_requirements": self.validation_requirements,
            "current_status": self.current_status.value,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> NormalizedFinding:
        return cls(
            stable_id=data["stable_id"],
            source_id=data["source_id"],
            source_phase=data["source_phase"],
            category=data["category"],
            severity=data["severity"],
            confidence=data["confidence"],
            description=data["description"],
            evidence=data["evidence"],
            affected_files=data.get("affected_files", []),
            proposed_remediation=data.get("proposed_remediation", ""),
            approval_required=data.get("approval_required", True),
            validation_requirements=data.get("validation_requirements", []),
            current_status=RepairStatus(data.get("current_status", RepairStatus.FINDING_DETECTED.value)),
        )


@dataclass
class ProposedPatch:
    file_path: str
    diff_or_description: str
    patch_type: str  # "text_replace", "file_create", "line_replace"
    target_text: Optional[str] = None
    replacement_text: Optional[str] = None
    full_content: Optional[str] = None
    original_content_hash: Optional[str] = None
    new_content_hash: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ProposedPatch:
        return cls(**data)


@dataclass
class RepairTask:
    repair_id: str
    source_finding_ids: List[str]
    title: str
    description: str
    category: RepairCategory
    severity: str
    confidence: str
    risk_level: RepairRiskLevel
    affected_files: List[str]
    proposed_changes: List[ProposedPatch]
    expected_benefit: str
    potential_side_effects: str
    dependencies: List[str]
    approval_required: bool
    validation_commands: List[str]
    rollback_strategy: str
    estimated_scope: str  # "LINE", "BLOCK", "FILE"
    priority: int
    disposition: ExecutionDisposition
    status: RepairStatus = RepairStatus.REPAIR_PLANNED
    root_cause_key: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "repair_id": self.repair_id,
            "source_finding_ids": self.source_finding_ids,
            "title": self.title,
            "description": self.description,
            "category": self.category.value,
            "severity": self.severity,
            "confidence": self.confidence,
            "risk_level": self.risk_level.value,
            "affected_files": self.affected_files,
            "proposed_changes": [p.to_dict() for p in self.proposed_changes],
            "expected_benefit": self.expected_benefit,
            "potential_side_effects": self.potential_side_effects,
            "dependencies": self.dependencies,
            "approval_required": self.approval_required,
            "validation_commands": self.validation_commands,
            "rollback_strategy": self.rollback_strategy,
            "estimated_scope": self.estimated_scope,
            "priority": self.priority,
            "disposition": self.disposition.value,
            "status": self.status.value,
            "root_cause_key": self.root_cause_key,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> RepairTask:
        return cls(
            repair_id=data["repair_id"],
            source_finding_ids=data.get("source_finding_ids", []),
            title=data["title"],
            description=data["description"],
            category=RepairCategory(data["category"]),
            severity=data["severity"],
            confidence=data["confidence"],
            risk_level=RepairRiskLevel(data["risk_level"]),
            affected_files=data.get("affected_files", []),
            proposed_changes=[ProposedPatch.from_dict(p) for p in data.get("proposed_changes", [])],
            expected_benefit=data.get("expected_benefit", ""),
            potential_side_effects=data.get("potential_side_effects", ""),
            dependencies=data.get("dependencies", []),
            approval_required=data.get("approval_required", True),
            validation_commands=data.get("validation_commands", []),
            rollback_strategy=data.get("rollback_strategy", ""),
            estimated_scope=data.get("estimated_scope", "FILE"),
            priority=data.get("priority", 10),
            disposition=ExecutionDisposition(data["disposition"]),
            status=RepairStatus(data.get("status", RepairStatus.REPAIR_PLANNED.value)),
            root_cause_key=data.get("root_cause_key", ""),
        )


@dataclass
class BackupRecord:
    repair_id: str
    file_path: str
    backup_path: str
    original_sha256: str
    post_change_sha256: Optional[str] = None
    timestamp: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> BackupRecord:
        return cls(**data)


@dataclass
class ValidationResult:
    level: str  # "patch_integrity", "local_validation", "project_quality_gates", "full_regression"
    command: str
    state: ValidationState
    exit_code: Optional[int] = None
    duration_seconds: float = 0.0
    output_redacted: str = ""
    error_summary: Optional[str] = None
    passed: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "level": self.level,
            "command": self.command,
            "state": self.state.value,
            "exit_code": self.exit_code,
            "duration_seconds": round(self.duration_seconds, 2),
            "output_redacted": self.output_redacted,
            "error_summary": self.error_summary,
            "passed": self.passed,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ValidationResult:
        return cls(
            level=data["level"],
            command=data["command"],
            state=ValidationState(data["state"]),
            exit_code=data.get("exit_code"),
            duration_seconds=data.get("duration_seconds", 0.0),
            output_redacted=data.get("output_redacted", ""),
            error_summary=data.get("error_summary"),
            passed=data.get("passed", False),
        )


@dataclass
class RegressionComparisonItem:
    check_id: str
    description: str
    baseline_state: ValidationState
    post_repair_state: ValidationState
    outcome: RegressionOutcome

    def to_dict(self) -> Dict[str, Any]:
        return {
            "check_id": self.check_id,
            "description": self.description,
            "baseline_state": self.baseline_state.value,
            "post_repair_state": self.post_repair_state.value,
            "outcome": self.outcome.value,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> RegressionComparisonItem:
        return cls(
            check_id=data["check_id"],
            description=data["description"],
            baseline_state=ValidationState(data["baseline_state"]),
            post_repair_state=ValidationState(data["post_repair_state"]),
            outcome=RegressionOutcome(data["outcome"]),
        )

