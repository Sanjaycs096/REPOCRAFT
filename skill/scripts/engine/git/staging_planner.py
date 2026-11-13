"""Module 3.7 — Staging Planner for RepoCraft Phase 5.

Generates deterministic staging plans without blanket or wildcard operations.
Calculates expected original and patch hashes, rejects path traversal, and filters critical changes.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Set

from .change_review import ChangeReviewGenerator
from .git_environment import GitEnvironment
from .git_types import (
    ChangeRisk,
    OperationStatus,
    StagingApproval,
    StagingApprovalEntry,
    StagingPlan,
    StagingPlanEntry,
    sha256_of_text,
)


def compute_file_hash(path: Path) -> Optional[str]:
    """Compute SHA-256 hash of a file on disk."""
    if not path.is_file():
        return None
    try:
        content = path.read_bytes()
        return hashlib.sha256(content).hexdigest()
    except Exception:
        return None


class StagingPlanner:
    """Constructs explicit, verifiable staging plans."""

    def __init__(self, target_dir: str, env: Optional[GitEnvironment] = None):
        self.target_dir = Path(target_dir).resolve()
        self.env = env or GitEnvironment(str(self.target_dir))
        self.review_generator = ChangeReviewGenerator(str(self.target_dir), self.env)

    def plan_staging(self, selected_files: Optional[List[str]] = None) -> StagingPlan:
        """Create a deterministic staging plan."""
        state = self.env.inspect_state()
        review = self.review_generator.generate_review()

        now_str = datetime.now(timezone.utc).isoformat()
        plan_id = f"PLAN-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"

        planned_files: List[str] = []
        excluded_files: List[str] = []
        entries: List[StagingPlanEntry] = []

        selected_set: Optional[Set[str]] = set(selected_files) if selected_files is not None else None

        for cf in review.files:
            file_path = cf.file_path
            # Check for path traversal or outside repo
            full_path = (self.target_dir / file_path).resolve()
            try:
                full_path.relative_to(self.target_dir)
            except ValueError:
                # Path is outside repo
                excluded_files.append(file_path)
                entries.append(
                    StagingPlanEntry(
                        file_path=file_path,
                        change_type=cf.change_type.value,
                        risk=cf.risk,
                        excluded_reason="PATH_OUTSIDE_REPO: Path escapes repository root.",
                    )
                )
                continue

            # Path traversal in string
            if ".." in file_path.replace("\\", "/").split("/"):
                excluded_files.append(file_path)
                entries.append(
                    StagingPlanEntry(
                        file_path=file_path,
                        change_type=cf.change_type.value,
                        risk=cf.risk,
                        excluded_reason="PATH_TRAVERSAL_DETECTED",
                    )
                )
                continue

            # Critical changes must never be automatically planned for staging
            if cf.risk == ChangeRisk.CRITICAL:
                excluded_files.append(file_path)
                entries.append(
                    StagingPlanEntry(
                        file_path=file_path,
                        change_type=cf.change_type.value,
                        risk=cf.risk,
                        excluded_reason="CRITICAL_RISK: Critical changes cannot be staged autonomously.",
                    )
                )
                continue

            # If specific files were selected, filter by selection
            if selected_set is not None and file_path not in selected_set:
                excluded_files.append(file_path)
                entries.append(
                    StagingPlanEntry(
                        file_path=file_path,
                        change_type=cf.change_type.value,
                        risk=cf.risk,
                        excluded_reason="NOT_SELECTED_BY_USER",
                    )
                )
                continue

            # Untracked files excluded unless explicitly requested
            if cf.untracked and selected_set is None:
                excluded_files.append(file_path)
                entries.append(
                    StagingPlanEntry(
                        file_path=file_path,
                        change_type=cf.change_type.value,
                        risk=cf.risk,
                        excluded_reason="UNTRACKED_FILE_EXCLUDED_BY_DEFAULT",
                    )
                )
                continue

            # Eligible for staging
            orig_hash = compute_file_hash(full_path)
            patch_hash = sha256_of_text(cf.diff_text) if cf.diff_text else None
            hunk_ids = [h.hunk_id for h in cf.hunks]

            planned_files.append(file_path)
            entries.append(
                StagingPlanEntry(
                    file_path=file_path,
                    change_type=cf.change_type.value,
                    expected_original_hash=orig_hash,
                    expected_patch_hash=patch_hash,
                    hunk_ids=hunk_ids,
                    risk=cf.risk,
                )
            )

        # Explicitly check any requested files that escape repository
        if selected_files:
            for s_file in selected_files:
                full_path = (self.target_dir / s_file).resolve()
                try:
                    full_path.relative_to(self.target_dir)
                except ValueError:
                    if s_file not in excluded_files:
                        excluded_files.append(s_file)
                        entries.append(
                            StagingPlanEntry(
                                file_path=s_file,
                                change_type="UNKNOWN",
                                risk=ChangeRisk.HIGH,
                                excluded_reason="PATH_OUTSIDE_REPO: Path escapes repository root.",
                            )
                        )

        is_partial = len(excluded_files) > 0
        status = OperationStatus.PASSED if planned_files else OperationStatus.BLOCKED

        return StagingPlan(
            plan_id=plan_id,
            timestamp=now_str,
            repository_path=str(self.target_dir),
            branch=state.current_branch,
            head_commit=state.head_commit,
            approved_files=planned_files,
            excluded_files=excluded_files,
            entries=entries,
            is_partial=is_partial,
            status=status,
        )

    def write_plan_and_manifest(
        self, plan: StagingPlan, output_dir: Path
    ) -> Tuple[Path, Path]:
        """Write staging-plan.json and template staging-approval.json."""
        output_dir.mkdir(parents=True, exist_ok=True)
        plan_path = output_dir / "staging-plan.json"
        approval_path = output_dir / "staging-approval.json"

        # Write plan
        plan_path.write_text(json.dumps(plan.to_dict(), indent=2), encoding="utf-8")

        # Create approval manifest template
        entries: List[StagingApprovalEntry] = []
        for e in plan.entries:
            if not e.excluded_reason:
                entries.append(
                    StagingApprovalEntry(
                        file_path=e.file_path,
                        approved=False,  # Defaults to False until user approves
                        expected_original_hash=e.expected_original_hash,
                        expected_patch_hash=e.expected_patch_hash,
                        hunk_ids=e.hunk_ids,
                    )
                )

        approval = StagingApproval(
            approval_id=f"APP-{plan.plan_id}",
            plan_id=plan.plan_id,
            repository_id=plan.repository_path,
            branch=plan.branch,
            head_commit=plan.head_commit,
            timestamp=plan.timestamp,
            entries=entries,
            status=OperationStatus.APPROVAL_REQUIRED,
        )
        approval_path.write_text(json.dumps(approval.to_dict(), indent=2), encoding="utf-8")

        return plan_path, approval_path
