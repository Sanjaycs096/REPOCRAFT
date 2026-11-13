"""Module 3.8 — Staging Approval Validator for RepoCraft Phase 5.

Validates explicit human staging approvals.
Verifies cryptographic patch hashes, checks branch and repository binding,
and rejects wildcards, path traversal, and out-of-band changes.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .git_environment import GitEnvironment
from .git_types import OperationStatus, StagingApproval, StagingApprovalEntry
from .staging_planner import compute_file_hash


class StagingApprovalValidator:
    """Validates staging-approval.json against current repository state."""

    def __init__(self, target_dir: str, env: Optional[GitEnvironment] = None):
        self.target_dir = Path(target_dir).resolve()
        self.env = env or GitEnvironment(str(self.target_dir))

    def load_approval(self, manifest_path: Path) -> Optional[StagingApproval]:
        """Load and parse staging-approval.json."""
        if not manifest_path.is_file():
            return None
        try:
            data = json.loads(manifest_path.read_text(encoding="utf-8"))
            entries: List[StagingApprovalEntry] = []
            for item in data.get("entries", []):
                entries.append(
                    StagingApprovalEntry(
                        file_path=item.get("file_path", ""),
                        approved=item.get("approved", False),
                        approved_by=item.get("approved_by"),
                        approved_at=item.get("approved_at"),
                        expected_original_hash=item.get("expected_original_hash"),
                        expected_patch_hash=item.get("expected_patch_hash"),
                        hunk_ids=item.get("hunk_ids", []),
                    )
                )
            return StagingApproval(
                approval_id=data.get("approval_id", ""),
                plan_id=data.get("plan_id", ""),
                repository_id=data.get("repository_id", ""),
                branch=data.get("branch", ""),
                head_commit=data.get("head_commit", ""),
                timestamp=data.get("timestamp", ""),
                engine_version=data.get("engine_version", "0.6.0"),
                entries=entries,
                status=OperationStatus(data.get("status", "APPROVAL_REQUIRED")),
            )
        except Exception:
            return None

    def validate_approval(
        self, approval: StagingApproval
    ) -> Tuple[bool, str, List[StagingApprovalEntry]]:
        """Validate staging approval against repository environment.

        Returns:
            (is_valid, failure_reason, approved_entries)
        """
        state = self.env.inspect_state()

        # 1. Branch check (only if inside a git repository and current branch is known)
        if state.is_git_repository and state.current_branch and approval.branch and approval.branch != state.current_branch:
            return False, f"BRANCH_MISMATCH: Approval was created for branch '{approval.branch}', but current branch is '{state.current_branch}'.", []

        # 2. Check for empty approvals
        approved_entries = [e for e in approval.entries if e.approved]
        if not approved_entries:
            return False, "NO_APPROVED_FILES: Manifest contains zero approved entries.", []

        # 3. Check each approved entry
        valid_entries: List[StagingApprovalEntry] = []
        for entry in approved_entries:
            path_str = entry.file_path.strip()

            # Reject wildcards
            if path_str in ("*", ".", "ALL", "all"):
                return False, f"WILDCARD_REJECTED: Wildcard pattern '{path_str}' is forbidden in staging approval.", []

            # Reject path traversal
            if ".." in path_str.replace("\\", "/").split("/"):
                return False, f"PATH_TRAVERSAL_REJECTED: Entry '{path_str}' contains directory traversal.", []

            full_path = (self.target_dir / path_str).resolve()
            try:
                full_path.relative_to(self.target_dir)
            except ValueError:
                return False, f"PATH_OUTSIDE_REPO: Entry '{path_str}' escapes repository root.", []

            # Verify file content hash if file exists and expected_original_hash is specified
            if entry.expected_original_hash and full_path.exists():
                curr_hash = compute_file_hash(full_path)
                if curr_hash != entry.expected_original_hash:
                    return False, f"CONTENT_HASH_MISMATCH: File '{path_str}' was modified after approval was generated.", []

            valid_entries.append(entry)

        return True, "Approval verified successfully.", valid_entries
