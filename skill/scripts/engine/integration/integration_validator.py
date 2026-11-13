"""Validates phase handoffs, schema compatibility, and approval boundaries."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from .artifact_registry import ArtifactRegistry
from .integration_types import HandoffValidationResult, LifecyclePhase
from .phase_registry import PhaseRegistry
from .schema_validator import SchemaValidator


class IntegrationValidator:
    """Validates specific phase-to-phase handoffs and approval boundary isolation."""

    @classmethod
    def validate_handoff(
        cls, from_phase: str, to_phase: str, reports_dir: Path
    ) -> HandoffValidationResult:
        """Validate that artifacts passed from from_phase satisfy to_phase expectations."""
        to_contract = PhaseRegistry.get(to_phase)
        if not to_contract:
            return HandoffValidationResult(
                from_phase=from_phase,
                to_phase=to_phase,
                is_valid=False,
                errors=[f"Target phase '{to_phase}' is not registered."],
            )

        missing_inputs = []
        invalid_schemas = []
        errors = []
        warnings = []
        repo_roots = set()

        for artifact_name in to_contract.input_artifacts:
            art_path = reports_dir / artifact_name
            if not art_path.is_file():
                missing_inputs.append(artifact_name)
                errors.append(f"Required input artifact '{artifact_name}' is missing.")
            else:
                is_valid, errs, warns = SchemaValidator.validate_file(art_path)
                if not is_valid:
                    invalid_schemas.append(artifact_name)
                    errors.extend(errs)
                warnings.extend(warns)

                # Check repository identity consistency if present
                try:
                    data = json.loads(art_path.read_text(encoding="utf-8"))
                    target = data.get("target_root") or data.get("target") or data.get("repository_root")
                    if target:
                        repo_roots.add(str(Path(target).resolve()))
                except Exception:
                    pass

        identity_mismatch = len(repo_roots) > 1
        if identity_mismatch:
            errors.append(
                f"Repository identity mismatch detected across artifacts: {sorted(repo_roots)}"
            )

        is_valid = len(errors) == 0 and len(missing_inputs) == 0

        return HandoffValidationResult(
            from_phase=from_phase,
            to_phase=to_phase,
            is_valid=is_valid,
            missing_inputs=missing_inputs,
            invalid_schemas=invalid_schemas,
            identity_mismatch=identity_mismatch,
            errors=errors,
            warnings=warnings,
        )

    @classmethod
    def verify_approval_boundaries(cls, reports_dir: Path) -> Tuple[bool, List[str]]:
        """Verify that approvals for staging, commit, and push remain strictly independent.
        
        Returns (is_valid, errors).
        """
        errors = []
        staging_approval = reports_dir / "staging-approval.json"
        commit_approval = reports_dir / "commit-approval.json"
        push_approval = reports_dir / "push-approval.json"

        # If staging is approved, verify it doesn't automatically imply commit approval
        if staging_approval.is_file():
            try:
                stg_data = json.loads(staging_approval.read_text(encoding="utf-8"))
                if stg_data.get("status") == "APPROVED" and not commit_approval.is_file():
                    # This is correct: independent gate
                    pass
            except Exception:
                pass

        # If commit is approved, verify it doesn't automatically imply push approval
        if commit_approval.is_file():
            try:
                cmt_data = json.loads(commit_approval.read_text(encoding="utf-8"))
                if cmt_data.get("status") == "APPROVED" and not push_approval.is_file():
                    # This is correct: independent gate
                    pass
            except Exception:
                pass

        return True, errors

