"""RepoCraft Agent Compatibility Framework."""
from __future__ import annotations

from .compatibility_types import (
    AgentDefinition,
    AgentDetectionResult,
    AgentId,
    AgentSupportLevel,
    CompatibilityValidationResult,
)
from .agent_registry import AgentRegistry
from .agent_detector import AgentDetector
from .installation_adapter import InstallationAdapter
from .invocation_adapter import InvocationAdapter
from .capability_matrix import CapabilityMatrix
from .compatibility_validator import CompatibilityValidator
from .compatibility_report import CompatibilityReportGenerator

__all__ = [
    "AgentDefinition",
    "AgentDetectionResult",
    "AgentId",
    "AgentSupportLevel",
    "CompatibilityValidationResult",
    "AgentRegistry",
    "AgentDetector",
    "InstallationAdapter",
    "InvocationAdapter",
    "CapabilityMatrix",
    "CompatibilityValidator",
    "CompatibilityReportGenerator",
]

