"""Dependency graph and topological verification of phase artifact handoffs."""
from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

from .phase_registry import PhaseRegistry
from .integration_types import LifecyclePhase


class DependencyGraph:
    """Evaluates prerequisites and DAG relationships between lifecycle phases."""

    # Explicit prerequisite dependencies between phases
    PHASE_PREREQUISITES: Dict[str, List[str]] = {
        LifecyclePhase.PHASE_0_INIT.value: [],
        LifecyclePhase.PHASE_1_INTEL.value: [],
        LifecyclePhase.PHASE_2_MAINTENANCE.value: [LifecyclePhase.PHASE_1_INTEL.value],
        LifecyclePhase.PHASE_3_SECURITY.value: [LifecyclePhase.PHASE_1_INTEL.value],
        LifecyclePhase.PHASE_4_REPAIR.value: [
            LifecyclePhase.PHASE_1_INTEL.value,
            LifecyclePhase.PHASE_2_MAINTENANCE.value,
            LifecyclePhase.PHASE_3_SECURITY.value,
        ],
        LifecyclePhase.PHASE_5_GIT_REVIEW.value: [],  # Can inspect any git state
        LifecyclePhase.PHASE_5_PUBLISH.value: [LifecyclePhase.PHASE_5_GIT_REVIEW.value],
        LifecyclePhase.PHASE_6_RELEASE.value: [
            LifecyclePhase.PHASE_1_INTEL.value,
        ],
    }

    @classmethod
    def get_prerequisites(cls, phase_id: str) -> List[str]:
        return cls.PHASE_PREREQUISITES.get(phase_id, [])

    @classmethod
    def check_prerequisites_satisfied(
        cls, phase_id: str, reports_dir: Path
    ) -> Tuple[bool, List[str]]:
        """Verify that all input artifacts required by phase_id exist in reports_dir.
        
        Returns (is_satisfied, missing_artifacts).
        """
        contract = PhaseRegistry.get(phase_id)
        if not contract:
            return False, [f"Unknown phase {phase_id}"]

        missing = []
        for req_artifact in contract.input_artifacts:
            path = reports_dir / req_artifact
            if not path.is_file():
                missing.append(req_artifact)

        return len(missing) == 0, missing

    @classmethod
    def get_execution_order(cls) -> List[str]:
        """Return the canonical execution order of lifecycle phases."""
        return [
            LifecyclePhase.PHASE_0_INIT.value,
            LifecyclePhase.PHASE_1_INTEL.value,
            LifecyclePhase.PHASE_2_MAINTENANCE.value,
            LifecyclePhase.PHASE_3_SECURITY.value,
            LifecyclePhase.PHASE_4_REPAIR.value,
            LifecyclePhase.PHASE_5_GIT_REVIEW.value,
            LifecyclePhase.PHASE_5_PUBLISH.value,
            LifecyclePhase.PHASE_6_RELEASE.value,
        ]

