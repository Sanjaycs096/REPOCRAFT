"""Module 3.12 — Commit Executor for RepoCraft Phase 5.

Executes atomic Git commits only after explicit, verified human authorization.
Respects hooks without bypassing, forbids amending/detached HEAD/history rewriting,
and emits commit-receipt.json.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from .commit_approval import CommitApprovalValidator
from .git_environment import GitEnvironment
from .git_status_analyzer import GitStatusAnalyzer
from .git_types import CommitApproval, CommitReceipt, OperationStatus, sha256_of_text


class CommitExecutor:
    """Executes authorized Git commits under strict verification boundaries."""

    def __init__(self, target_dir: str, env: Optional[GitEnvironment] = None):
        self.target_dir = Path(target_dir).resolve()
        self.env = env or GitEnvironment(str(self.target_dir))
        self.status_analyzer = GitStatusAnalyzer(str(self.target_dir), self.env)
        self.validator = CommitApprovalValidator(str(self.target_dir), self.env)

    def execute_commit(
        self, approval: CommitApproval, reports_dir: Optional[Path] = None
    ) -> CommitReceipt:
        """Execute commit after rigorous validation."""
        now_str = datetime.now(timezone.utc).isoformat()
        receipt_id = f"REC-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"

        # 1. State verification
        state = self.env.inspect_state()

        if state.is_detached_head:
            return CommitReceipt(
                receipt_id=receipt_id,
                commit_hash="",
                parent_commit=state.head_commit,
                branch=state.current_branch,
                message=approval.commit_message,
                status=OperationStatus.BLOCKED,
                error_message="DETACHED_HEAD_REJECTED: Committing on a detached HEAD is strictly forbidden.",
                timestamp=now_str,
            )

        if state.operations_in_progress:
            return CommitReceipt(
                receipt_id=receipt_id,
                commit_hash="",
                parent_commit=state.head_commit,
                branch=state.current_branch,
                message=approval.commit_message,
                status=OperationStatus.BLOCKED,
                error_message=f"OPERATION_IN_PROGRESS: Git operations active: {', '.join(state.operations_in_progress)}.",
                timestamp=now_str,
            )

        # 2. Check approval manifest
        is_valid, msg = self.validator.validate_approval(approval)
        if not is_valid:
            return CommitReceipt(
                receipt_id=receipt_id,
                commit_hash="",
                parent_commit=state.head_commit,
                branch=state.current_branch,
                message=approval.commit_message,
                status=OperationStatus.REJECTED,
                error_message=msg,
                timestamp=now_str,
            )

        parent_before = state.head_commit

        # 3. Execute git commit (respecting hooks, no --no-verify, no --amend)
        code, out, err = self.env.run_cmd(["commit", "-m", approval.commit_message])
        if code != 0:
            return CommitReceipt(
                receipt_id=receipt_id,
                commit_hash="",
                parent_commit=parent_before,
                branch=state.current_branch,
                message=approval.commit_message,
                status=OperationStatus.FAILED,
                error_message=f"GIT_COMMIT_FAILED: {err or out}",
                timestamp=now_str,
            )

        # 4. Post-commit verification
        code, new_head, _ = self.env.run_cmd(["rev-parse", "HEAD"])
        new_commit = new_head.strip() if code == 0 else ""

        code, committed_files_raw, _ = self.env.run_cmd(["diff-tree", "--no-commit-id", "--name-only", "-r", "HEAD"])
        committed_files = committed_files_raw.splitlines() if code == 0 else []

        code, commit_diff, _ = self.env.run_cmd(["diff", "HEAD~1..HEAD"])
        commit_diff_hash = sha256_of_text(commit_diff) if code == 0 else ""

        receipt = CommitReceipt(
            receipt_id=receipt_id,
            commit_hash=new_commit,
            parent_commit=parent_before,
            branch=state.current_branch,
            message=approval.commit_message,
            committed_files=committed_files,
            committed_patch_hash=commit_diff_hash,
            timestamp=now_str,
            status=OperationStatus.PASSED,
        )

        if reports_dir:
            reports_dir.mkdir(parents=True, exist_ok=True)
            receipt_path = reports_dir / "commit-receipt.json"
            receipt_path.write_text(json.dumps(receipt.to_dict(), indent=2), encoding="utf-8")

        return receipt

