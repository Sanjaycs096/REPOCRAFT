"""Type definitions and contracts for Agent Compatibility Framework."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class AgentSupportLevel(str, Enum):
    """Calibrated support level for coding agents."""
    SUPPORTED = "SUPPORTED"
    PARTIALLY_SUPPORTED = "PARTIALLY_SUPPORTED"
    INSTALLATION_ONLY = "INSTALLATION_ONLY"
    MANUAL_CONFIGURATION_REQUIRED = "MANUAL_CONFIGURATION_REQUIRED"
    NOT_SUPPORTED = "NOT_SUPPORTED"
    NOT_TESTED = "NOT_TESTED"


class AgentId(str, Enum):
    """Known agent identifiers."""
    ANTIGRAVITY = "antigravity"
    CLAUDE_CODE = "claude-code"
    CURSOR = "cursor"
    GEMINI_CLI = "gemini-cli"
    GENERIC = "project"


@dataclass(frozen=True)
class AgentDefinition:
    """Specification of an agent's integration contract."""
    agent_id: str
    display_name: str
    support_level: AgentSupportLevel
    skill_dir: str
    installation_method: str
    expected_format: str
    invocation_instructions: str
    required_metadata: List[str] = field(default_factory=list)
    supported_capabilities: List[str] = field(default_factory=list)
    known_limitations: List[str] = field(default_factory=list)
    validation_status: str = "UNVERIFIED"
    compatibility_evidence: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "display_name": self.display_name,
            "support_level": self.support_level.value,
            "skill_dir": self.skill_dir,
            "installation_method": self.installation_method,
            "expected_format": self.expected_format,
            "invocation_instructions": self.invocation_instructions,
            "required_metadata": list(self.required_metadata),
            "supported_capabilities": list(self.supported_capabilities),
            "known_limitations": list(self.known_limitations),
            "validation_status": self.validation_status,
            "compatibility_evidence": list(self.compatibility_evidence),
        }


@dataclass
class AgentDetectionResult:
    """Result of attempting to detect agent environments in a repository."""
    detected_agent: Optional[str]
    confidence: float
    indicator_paths: List[str] = field(default_factory=list)
    environment_variables: List[str] = field(default_factory=list)
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "detected_agent": self.detected_agent,
            "confidence": self.confidence,
            "indicator_paths": list(self.indicator_paths),
            "environment_variables": list(self.environment_variables),
            "notes": self.notes,
        }


@dataclass
class CompatibilityValidationResult:
    """Result of validating an installed skill against an agent's contract."""
    agent_id: str
    support_level: AgentSupportLevel
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    evidence: List[str] = field(default_factory=list)
    checked_paths: List[str] = field(default_factory=list)
    capability_scores: Dict[str, bool] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "support_level": self.support_level.value,
            "is_valid": self.is_valid,
            "errors": list(self.errors),
            "warnings": list(self.warnings),
            "evidence": list(self.evidence),
            "checked_paths": list(self.checked_paths),
            "capability_scores": dict(self.capability_scores),
        }

