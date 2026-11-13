"""Central registry of all RepoCraft artifacts, schemas, and sensitivity rules."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from .integration_types import ArtifactContract, ArtifactSensitivity, LifecyclePhase


_ARTIFACT_CONTRACTS: Dict[str, ArtifactContract] = {
    # Phase 0
    "INSTALL-MANIFEST.json": ArtifactContract(
        artifact_id="INSTALL-MANIFEST.json",
        filename="INSTALL-MANIFEST.json",
        producing_phase=LifecyclePhase.PHASE_0_INIT.value,
        schema_version="1.0.0",
        required_fields=["name", "version", "agent", "files"],
        optional_fields=["installed_to"],
        data_sensitivity=ArtifactSensitivity.PUBLIC,
        description="Installation record containing file inventory and SHA-256 hashes.",
    ),
    # Phase 1
    "inventory.json": ArtifactContract(
        artifact_id="inventory.json",
        filename="inventory.json",
        producing_phase=LifecyclePhase.PHASE_1_INTEL.value,
        schema_version="1.0.0",
        required_fields=["files_count"],
        optional_fields=["version", "repository", "technologies", "git_baseline", "schema_version", "generated_at", "target_root", "file_inventory_summary"],
        data_sensitivity=ArtifactSensitivity.INTERNAL,
        description="Comprehensive repository file inventory and categorization.",
    ),
    "recommendations.json": ArtifactContract(
        artifact_id="recommendations.json",
        filename="recommendations.json",
        producing_phase=LifecyclePhase.PHASE_1_INTEL.value,
        schema_version="1.0.0",
        required_fields=["schema_version", "recommendations"],
        optional_fields=["priority_order"],
        data_sensitivity=ArtifactSensitivity.PUBLIC,
        description="Phase 1 prioritized repository improvements.",
    ),
    # Phase 2
    "maintenance-analysis.json": ArtifactContract(
        artifact_id="maintenance-analysis.json",
        filename="maintenance-analysis.json",
        producing_phase=LifecyclePhase.PHASE_2_MAINTENANCE.value,
        schema_version="1.0.0",
        required_fields=["schema_version", "target", "timestamp"],
        optional_fields=["organization", "unused_files", "naming_conventions"],
        data_sensitivity=ArtifactSensitivity.INTERNAL,
        description="Codebase structure, import graph, and calibrated unused file analysis.",
    ),
    "maintenance-plan.json": ArtifactContract(
        artifact_id="maintenance-plan.json",
        filename="maintenance-plan.json",
        producing_phase=LifecyclePhase.PHASE_2_MAINTENANCE.value,
        schema_version="1.0.0",
        required_fields=["schema_version", "tasks", "generated_at"],
        optional_fields=["total_tasks", "risk_breakdown"],
        data_sensitivity=ArtifactSensitivity.PUBLIC,
        description="Prioritized maintenance action items with risk and approval classifications.",
    ),
    # Phase 3
    "security-findings.json": ArtifactContract(
        artifact_id="security-findings.json",
        filename="security-findings.json",
        producing_phase=LifecyclePhase.PHASE_3_SECURITY.value,
        schema_version="1.0.0",
        required_fields=["schema_version", "generated_at", "findings"],
        optional_fields=["total_findings", "severity_counts"],
        data_sensitivity=ArtifactSensitivity.SENSITIVE_REDACTED,
        description="Security pattern findings, discovered secret locations (redacted), and container hygiene.",
    ),
    "dependency-audit.json": ArtifactContract(
        artifact_id="dependency-audit.json",
        filename="dependency-audit.json",
        producing_phase=LifecyclePhase.PHASE_3_SECURITY.value,
        schema_version="1.0.0",
        required_fields=["schema_version", "generated_at", "manifests"],
        optional_fields=["unpinned_dependencies", "missing_lockfiles"],
        data_sensitivity=ArtifactSensitivity.PUBLIC,
        description="Dependency audit across package manifests and lockfiles.",
    ),
    "test-analysis.json": ArtifactContract(
        artifact_id="test-analysis.json",
        filename="test-analysis.json",
        producing_phase=LifecyclePhase.PHASE_3_SECURITY.value,
        schema_version="1.0.0",
        required_fields=["schema_version", "generated_at", "frameworks"],
        optional_fields=["test_files", "readiness_blockers"],
        data_sensitivity=ArtifactSensitivity.PUBLIC,
        description="Discovered test frameworks, test files, and runner readiness.",
    ),
    "test-execution-report.json": ArtifactContract(
        artifact_id="test-execution-report.json",
        filename="test-execution-report.json",
        producing_phase=LifecyclePhase.PHASE_3_SECURITY.value,
        schema_version="1.0.0",
        required_fields=["schema_version", "execution_status", "results"],
        optional_fields=["command", "duration_seconds", "output_redacted"],
        data_sensitivity=ArtifactSensitivity.INTERNAL,
        description="Controlled test execution results, pass/fail counts, and outputs.",
    ),
    "cicd-audit.json": ArtifactContract(
        artifact_id="cicd-audit.json",
        filename="cicd-audit.json",
        producing_phase=LifecyclePhase.PHASE_3_SECURITY.value,
        schema_version="1.0.0",
        required_fields=["schema_version", "workflows"],
        optional_fields=["triggers", "unpinned_actions", "permissions"],
        data_sensitivity=ArtifactSensitivity.PUBLIC,
        description="CI/CD pipeline and supply chain audit.",
    ),
    # Phase 4
    "repair-findings.json": ArtifactContract(
        artifact_id="repair-findings.json",
        filename="repair-findings.json",
        producing_phase=LifecyclePhase.PHASE_4_REPAIR.value,
        schema_version="1.0.0",
        required_fields=["schema_version", "findings", "generated_at"],
        optional_fields=["source_phases", "deduplicated_count"],
        data_sensitivity=ArtifactSensitivity.INTERNAL,
        description="Normalized, deduplicated findings ingested from Phases 1, 2, and 3.",
    ),
    "repair-plan.json": ArtifactContract(
        artifact_id="repair-plan.json",
        filename="repair-plan.json",
        producing_phase=LifecyclePhase.PHASE_4_REPAIR.value,
        schema_version="1.0.0",
        required_fields=["schema_version", "tasks", "generated_at"],
        optional_fields=["execution_order", "total_tasks"],
        data_sensitivity=ArtifactSensitivity.PUBLIC,
        description="Prioritized repair tasks with risk classifications and proposed patches.",
    ),
    "approval-manifest.json": ArtifactContract(
        artifact_id="approval-manifest.json",
        filename="approval-manifest.json",
        producing_phase=LifecyclePhase.PHASE_4_REPAIR.value,
        schema_version="1.0.0",
        required_fields=["schema_version", "tasks", "generated_at"],
        optional_fields=["approved_by", "signature"],
        data_sensitivity=ArtifactSensitivity.PUBLIC,
        description="Human-editable repair authorization manifest binding patch hashes.",
    ),
    "repair-execution.json": ArtifactContract(
        artifact_id="repair-execution.json",
        filename="repair-execution.json",
        producing_phase=LifecyclePhase.PHASE_4_REPAIR.value,
        schema_version="1.0.0",
        required_fields=["schema_version", "results", "applied_patches"],
        optional_fields=["modified_files", "execution_duration"],
        data_sensitivity=ArtifactSensitivity.INTERNAL,
        description="Execution log of applied patches and modified files.",
    ),
    "regression-comparison.json": ArtifactContract(
        artifact_id="regression-comparison.json",
        filename="regression-comparison.json",
        producing_phase=LifecyclePhase.PHASE_4_REPAIR.value,
        schema_version="1.0.0",
        required_fields=["schema_version", "comparisons"],
        optional_fields=["baseline_status", "post_repair_status"],
        data_sensitivity=ArtifactSensitivity.INTERNAL,
        description="Multi-level regression validation results.",
    ),
    "rollback-report.json": ArtifactContract(
        artifact_id="rollback-report.json",
        filename="rollback-report.json",
        producing_phase=LifecyclePhase.PHASE_4_REPAIR.value,
        schema_version="1.0.0",
        required_fields=["schema_version", "actions", "restored_files"],
        optional_fields=["blocked_rollbacks", "warnings"],
        data_sensitivity=ArtifactSensitivity.PUBLIC,
        description="Rollback records protecting user modifications.",
    ),
    # Phase 5
    "git-state.json": ArtifactContract(
        artifact_id="git-state.json",
        filename="git-state.json",
        producing_phase=LifecyclePhase.PHASE_5_GIT_REVIEW.value,
        schema_version="1.0.0",
        required_fields=["schema_version", "generated_at", "is_git_repository"],
        optional_fields=["current_branch", "head_commit", "is_clean", "remotes"],
        data_sensitivity=ArtifactSensitivity.INTERNAL,
        description="Git environment snapshot with credential-redacted remotes and state.",
    ),
    "git-change-review.json": ArtifactContract(
        artifact_id="git-change-review.json",
        filename="git-change-review.json",
        producing_phase=LifecyclePhase.PHASE_5_GIT_REVIEW.value,
        schema_version="1.0.0",
        required_fields=["schema_version", "changes", "overall_risk"],
        optional_fields=["staged_count", "unstaged_count", "untracked_count"],
        data_sensitivity=ArtifactSensitivity.INTERNAL,
        description="Structured file changes, 5-tier risk classifications, and diff stats.",
    ),
    "staging-plan.json": ArtifactContract(
        artifact_id="staging-plan.json",
        filename="staging-plan.json",
        producing_phase=LifecyclePhase.PHASE_5_GIT_REVIEW.value,
        schema_version="1.0.0",
        required_fields=["schema_version", "staged_files", "patch_hash"],
        optional_fields=["excluded_files", "reason"],
        data_sensitivity=ArtifactSensitivity.PUBLIC,
        description="Deterministic staging plan with exact file paths and patch hashes.",
    ),
    "staging-approval.json": ArtifactContract(
        artifact_id="staging-approval.json",
        filename="staging-approval.json",
        producing_phase=LifecyclePhase.PHASE_5_GIT_REVIEW.value,
        schema_version="1.0.0",
        required_fields=["schema_version", "status", "authorized_by"],
        optional_fields=["files_approved", "expected_patch_hash"],
        data_sensitivity=ArtifactSensitivity.PUBLIC,
        description="Staging authorization manifest.",
    ),
    "staging-result.json": ArtifactContract(
        artifact_id="staging-result.json",
        filename="staging-result.json",
        producing_phase=LifecyclePhase.PHASE_5_GIT_REVIEW.value,
        schema_version="1.0.0",
        required_fields=["schema_version", "status", "staged_files"],
        optional_fields=["post_stage_diff_hash"],
        data_sensitivity=ArtifactSensitivity.INTERNAL,
        description="Post-stage verification record.",
    ),
    "commit-approval.json": ArtifactContract(
        artifact_id="commit-approval.json",
        filename="commit-approval.json",
        producing_phase=LifecyclePhase.PHASE_5_GIT_REVIEW.value,
        schema_version="1.0.0",
        required_fields=["schema_version", "status", "commit_message"],
        optional_fields=["staged_patch_hash", "expected_parent_commit"],
        data_sensitivity=ArtifactSensitivity.PUBLIC,
        description="Commit authorization manifest binding commit message and staged diff hash.",
    ),
    "commit-receipt.json": ArtifactContract(
        artifact_id="commit-receipt.json",
        filename="commit-receipt.json",
        producing_phase=LifecyclePhase.PHASE_5_GIT_REVIEW.value,
        schema_version="1.0.0",
        required_fields=["schema_version", "status", "commit_hash"],
        optional_fields=["parent_commit", "branch"],
        data_sensitivity=ArtifactSensitivity.PUBLIC,
        description="Cryptographic commit verification receipt.",
    ),
    "remote-status.json": ArtifactContract(
        artifact_id="remote-status.json",
        filename="remote-status.json",
        producing_phase=LifecyclePhase.PHASE_5_GIT_REVIEW.value,
        schema_version="1.0.0",
        required_fields=["schema_version", "remotes"],
        optional_fields=["tracking_branch", "ahead_count", "behind_count"],
        data_sensitivity=ArtifactSensitivity.INTERNAL,
        description="Offline remote inspection snapshot.",
    ),
    "push-plan.json": ArtifactContract(
        artifact_id="push-plan.json",
        filename="push-plan.json",
        producing_phase=LifecyclePhase.PHASE_5_GIT_REVIEW.value,
        schema_version="1.0.0",
        required_fields=["schema_version", "remote_name", "target_branch"],
        optional_fields=["push_mode", "commit_to_push"],
        data_sensitivity=ArtifactSensitivity.PUBLIC,
        description="Remote publishing plan.",
    ),
    "push-approval.json": ArtifactContract(
        artifact_id="push-approval.json",
        filename="push-approval.json",
        producing_phase=LifecyclePhase.PHASE_5_GIT_REVIEW.value,
        schema_version="1.0.0",
        required_fields=["schema_version", "status", "target_branch"],
        optional_fields=["remote_name", "authorized_by"],
        data_sensitivity=ArtifactSensitivity.PUBLIC,
        description="Push authorization manifest with strict force-push rejection.",
    ),
    "push-result.json": ArtifactContract(
        artifact_id="push-result.json",
        filename="push-result.json",
        producing_phase=LifecyclePhase.PHASE_5_GIT_REVIEW.value,
        schema_version="1.0.0",
        required_fields=["schema_version", "status"],
        optional_fields=["remote_ref", "commit_pushed"],
        data_sensitivity=ArtifactSensitivity.PUBLIC,
        description="Remote publishing outcome receipt.",
    ),
    # Phase 6
    "agent-compatibility.json": ArtifactContract(
        artifact_id="agent-compatibility.json",
        filename="agent-compatibility.json",
        producing_phase=LifecyclePhase.PHASE_6_RELEASE.value,
        schema_version="1.0.0",
        required_fields=["schema_version", "repocraft_version", "capability_matrix"],
        optional_fields=["detected_agent", "validation_results"],
        data_sensitivity=ArtifactSensitivity.PUBLIC,
        description="Agent compatibility matrix and validation evidence.",
    ),
    "phase-registry.json": ArtifactContract(
        artifact_id="phase-registry.json",
        filename="phase-registry.json",
        producing_phase=LifecyclePhase.PHASE_6_RELEASE.value,
        schema_version="1.0.0",
        required_fields=["schema_version", "phases"],
        optional_fields=[],
        data_sensitivity=ArtifactSensitivity.PUBLIC,
        description="Registry of lifecycle phase contracts and entry points.",
    ),
    "artifact-registry.json": ArtifactContract(
        artifact_id="artifact-registry.json",
        filename="artifact-registry.json",
        producing_phase=LifecyclePhase.PHASE_6_RELEASE.value,
        schema_version="1.0.0",
        required_fields=["schema_version", "artifacts"],
        optional_fields=[],
        data_sensitivity=ArtifactSensitivity.PUBLIC,
        description="Registry of artifact contracts and schema specifications.",
    ),
    "lifecycle-integration-report.json": ArtifactContract(
        artifact_id="lifecycle-integration-report.json",
        filename="lifecycle-integration-report.json",
        producing_phase=LifecyclePhase.PHASE_6_RELEASE.value,
        schema_version="1.0.0",
        required_fields=["schema_version", "is_valid", "executed_phases"],
        optional_fields=["handoff_results", "artifact_evaluations"],
        data_sensitivity=ArtifactSensitivity.PUBLIC,
        description="Comprehensive cross-phase lifecycle integration validation report.",
    ),
    "release-manifest.json": ArtifactContract(
        artifact_id="release-manifest.json",
        filename="release-manifest.json",
        producing_phase=LifecyclePhase.PHASE_6_RELEASE.value,
        schema_version="1.0.0",
        required_fields=["schema_version", "package_name", "files"],
        optional_fields=["version", "sha256", "total_files"],
        data_sensitivity=ArtifactSensitivity.PUBLIC,
        description="Release package inventory and cryptographic checksums.",
    ),
    "package-integrity.json": ArtifactContract(
        artifact_id="package-integrity.json",
        filename="package-integrity.json",
        producing_phase=LifecyclePhase.PHASE_6_RELEASE.value,
        schema_version="1.0.0",
        required_fields=["schema_version", "is_valid", "checksums"],
        optional_fields=["archive_path", "errors", "warnings"],
        data_sensitivity=ArtifactSensitivity.PUBLIC,
        description="Archive verification, traversal check, and integrity results.",
    ),
    "release-readiness.json": ArtifactContract(
        artifact_id="release-readiness.json",
        filename="release-readiness.json",
        producing_phase=LifecyclePhase.PHASE_6_RELEASE.value,
        schema_version="1.0.0",
        required_fields=["schema_version", "release_status", "gates"],
        optional_fields=["unresolved_blockers", "recommendations"],
        data_sensitivity=ArtifactSensitivity.PUBLIC,
        description="Production readiness assessment against all mandatory completion gates.",
    ),
    "phase6-security-audit.json": ArtifactContract(
        artifact_id="phase6-security-audit.json",
        filename="phase6-security-audit.json",
        producing_phase=LifecyclePhase.PHASE_6_RELEASE.value,
        schema_version="1.0.0",
        required_fields=["schema_version", "audit_status", "findings"],
        optional_fields=["dependency_count", "subprocess_safety"],
        data_sensitivity=ArtifactSensitivity.INTERNAL,
        description="Security and supply-chain review of RepoCraft itself.",
    ),
}


class ArtifactRegistry:
    """Query and validation interface for RepoCraft artifacts."""

    @classmethod
    def get(cls, filename: str) -> Optional[ArtifactContract]:
        return _ARTIFACT_CONTRACTS.get(filename)

    @classmethod
    def list_all(cls) -> List[ArtifactContract]:
        return list(_ARTIFACT_CONTRACTS.values())

    @classmethod
    def list_by_phase(cls, phase_id: str) -> List[ArtifactContract]:
        return [
            art for art in _ARTIFACT_CONTRACTS.values()
            if art.producing_phase == phase_id
        ]

    @classmethod
    def is_known(cls, filename: str) -> bool:
        return filename in _ARTIFACT_CONTRACTS

    @classmethod
    def to_dict(cls) -> Dict[str, Any]:
        return {
            "schema_version": "1.0.0",
            "total_artifacts": len(_ARTIFACT_CONTRACTS),
            "artifacts": {k: v.to_dict() for k, v in _ARTIFACT_CONTRACTS.items()},
        }
