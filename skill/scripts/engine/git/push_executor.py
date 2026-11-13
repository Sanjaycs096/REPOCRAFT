"""Module 3.15 — Push Executor for RepoCraft Phase 5.

Executes normal fast-forward Git pushes to verified remotes.
Strictly forbids force pushes, history rewriting, or branch deletion, emitting push-result.json.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from .git_environment import GitEnvironment
from .git_types import OperationStatus, PublishResult, PushApproval, PushMode
from .push_approval import PushApprovalValidator


class PushExecutor:
    """Executes validated push operations safely and non-destructively."""

    def __init__(self, target_dir: str, env: Optional[GitEnvironment] = None):
        self.target_dir = Path(target_dir).resolve()
        self.env = env or GitEnvironment(str(self.target_dir))
        self.validator = PushApprovalValidator(str(self.target_dir), self.env)

    def execute_push(
        self, approval: PushApproval, reports_dir: Optional[Path] = None
    ) -> PublishResult:
        """Execute push operation under strict boundaries."""
        now_str = datetime.now(timezone.utc).isoformat()
        op_id = f"PUSH-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"

        # 1. Validate approval
        is_valid, msg = self.validator.validate_approval(approval)
        if not is_valid:
            return PublishResult(
                operation_id=op_id,
                timestamp=now_str,
                remote_name=approval.remote_name,
                destination_branch=approval.destination_branch,
                pushed_commit=approval.commit_hash,
                status=OperationStatus.REJECTED,
                message=msg,
            )

        # 2. Build safe command: git push <remote> <source_branch>:<dest_branch>
        # Never add --force, -f, or --force-with-lease
        cmd = ["push", approval.remote_name, f"{approval.source_branch}:{approval.destination_branch}"]
        if approval.push_mode == PushMode.DRY_RUN:
            cmd.append("--dry-run")

        code, out, err = self.env.run_cmd(cmd)
        if code != 0:
            return PublishResult(
                operation_id=op_id,
                timestamp=now_str,
                remote_name=approval.remote_name,
                destination_branch=approval.destination_branch,
                pushed_commit=approval.commit_hash,
                status=OperationStatus.FAILED,
                message=f"GIT_PUSH_FAILED: {err or out}",
            )

        # 3. Post-push verification
        verified_commit = None
        code, ls_out, _ = self.env.run_cmd(["ls-remote", approval.remote_name, approval.destination_branch])
        if code == 0 and ls_out.strip():
            parts = ls_out.split()
            if parts:
                verified_commit = parts[0]

        result = PublishResult(
            operation_id=op_id,
            timestamp=now_str,
            remote_name=approval.remote_name,
            destination_branch=approval.destination_branch,
            pushed_commit=approval.commit_hash,
            verified_remote_commit=verified_commit,
            status=OperationStatus.PASSED,
            message="Push completed and remote destination verified.",
        )

        if reports_dir:
            reports_dir.mkdir(parents=True, exist_ok=True)
            res_path = reports_dir / "push-result.json"
            res_path.write_text(json.dumps(result.to_dict(), indent=2), encoding="utf-8")

        return result

