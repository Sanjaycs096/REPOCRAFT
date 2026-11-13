"""Data types and contracts for RepoCraft Lifecycle Integration Engine."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class LifecyclePhase(str, Enum):
    """Supported RepoCraft lifecycle phases."""
    PHASE_0_INIT = "phase_0_init"
    PHASE_1_INTEL = "phase_1_intel"
    PHASE_2_MAINTENANCE = "phase_2_maintenance"
    PHASE_3_SECURITY = "phase_3_security"
    PHASE_4_REPAIR = "phase_4_repair"
    PHASE_5_GIT_REVIEW = "phase_5_git_review"
    PHASE_5_PUBLISH = "phase_5_publish"
    PHASE_6_RELEASE = "phase_6_release"


class ArtifactSensitivity(str, Enum):
    """Sensitivity classification of generated artifacts."""
    PUBLIC = "PUBLIC"
    INTERNAL = "INTERNAL"
    SENSITIVE_REDACTED = "SENSITIVE_REDACTED"


class ValidationSeverity(str, Enum):
    """Severity of integration findings."""
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


@dataclass(frozen=True)
class PhaseContract:
    """Contract definition for a RepoCraft lifecycle phase."""
    phase_id: str
    display_name: str
    cli_entry_point: str
    input_artifacts: List[str]
    output_artifacts: List[str]
    schema_version: str
    required_dependencies: List[str]
    optional_dependencies: List[str]
    safety_policy: str
    execution_permissions: str
    supported_modes: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "phase_id": self.phase_id,
            "display_name": self.display_name,
            "cli_entry_point": self.cli_entry_point,
            "input_artifacts": list(self.input_artifacts),
            "output_artifacts": list(self.output_artifacts),
            "schema_version": self.schema_version,
            "required_dependencies": list(self.required_dependencies),
            "optional_dependencies": list(self.optional_dependencies),
            "safety_policy": self.safety_policy,
            "execution_permissions": self.execution_permissions,
            "supported_modes": list(self.supported_modes),
        }


@dataclass(frozen=True)
class ArtifactContract:
    """Contract definition for a RepoCraft artifact."""
    artifact_id: str
    filename: str
    producing_phase: str
    schema_version: str
    required_fields: List[str]
    optional_fields: List[str]
    data_sensitivity: ArtifactSensitivity
    description: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "artifact_id": self.artifact_id,
            "filename": self.filename,
            "producing_phase": self.producing_phase,
            "schema_version": self.schema_version,
            "required_fields": list(self.required_fields),
            "optional_fields": list(self.optional_fields),
            "data_sensitivity": self.data_sensitivity.value,
            "description": self.description,
        }


@dataclass
class HandoffValidationResult:
    """Validation result of a transition from one phase to the next."""
    from_phase: str
    to_phase: str
    is_valid: bool
    missing_inputs: List[str] = field(default_factory=list)
    invalid_schemas: List[str] = field(default_factory=list)
    identity_mismatch: bool = False
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "from_phase": self.from_phase,
            "to_phase": self.to_phase,
            "is_valid": self.is_valid,
            "missing_inputs": list(self.missing_inputs),
            "invalid_schemas": list(self.invalid_schemas),
            "identity_mismatch": self.identity_mismatch,
            "errors": list(self.errors),
            "warnings": list(self.warnings),
        }


@dataclass
class LifecycleValidationResult:
    """Overall result of validating full lifecycle integration."""
    is_valid: bool
    target_repo: str
    reports_dir: str
    executed_phases: List[str] = field(default_factory=list)
    missing_phases: List[str] = field(default_factory=list)
    handoff_results: List[HandoffValidationResult] = field(default_factory=list)
    artifact_evaluations: Dict[str, bool] = field(default_factory=dict)
    approval_boundaries_preserved: bool = True
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_valid": self.is_valid,
            "target_repo": self.target_repo,
            "reports_dir": self.reports_dir,
            "executed_phases": list(self.executed_phases),
            "missing_phases": list(self.missing_phases),
            "handoff_results": [h.to_dict() for h in self.handoff_results],
            "artifact_evaluations": dict(self.artifact_evaluations),
            "approval_boundaries_preserved": self.approval_boundaries_preserved,
            "errors": list(self.errors),
            "warnings": list(self.warnings),
        }

