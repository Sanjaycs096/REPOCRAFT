"""Data models and type definitions for RepoCraft Phase 5 Git Workflow Engine.

Defines contracts for repository state, status entries, diff hunks, risk classifications,
staging plans, staging approvals, commit proposals, commit receipts, push approvals,
publish results, and pull request drafts.
"""
from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class OperationStatus(str, Enum):
    """Explicit operation status."""
    NOT_RUN = "NOT_RUN"
    PASSED = "PASSED"
    FAILED = "FAILED"
    BLOCKED = "BLOCKED"
    APPROVAL_REQUIRED = "APPROVAL_REQUIRED"
    REJECTED = "REJECTED"
    CONFLICT = "CONFLICT"
    SKIPPED = "SKIPPED"
    UNKNOWN = "UNKNOWN"


class ChangeRisk(str, Enum):
    """Risk tier for change evaluation."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"
    UNKNOWN = "UNKNOWN"


class ChangeType(str, Enum):
    """File modification type in Git."""
    ADDED = "ADDED"
    MODIFIED = "MODIFIED"
    DELETED = "DELETED"
    RENAMED = "RENAMED"
    COPIED = "COPIED"
    TYPE_CHANGED = "TYPE_CHANGED"
    UNTRACKED = "UNTRACKED"
    IGNORED = "IGNORED"
    UNMERGED = "UNMERGED"


class PushMode(str, Enum):
    """Push execution mode."""
    NORMAL = "NORMAL"
    DRY_RUN = "DRY_RUN"


def sha256_of_text(text: str) -> str:
    """Compute SHA-256 hash of text string."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


