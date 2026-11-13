"""Central registry of RepoCraft lifecycle phases, contracts, and entry points."""
from __future__ import annotations

from typing import Dict, List, Optional

from .integration_types import LifecyclePhase, PhaseContract


_PHASE_CONTRACTS: Dict[str, PhaseContract] = {
    LifecyclePhase.PHASE_0_INIT.value: PhaseContract(
        phase_id=LifecyclePhase.PHASE_0_INIT.value,
        display_name="Phase 0: Initialization & Installation",
        cli_entry_point="install.py",
        input_artifacts=[],
        output_artifacts=["INSTALL-MANIFEST.json"],
        schema_version="1.0.0",
        required_dependencies=["python>=3.9"],
        optional_dependencies=[],
        safety_policy="safety-and-git-baseline.md",
        execution_permissions="safe_skill_copy",
        supported_modes=["default", "force"],
    ),
    LifecyclePhase.PHASE_1_INTEL.value: PhaseContract(
        phase_id=LifecyclePhase.PHASE_1_INTEL.value,
        display_name="Phase 1: Repository Intelligence",
        cli_entry_point="skill/scripts/repocraft_intel.py",
        input_artifacts=[],
        output_artifacts=[
            "inventory.json",
            "repository-overview.md",
            "repository-audit.md",
            "recommendations.json",
        ],
        schema_version="1.0.0",
        required_dependencies=["python>=3.9"],
        optional_dependencies=["git"],
        safety_policy="repository-intelligence.md",
        execution_permissions="strictly_read_only",
        supported_modes=["default", "json_only"],
    ),
    LifecyclePhase.PHASE_2_MAINTENANCE.value: PhaseContract(
        phase_id=LifecyclePhase.PHASE_2_MAINTENANCE.value,
        display_name="Phase 2: Maintenance, Documentation & Presentation",
        cli_entry_point="skill/scripts/repocraft_maintenance.py",
        input_artifacts=["inventory.json", "repository-overview.md"],
        output_artifacts=[
            "maintenance-analysis.json",
            "README-improved.md",
            "documentation-audit.md",
            "github-presentation-audit.md",
            "maintenance-plan.json",
            "phase2-report.md",
        ],
        schema_version="1.0.0",
        required_dependencies=["python>=3.9"],
        optional_dependencies=[],
        safety_policy="maintenance-policy.md",
        execution_permissions="read_only_in_audit_mode",
        supported_modes=["audit", "draft", "apply"],
    ),
    LifecyclePhase.PHASE_3_SECURITY.value: PhaseContract(
        phase_id=LifecyclePhase.PHASE_3_SECURITY.value,
        display_name="Phase 3: Security, Testing & CI/CD Validation",
        cli_entry_point="skill/scripts/repocraft_security.py",
        input_artifacts=["inventory.json"],
        output_artifacts=[
            "security-findings.json",
            "dependency-audit.json",
            "test-analysis.json",
            "test-execution-report.json",
            "cicd-audit.json",
            "security-quality-report.md",
            "phase3-report.md",
        ],
        schema_version="1.0.0",
        required_dependencies=["python>=3.9"],
        optional_dependencies=["pytest", "npm", "mvn", "cargo"],
        safety_policy="security-testing-policy.md",
        execution_permissions="controlled_test_execution_requires_flag",
        supported_modes=["audit", "execute_tests"],
    ),
    LifecyclePhase.PHASE_4_REPAIR.value: PhaseContract(
        phase_id=LifecyclePhase.PHASE_4_REPAIR.value,
        display_name="Phase 4: Bounded Repair & Regression Validation",
        cli_entry_point="skill/scripts/repocraft_repair.py",
        input_artifacts=[
            "inventory.json",
            "maintenance-plan.json",
            "security-findings.json",
        ],
        output_artifacts=[
            "repair-findings.json",
            "repair-plan.json",
            "approval-manifest.json",
            "repair-execution.json",
            "regression-comparison.json",
            "rollback-report.json",
            "phase4-report.md",
        ],
        schema_version="1.0.0",
        required_dependencies=["python>=3.9", "git"],
        optional_dependencies=[],
        safety_policy="repair-and-regression-policy.md",
        execution_permissions="explicit_hash_authorization_required",
        supported_modes=["plan", "draft", "apply-approved"],
    ),
    LifecyclePhase.PHASE_5_GIT_REVIEW.value: PhaseContract(
        phase_id=LifecyclePhase.PHASE_5_GIT_REVIEW.value,
        display_name="Phase 5: Git Review, Conditional Commit & PR Draft",
        cli_entry_point="skill/scripts/repocraft_git.py",
        input_artifacts=[],
        output_artifacts=[
            "git-state.json",
            "git-change-review.md",
            "git-change-review.json",
            "staging-plan.json",
            "staging-approval.json",
            "staging-result.json",
            "commit-proposal.md",
            "commit-approval.json",
            "commit-receipt.json",
            "remote-status.json",
            "push-plan.json",
            "push-approval.json",
            "push-result.json",
            "pull-request-draft.md",
            "git-workflow-report.md",
        ],
        schema_version="1.0.0",
        required_dependencies=["python>=3.9", "git>=2.20"],
        optional_dependencies=[],
        safety_policy="git-workflow-policy.md",
        execution_permissions="independent_approval_per_git_action",
        supported_modes=[
            "inspect",
            "review",
            "plan-stage",
            "stage-approved",
            "draft-commit",
            "commit-approved",
            "inspect-remote",
            "plan-push",
            "push-approved",
            "draft-pr",
        ],
    ),
    LifecyclePhase.PHASE_6_RELEASE.value: PhaseContract(
        phase_id=LifecyclePhase.PHASE_6_RELEASE.value,
        display_name="Phase 6: Agent Compatibility, Release Packaging & Production Readiness",
        cli_entry_point="skill/scripts/repocraft_status.py",
        input_artifacts=[
            "inventory.json",
            "git-state.json",
            "git-workflow-report.md",
        ],
        output_artifacts=[
            "agent-compatibility.json",
            "phase-registry.json",
            "artifact-registry.json",
            "lifecycle-integration-report.json",
            "release-manifest.json",
            "package-integrity.json",
            "release-readiness.json",
            "phase6-security-audit.json",
        ],
        schema_version="1.0.0",
        required_dependencies=["python>=3.9"],
        optional_dependencies=[],
        safety_policy="release-and-portability-policy.md",
        execution_permissions="strictly_read_only_diagnostics",
        supported_modes=["status", "verify-installation", "verify-package", "json"],
    ),
}


class PhaseRegistry:
    """Query and validation interface for RepoCraft lifecycle phases."""

    @classmethod
    def get(cls, phase_id: str) -> Optional[PhaseContract]:
        return _PHASE_CONTRACTS.get(phase_id.lower().strip())

    @classmethod
    def list_all(cls) -> List[PhaseContract]:
        return list(_PHASE_CONTRACTS.values())

    @classmethod
    def get_producing_phase_for_artifact(cls, filename: str) -> Optional[PhaseContract]:
        for phase in _PHASE_CONTRACTS.values():
            if filename in phase.output_artifacts:
                return phase
        return None

    @classmethod
    def to_dict(cls) -> Dict[str, Any]:
        return {
            "schema_version": "1.0.0",
            "phases": {p_id: p.to_dict() for p_id, p in _PHASE_CONTRACTS.items()},
        }

