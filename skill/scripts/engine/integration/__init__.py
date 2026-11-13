"""RepoCraft Full Lifecycle Integration Engine."""
from __future__ import annotations

from .integration_types import (
    ArtifactContract,
    ArtifactSensitivity,
    HandoffValidationResult,
    LifecyclePhase,
    LifecycleValidationResult,
    PhaseContract,
    ValidationSeverity,
)
from .phase_registry import PhaseRegistry
from .artifact_registry import ArtifactRegistry
from .schema_validator import SchemaValidator
from .dependency_graph import DependencyGraph
from .integration_validator import IntegrationValidator
from .lifecycle_orchestrator import LifecycleOrchestrator
from .integration_report import IntegrationReportGenerator

__all__ = [
    "ArtifactContract",
    "ArtifactSensitivity",
    "HandoffValidationResult",
    "LifecyclePhase",
    "LifecycleValidationResult",
    "PhaseContract",
    "ValidationSeverity",
    "PhaseRegistry",
    "ArtifactRegistry",
    "SchemaValidator",
    "DependencyGraph",
    "IntegrationValidator",
    "LifecycleOrchestrator",
    "IntegrationReportGenerator",
]

