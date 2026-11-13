"""Module 3.11 — Commit Approval Validator for RepoCraft Phase 5.

Validates explicit human commit authorizations.
Cryptographically checks staged diff hash, parent commit hash, branch binding,
and commit message integrity.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional, Tuple

from .diff_analyzer import DiffAnalyzer
from .git_environment import GitEnvironment
from .git_types import CommitApproval, OperationStatus, sha256_of_text


class CommitApprovalValidator:
    """Validates commit authorization manifest against live repository state."""

    def __init__(self, target_dir: str, env: Optional[GitEnvironment] = None):
        self.target_dir = Path(target_dir).resolve()
        self.env = env or GitEnvironment(str(self.target_dir))
        self.diff_analyzer = DiffAnalyzer(str(self.target_dir), self.env)

    def load_approval(self, manifest_path: Path) -> Optional[CommitApproval]:
        """Load and parse commit-approval.json."""
        if not manifest_path.is_file():
            return None
        try:
            data = json.loads(manifest_path.read_text(encoding="utf-8"))
            return CommitApproval(
                approval_id=data.get("approval_id", ""),
                repository_id=data.get("repository_id", ""),
                branch=data.get("branch", ""),
                parent_commit=data.get("parent_commit", ""),
                commit_message=data.get("commit_message", ""),
                commit_message_hash=data.get("commit_message_hash", ""),
                staged_patch_hash=data.get("staged_patch_hash", ""),
                approved_files=data.get("approved_files", []),
                approved=data.get("approved", False),
                approved_by=data.get("approved_by"),
                approved_at=data.get("approved_at"),
                engine_version=data.get("engine_version", "0.6.0"),
                status=OperationStatus(data.get("status", "APPROVAL_REQUIRED")),
            )
        except Exception:
            return None

    def validate_approval(self, approval: CommitApproval) -> Tuple[bool, str]:
        """Validate commit authorization manifest.

        Returns:
            (is_valid, failure_reason)
        """
        # 1. Check approval flag
        if not approval.approved:
            return False, "APPROVAL_REQUIRED: Commit manifest is marked unapproved (approved=false)."

        state = self.env.inspect_state()

        # 2. Check branch
        if approval.branch and approval.branch != state.current_branch:
            return False, f"BRANCH_MISMATCH: Approval for branch '{approval.branch}', but current branch is '{state.current_branch}'."

        # 3. Check parent commit
        if approval.parent_commit and approval.parent_commit != state.head_commit:
            return False, f"PARENT_COMMIT_MISMATCH: Approval based on parent '{approval.parent_commit}', but HEAD is '{state.head_commit}'."

        # 4. Check commit message hash
        expected_msg_hash = sha256_of_text(approval.commit_message)
        if approval.commit_message_hash and approval.commit_message_hash != expected_msg_hash:
            return False, "COMMIT_MESSAGE_TAMPERED: Message hash does not match commit_message content."

        # 5. Check staged patch hash
        curr_staged_hash = self.diff_analyzer.get_staged_diff_hash()
        if approval.staged_patch_hash and approval.staged_patch_hash != curr_staged_hash:
            return False, f"STAGED_DIFF_HASH_MISMATCH: Staged changes modified after approval was generated (expected {approval.staged_patch_hash}, got {curr_staged_hash})."

        return True, "Commit approval verified successfully."

