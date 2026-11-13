"""Read-only master orchestrator for lifecycle integration verification."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional

from .artifact_registry import ArtifactRegistry
from .dependency_graph import DependencyGraph
from .integration_types import LifecyclePhase, LifecycleValidationResult
from .integration_validator import IntegrationValidator
from .phase_registry import PhaseRegistry
from .schema_validator import SchemaValidator


class LifecycleOrchestrator:
    """Evaluates full lifecycle integration across phases in a target repository."""

    @classmethod
    def evaluate_lifecycle(
        cls, target_root: Path, reports_dir: Path
    ) -> LifecycleValidationResult:
        """Inspect target_root and reports_dir to validate lifecycle integration integrity."""
        target_resolved = str(target_root.resolve())
        reports_resolved = str(reports_dir.resolve())

        executed_phases: List[str] = []
        missing_phases: List[str] = []
        errors: List[str] = []
        warnings: List[str] = []
        artifact_evals: Dict[str, bool] = {}

        # 1. Discover executed phases based on generated artifacts
        for phase in PhaseRegistry.list_all():
            phase_executed = False
            for art in phase.output_artifacts:
                art_path = reports_dir / art
                if art_path.is_file():
                    phase_executed = True
                    is_valid, errs, warns = SchemaValidator.validate_file(art_path)
                    artifact_evals[art] = is_valid
                    if not is_valid:
                        errors.extend(errs)
                    warnings.extend(warns)
                else:
                    artifact_evals[art] = False

            if phase_executed:
                executed_phases.append(phase.phase_id)
            else:
                missing_phases.append(phase.phase_id)

        # 2. Check handoffs between executed sequential phases
        handoff_results = []
        phases_in_order = DependencyGraph.get_execution_order()
        for i in range(len(phases_in_order) - 1):
            p1 = phases_in_order[i]
            p2 = phases_in_order[i + 1]
            if p2 in executed_phases:
                handoff = IntegrationValidator.validate_handoff(p1, p2, reports_dir)
                handoff_results.append(handoff)
                if not handoff.is_valid:
                    errors.extend(handoff.errors)
                warnings.extend(handoff.warnings)

        # 3. Verify approval boundaries remain independent
        boundaries_ok, boundary_errors = IntegrationValidator.verify_approval_boundaries(reports_dir)
        if not boundaries_ok:
            errors.extend(boundary_errors)

        is_valid = len(errors) == 0

        return LifecycleValidationResult(
            is_valid=is_valid,
            target_repo=target_resolved,
            reports_dir=reports_resolved,
            executed_phases=executed_phases,
            missing_phases=missing_phases,
            handoff_results=handoff_results,
            artifact_evaluations=artifact_evals,
            approval_boundaries_preserved=boundaries_ok,
            errors=errors,
            warnings=warnings,
        )

