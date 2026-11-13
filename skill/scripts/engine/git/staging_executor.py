"""Module 3.9 — Staging Executor for RepoCraft Phase 5.

Applies approved staging plans using explicit per-file staging.
Verifies index integrity post-staging and produces staging-result.json.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .diff_analyzer import DiffAnalyzer
from .git_environment import GitEnvironment
from .git_status_analyzer import GitStatusAnalyzer
from .git_types import OperationStatus, StagingApproval, StagingResult
from .staging_approval import StagingApprovalValidator


class StagingExecutor:
    """Executes validated staging approvals safely and deterministically."""

    def __init__(self, target_dir: str, env: Optional[GitEnvironment] = None):
        self.target_dir = Path(target_dir).resolve()
        self.env = env or GitEnvironment(str(self.target_dir))
        self.status_analyzer = GitStatusAnalyzer(str(self.target_dir), self.env)
        self.diff_analyzer = DiffAnalyzer(str(self.target_dir), self.env)
        self.approval_validator = StagingApprovalValidator(str(self.target_dir), self.env)

    def execute_staging(
        self, approval: StagingApproval, reports_dir: Optional[Path] = None
    ) -> StagingResult:
        """Stage only approved files and verify index."""
        op_id = f"STAGE-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"

        # 1. Check for operations in progress
        state = self.env.inspect_state()
        if state.operations_in_progress:
            return StagingResult(
                operation_id=op_id,
                plan_id=approval.plan_id,
                status=OperationStatus.BLOCKED,
                error_message=f"OPERATION_IN_PROGRESS: Git operations active: {', '.join(state.operations_in_progress)}.",
            )

        # 2. Validate approval manifest
        is_valid, msg, approved_entries = self.approval_validator.validate_approval(approval)
        if not is_valid:
            return StagingResult(
                operation_id=op_id,
                plan_id=approval.plan_id,
                status=OperationStatus.REJECTED,
                error_message=msg,
            )

        # 3. Stage each approved file individually
        staged_files: List[str] = []
        warnings: List[str] = []

        for entry in approved_entries:
            path_str = entry.file_path
            # Stage using git add -- <path>
            code, out, err = self.env.run_cmd(["add", "--", path_str])
            if code != 0:
                warnings.append(f"Failed to stage '{path_str}': {err or out}")
            else:
                staged_files.append(path_str)

        # 4. Post-staging verification
        currently_staged = self.status_analyzer.get_staged_files()
        unexpected_staged = [p for p in currently_staged if p not in [e.file_path for e in approved_entries]]

        diff_hash = self.diff_analyzer.get_staged_diff_hash()

        status = OperationStatus.PASSED if staged_files and not unexpected_staged else OperationStatus.FAILED
        err_msg = None
        if unexpected_staged:
            status = OperationStatus.FAILED
            err_msg = f"UNEXPECTED_STAGED_CONTENT: Files outside approved manifest found in index: {unexpected_staged}"

        result = StagingResult(
            operation_id=op_id,
            plan_id=approval.plan_id,
            staged_files=staged_files,
            verified_paths=[p for p in staged_files if p in currently_staged],
            staged_diff_hash=diff_hash,
            status=status,
            error_message=err_msg,
            warnings=warnings,
        )

        if reports_dir:
            reports_dir.mkdir(parents=True, exist_ok=True)
            res_path = reports_dir / "staging-result.json"
            res_path.write_text(json.dumps(result.to_dict(), indent=2), encoding="utf-8")

        return result

