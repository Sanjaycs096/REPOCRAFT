"""RepoCraft Phase 5 — Git Review, Conditional Commit & Publishing Engine.

Public package exports for Git environment inspection, status analysis,
diff parsing, risk classification, staging planning/execution,
commit generation/execution, remote inspection, push publishing, and PR drafting.
"""
from __future__ import annotations

from .change_review import ChangeReviewGenerator
from .change_risk_analyzer import ChangeRiskAnalyzer
from .commit_approval import CommitApprovalValidator
from .commit_executor import CommitExecutor
from .commit_message_generator import CommitMessageGenerator
from .diff_analyzer import DiffAnalyzer
from .git_environment import GitEnvironment, redact_url
from .git_orchestrator import GitOrchestrator
from .git_report_generator import GitReportGenerator
from .git_status_analyzer import GitStatusAnalyzer
from .git_types import (
    BranchInfo,
    ChangeFile,
    ChangeHunk,
    ChangeReview,
    ChangeRisk,
    ChangeType,
    CommitApproval,
    CommitInfo,
    CommitProposal,
    CommitReceipt,
    GitOperationResult,
    GitStatusEntry,
    GitWorkflowReport,
    OperationStatus,
    PublishResult,
    PullRequestDraft,
    PushApproval,
    PushMode,
    PushPlan,
    RemoteInfo,
    RepositoryState,
    StagingApproval,
    StagingApprovalEntry,
    StagingPlan,
    StagingPlanEntry,
    StagingResult,
    sha256_of_text,
)
from .pull_request_planner import PullRequestPlanner
from .push_approval import PushApprovalValidator
from .push_executor import PushExecutor
from .remote_inspector import RemoteInspector
from .staging_approval import StagingApprovalValidator
from .staging_executor import StagingExecutor
from .staging_planner import StagingPlanner

__all__ = [
    "GitEnvironment",
    "redact_url",
    "GitStatusAnalyzer",
    "DiffAnalyzer",
    "ChangeRiskAnalyzer",
    "ChangeReviewGenerator",
    "StagingPlanner",
    "StagingApprovalValidator",
    "StagingExecutor",
    "CommitMessageGenerator",
    "CommitApprovalValidator",
    "CommitExecutor",
    "RemoteInspector",
    "PushApprovalValidator",
    "PushExecutor",
    "PullRequestPlanner",
    "GitReportGenerator",
    "GitOrchestrator",
    "OperationStatus",
    "ChangeRisk",
    "ChangeType",
    "PushMode",
    "RepositoryState",
    "GitStatusEntry",
    "BranchInfo",
    "RemoteInfo",
    "CommitInfo",
    "ChangeHunk",
    "ChangeFile",
    "ChangeReview",
    "StagingPlan",
    "StagingPlanEntry",
    "StagingApproval",
    "StagingApprovalEntry",
    "StagingResult",
    "CommitProposal",
    "CommitApproval",
    "CommitReceipt",
    "PushPlan",
    "PushApproval",
    "PublishResult",
    "PullRequestDraft",
    "GitWorkflowReport",
    "sha256_of_text",
]

