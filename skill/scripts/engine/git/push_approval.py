"""Module 3.14 — Push Approval Validator for RepoCraft Phase 5.

Validates explicit human publishing authorizations.
Rejects force pushes, unapproved remotes or branches, and mismatched commit hashes.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional, Tuple

from .git_environment import GitEnvironment
from .git_types import OperationStatus, PushApproval, PushMode


class PushApprovalValidator:
    """Validates publishing authorizations prior to remote push operations."""

    def __init__(self, target_dir: str, env: Optional[GitEnvironment] = None):
        self.target_dir = Path(target_dir).resolve()
        self.env = env or GitEnvironment(str(self.target_dir))

    def load_approval(self, manifest_path: Path) -> Optional[PushApproval]:
        """Load and parse push-approval.json."""
        if not manifest_path.is_file():
            return None
        try:
            data = json.loads(manifest_path.read_text(encoding="utf-8"))
            return PushApproval(
                approval_id=data.get("approval_id", ""),
                repository_id=data.get("repository_id", ""),
                remote_name=data.get("remote_name", ""),
                sanitized_remote_url=data.get("sanitized_remote_url", ""),
                source_branch=data.get("source_branch", ""),
                destination_branch=data.get("destination_branch", ""),
                commit_hash=data.get("commit_hash", ""),
                expected_remote_base=data.get("expected_remote_base"),
                push_mode=PushMode(data.get("push_mode", "NORMAL")),
                approved=data.get("approved", False),
                approved_by=data.get("approved_by"),
                approved_at=data.get("approved_at"),
                engine_version=data.get("engine_version", "0.6.0"),
                status=OperationStatus(data.get("status", "APPROVAL_REQUIRED")),
            )
        except Exception:
            return None

    def validate_approval(self, approval: PushApproval) -> Tuple[bool, str]:
        """Validate push authorization manifest against repository state.

        Returns:
            (is_valid, failure_reason)
        """
        # 1. Check approval flag
        if not approval.approved:
            return False, "APPROVAL_REQUIRED: Push manifest is marked unapproved (approved=false)."

        state = self.env.inspect_state()

        # 2. Check remote existence
        matching_remote = [r for r in state.remotes if r.name == approval.remote_name]
        if not matching_remote:
            return False, f"REMOTE_NOT_FOUND: Configured remote '{approval.remote_name}' not found in repository."

        # 3. Check source branch
        if approval.source_branch and approval.source_branch != state.current_branch:
            return False, f"SOURCE_BRANCH_MISMATCH: Approval for branch '{approval.source_branch}', but currently on '{state.current_branch}'."

        # 4. Check commit hash
        if approval.commit_hash and approval.commit_hash != state.head_commit:
            return False, f"COMMIT_MISMATCH: Approval for commit '{approval.commit_hash}', but HEAD is '{state.head_commit}'."

        return True, "Push approval verified successfully."