@dataclass
class GitOperationResult:
    """Generic result wrapper for a Git operation."""
    operation_name: str
    status: OperationStatus
    message: str = ""
    exit_code: int = 0
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class RemoteInfo:
    """Git remote configuration with sanitized URLs."""
    name: str
    fetch_url: str
    push_url: str
    is_credential_redacted: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class BranchInfo:
    """Git branch state."""
    name: str
    is_current: bool = False
    upstream: Optional[str] = None
    ahead: int = 0
    behind: int = 0
    head_commit: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class CommitInfo:
    """Commit metadata."""
    commit_hash: str
    parent_hashes: List[str] = field(default_factory=list)
    author: str = ""
    author_email: str = ""
    date: str = ""
    message: str = ""
    is_signed: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class RepositoryState:
    """Snapshot of Git repository and environment."""
    is_git_repository: bool
    git_version: str = ""
    repo_root: str = ""
    current_branch: str = ""
    head_commit: str = ""
    is_detached_head: bool = False
    is_shallow: bool = False
    upstream_branch: Optional[str] = None
    operations_in_progress: List[str] = field(default_factory=list)
    remotes: List[RemoteInfo] = field(default_factory=list)
    commit_signing_enabled: bool = False
    user_name: Optional[str] = None
    user_email: Optional[str] = None
    warning: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class GitStatusEntry:
    """Raw parsed Git status entry."""
    file_path: str
    index_status: str
    worktree_status: str
    staged: bool = False
    unstaged: bool = False
    untracked: bool = False
    ignored: bool = False
    unmerged: bool = False
    orig_path: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ChangeHunk:
    """Individual diff hunk."""
    hunk_id: str
    old_start: int
    old_lines: int
    new_start: int
    new_lines: int
    header: str
    lines: List[str] = field(default_factory=list)
    added_count: int = 0
    deleted_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ChangeFile:
    """Comprehensive change information for a file."""
    file_path: str
    change_type: ChangeType
    staged: bool = False
    unstaged: bool = False
    untracked: bool = False
    is_binary: bool = False
    is_oversized: bool = False
    old_mode: Optional[str] = None
    new_mode: Optional[str] = None
    added_lines: int = 0
    deleted_lines: int = 0
    hunks: List[ChangeHunk] = field(default_factory=list)
    risk: ChangeRisk = ChangeRisk.UNKNOWN
    risk_reasons: List[str] = field(default_factory=list)
    sensitive_patterns: List[str] = field(default_factory=list)
    is_partially_reviewed: bool = False
    original_content_hash: Optional[str] = None
    new_content_hash: Optional[str] = None
    diff_text: str = ""
    approval_requirement: str = ""
    recommendation: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ChangeReview:
    """Aggregated repository change review."""
    review_id: str
    timestamp: str
    repository_path: str
    branch: str
    head_commit: str
    files: List[ChangeFile] = field(default_factory=list)
    overall_risk: ChangeRisk = ChangeRisk.LOW
    critical_files: List[str] = field(default_factory=list)
    high_risk_files: List[str] = field(default_factory=list)
    sensitive_files: List[str] = field(default_factory=list)
    binary_files: List[str] = field(default_factory=list)
    untracked_files: List[str] = field(default_factory=list)
    summary: str = ""
    review_recommendations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class StagingPlanEntry:
    """Planned staging item."""
    file_path: str
    change_type: str
    expected_original_hash: Optional[str] = None
    expected_patch_hash: Optional[str] = None
    hunk_ids: List[str] = field(default_factory=list)
    risk: ChangeRisk = ChangeRisk.LOW
    excluded_reason: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class StagingPlan:
    """Deterministic staging plan."""
    plan_id: str
    timestamp: str
    repository_path: str
    branch: str
    head_commit: str
    approved_files: List[str] = field(default_factory=list)
    excluded_files: List[str] = field(default_factory=list)
    entries: List[StagingPlanEntry] = field(default_factory=list)
    is_partial: bool = False
    status: OperationStatus = OperationStatus.NOT_RUN

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class StagingApprovalEntry:
    """Individual file approval in staging manifest."""
    file_path: str
    approved: bool = False
    approved_by: Optional[str] = None
    approved_at: Optional[str] = None
    expected_original_hash: Optional[str] = None
    expected_patch_hash: Optional[str] = None
    hunk_ids: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class StagingApproval:
    """Explicit staging approval manifest."""
    approval_id: str
    plan_id: str
    repository_id: str
    branch: str
    head_commit: str
    timestamp: str
    engine_version: str = "0.6.0"
    entries: List[StagingApprovalEntry] = field(default_factory=list)
    status: OperationStatus = OperationStatus.APPROVAL_REQUIRED

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class StagingResult:
    """Result of staging execution."""
    operation_id: str
    plan_id: str
    staged_files: List[str] = field(default_factory=list)
    verified_paths: List[str] = field(default_factory=list)
    staged_diff_hash: str = ""
    status: OperationStatus = OperationStatus.NOT_RUN
    error_message: Optional[str] = None
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class CommitProposal:
    """Proposed commit message from staged changes."""
    proposal_id: str
    timestamp: str
    summary: str
    body: str
    full_message: str
    commit_type: str = "chore"
    scope: Optional[str] = None
    breaking_change: bool = False
    breaking_description: Optional[str] = None
    staged_patch_hash: str = ""
    staged_files: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class CommitApproval:
    """Explicit commit authorization manifest."""
    approval_id: str
    repository_id: str
    branch: str
    parent_commit: str
    commit_message: str
    commit_message_hash: str
    staged_patch_hash: str
    approved_files: List[str] = field(default_factory=list)
    approved: bool = False
    approved_by: Optional[str] = None
    approved_at: Optional[str] = None
    engine_version: str = "0.6.0"
    status: OperationStatus = OperationStatus.APPROVAL_REQUIRED

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class CommitReceipt:
    """Verified commit record post-commit."""
    receipt_id: str
    commit_hash: str
    parent_commit: str
    branch: str
    message: str
    committed_files: List[str] = field(default_factory=list)
    committed_patch_hash: str = ""
    timestamp: str = ""
    status: OperationStatus = OperationStatus.PASSED
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class PushPlan:
    """Proposed publishing plan."""
    plan_id: str
    timestamp: str
    remote_name: str
    sanitized_remote_url: str
    source_branch: str
    destination_branch: str
    commit_hash: str
    expected_remote_base: Optional[str] = None
    push_mode: PushMode = PushMode.NORMAL
    is_diverged: bool = False
    is_behind: bool = False
    is_protected: bool = False
    status: OperationStatus = OperationStatus.NOT_RUN

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class PushApproval:
    """Explicit push authorization manifest."""
    approval_id: str
    repository_id: str
    remote_name: str
    sanitized_remote_url: str
    source_branch: str
    destination_branch: str
    commit_hash: str
    expected_remote_base: Optional[str] = None
    push_mode: PushMode = PushMode.NORMAL
    approved: bool = False
    approved_by: Optional[str] = None
    approved_at: Optional[str] = None
    engine_version: str = "0.6.0"
    status: OperationStatus = OperationStatus.APPROVAL_REQUIRED

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class PublishResult:
    """Result of remote push execution."""
    operation_id: str
    timestamp: str
    remote_name: str
    destination_branch: str
    pushed_commit: str
    verified_remote_commit: Optional[str] = None
    status: OperationStatus = OperationStatus.NOT_RUN
    message: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class PullRequestDraft:
    """Pull request description proposal."""
    draft_id: str
    timestamp: str
    title: str
    description: str
    source_branch: str
    target_branch: str
    commits: List[str] = field(default_factory=list)
    risk_summary: str = ""
    test_evidence: str = ""
    known_limitations: List[str] = field(default_factory=list)
    status: OperationStatus = OperationStatus.PASSED

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class GitWorkflowReport:
    """Overall Phase 5 Git workflow report data."""
    report_id: str
    timestamp: str
    repository_root: str
    branch: str
    head_commit: str
    state_status: OperationStatus = OperationStatus.PASSED
    review_status: OperationStatus = OperationStatus.PASSED
    staging_status: OperationStatus = OperationStatus.NOT_RUN
    commit_status: OperationStatus = OperationStatus.NOT_RUN
    push_status: OperationStatus = OperationStatus.NOT_RUN
    summary: str = ""
    warnings: List[str] = field(default_factory=list)
    artifacts: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
