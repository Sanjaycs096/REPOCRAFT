"""Module 3.18 — Git Orchestrator for RepoCraft Phase 5.

Coordinates end-to-end Git workflow operations:
inspect, review, plan-stage, stage-approved, draft-commit, commit-approved,
inspect-remote, plan-push, push-approved, and draft-pr.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from .change_review import ChangeReviewGenerator
from .commit_approval import CommitApprovalValidator
from .commit_executor import CommitExecutor
from .commit_message_generator import CommitMessageGenerator
from .diff_analyzer import DiffAnalyzer
from .git_environment import GitEnvironment
from .git_report_generator import GitReportGenerator
from .git_status_analyzer import GitStatusAnalyzer
from .git_types import (
    CommitReceipt,
    OperationStatus,
    PublishResult,
    PullRequestDraft,
    StagingResult,
)
from .pull_request_planner import PullRequestPlanner
from .push_approval import PushApprovalValidator
from .push_executor import PushExecutor
from .remote_inspector import RemoteInspector
from .staging_approval import StagingApprovalValidator
from .staging_executor import StagingExecutor
from .staging_planner import StagingPlanner


class GitOrchestrator:
    """Master controller for RepoCraft Phase 5 Git workflow operations."""

    def __init__(self, target_dir: str, env: Optional[GitEnvironment] = None):
        self.target_dir = Path(target_dir).resolve()
        self.env = env or GitEnvironment(str(self.target_dir))
        self.status_analyzer = GitStatusAnalyzer(str(self.target_dir), self.env)
        self.diff_analyzer = DiffAnalyzer(str(self.target_dir), self.env)
        self.review_generator = ChangeReviewGenerator(str(self.target_dir), self.env)
        self.staging_planner = StagingPlanner(str(self.target_dir), self.env)
        self.staging_executor = StagingExecutor(str(self.target_dir), self.env)
        self.commit_generator = CommitMessageGenerator(str(self.target_dir), self.env)
        self.commit_executor = CommitExecutor(str(self.target_dir), self.env)
        self.remote_inspector = RemoteInspector(str(self.target_dir), self.env)
        self.push_executor = PushExecutor(str(self.target_dir), self.env)
        self.pr_planner = PullRequestPlanner(str(self.target_dir), self.env)
        self.report_generator = GitReportGenerator(str(self.target_dir), self.env)

    def inspect(self, reports_dir: Optional[Path] = None) -> Dict[str, Any]:
        """Inspect repository and Git environment state."""
        state = self.env.inspect_state()
        data = state.to_dict()
        if reports_dir:
            reports_dir.mkdir(parents=True, exist_ok=True)
            out_file = reports_dir / "git-state.json"
            out_file.write_text(json.dumps(data, indent=2), encoding="utf-8")
        return data

    def review(self, reports_dir: Path) -> Dict[str, Any]:
        """Generate change review and risk classifications."""
        self.inspect(reports_dir)
        review = self.review_generator.generate_review()
        self.review_generator.write_reports(review, reports_dir)
        self.report_generator.generate_workflow_report(reports_dir)
        return review.to_dict()

    def plan_stage(
        self, reports_dir: Path, selected_files: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Generate deterministic staging plan without modifying index."""
        self.inspect(reports_dir)
        plan = self.staging_planner.plan_staging(selected_files)
        self.staging_planner.write_plan_and_manifest(plan, reports_dir)
        self.report_generator.generate_workflow_report(reports_dir)
        return plan.to_dict()

    def stage_approved(
        self, manifest_path: Path, reports_dir: Optional[Path] = None
    ) -> StagingResult:
        """Stage only explicitly approved files."""
        out_dir = reports_dir or manifest_path.parent
        validator = StagingApprovalValidator(str(self.target_dir), self.env)
        approval = validator.load_approval(manifest_path)
        if not approval:
            res = StagingResult(
                operation_id="STAGE-ERR",
                plan_id="NONE",
                status=OperationStatus.REJECTED,
                error_message=f"MANIFEST_NOT_FOUND_OR_INVALID: '{manifest_path}'.",
            )
            return res

        result = self.staging_executor.execute_staging(approval, out_dir)
        self.report_generator.generate_workflow_report(out_dir)
        return result

    def draft_commit(self, reports_dir: Path) -> Dict[str, Any]:
        """Draft Conventional Commit message from staged changes."""
        self.inspect(reports_dir)
        proposal = self.commit_generator.generate_proposal()
        self.commit_generator.write_proposal_and_manifest(proposal, reports_dir)
        self.report_generator.generate_workflow_report(reports_dir)
        return proposal.to_dict()

    def commit_approved(
        self, manifest_path: Path, reports_dir: Optional[Path] = None
    ) -> CommitReceipt:
        """Execute commit after validating explicit commit approval."""
        out_dir = reports_dir or manifest_path.parent
        validator = CommitApprovalValidator(str(self.target_dir), self.env)
        approval = validator.load_approval(manifest_path)
        if not approval:
            receipt = CommitReceipt(
                receipt_id="REC-ERR",
                commit_hash="",
                parent_commit="",
                branch="",
                message="",
                status=OperationStatus.REJECTED,
                error_message=f"MANIFEST_NOT_FOUND_OR_INVALID: '{manifest_path}'.",
            )
            return receipt

        receipt = self.commit_executor.execute_commit(approval, out_dir)
        self.report_generator.generate_workflow_report(out_dir)
        return receipt

    def inspect_remote(self, reports_dir: Optional[Path] = None) -> Dict[str, Any]:
        """Inspect remotes and branch tracking status."""
        status_info = self.remote_inspector.inspect_remote_status()
        if reports_dir:
            reports_dir.mkdir(parents=True, exist_ok=True)
            p = reports_dir / "remote-status.json"
            p.write_text(json.dumps(status_info, indent=2), encoding="utf-8")
        return status_info

    def plan_push(
        self,
        reports_dir: Path,
        remote_name: Optional[str] = None,
        destination_branch: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Generate push plan proposing destination and divergence checks."""
        push_plan = self.remote_inspector.plan_push(remote_name, destination_branch)
        self.remote_inspector.write_remote_status_and_push_plan(push_plan, reports_dir)
        self.report_generator.generate_workflow_report(reports_dir)
        return push_plan.to_dict()

    def push_approved(
        self, manifest_path: Path, reports_dir: Optional[Path] = None
    ) -> PublishResult:
        """Publish approved commit to remote destination."""
        out_dir = reports_dir or manifest_path.parent
        validator = PushApprovalValidator(str(self.target_dir), self.env)
        approval = validator.load_approval(manifest_path)
        if not approval:
            res = PublishResult(
                operation_id="PUSH-ERR",
                timestamp="",
                remote_name="",
                destination_branch="",
                pushed_commit="",
                status=OperationStatus.REJECTED,
                message=f"MANIFEST_NOT_FOUND_OR_INVALID: '{manifest_path}'.",
            )
            return res

        result = self.push_executor.execute_push(approval, out_dir)
        self.report_generator.generate_workflow_report(out_dir)
        return result

    def draft_pr(
        self,
        reports_dir: Path,
        target_branch: Optional[str] = None,
    ) -> PullRequestDraft:
        """Draft pull request proposal."""
        draft = self.pr_planner.generate_draft(target_branch, reports_dir)
        self.pr_planner.write_draft(draft, reports_dir)
        self.report_generator.generate_workflow_report(reports_dir)
        return draft

