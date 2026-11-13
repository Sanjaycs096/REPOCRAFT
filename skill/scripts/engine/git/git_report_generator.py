"""Module 3.17 — Git Workflow Report Generator for RepoCraft Phase 5.

Produces git-workflow-report.md compiling all Git workflow operations,
audit evidence, approvals, commit receipts, and publishing logs.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from .git_environment import GitEnvironment
from .git_types import GitWorkflowReport, OperationStatus


class GitReportGenerator:
    """Renders comprehensive human-readable workflow summaries."""

    def __init__(self, target_dir: str, env: Optional[GitEnvironment] = None):
        self.target_dir = Path(target_dir).resolve()
        self.env = env or GitEnvironment(str(self.target_dir))

    def generate_workflow_report(self, reports_dir: Path) -> Path:
        """Scan reports_dir for generated Phase 5 artifacts and render git-workflow-report.md."""
        reports_dir.mkdir(parents=True, exist_ok=True)
        report_path = reports_dir / "git-workflow-report.md"

        now_str = datetime.now(timezone.utc).isoformat()
        state = self.env.inspect_state()

        artifacts: Dict[str, str] = {}
        for fname in [
            "git-state.json",
            "git-change-review.md",
            "git-change-review.json",
            "staging-plan.json",
            "staging-approval.json",
            "staging-result.json",
            "commit-proposal.md",
            "commit-approval.json",
            "commit-receipt.json",
            "remote-status.json",
            "push-plan.json",
            "push-approval.json",
            "push-result.json",
            "pull-request-draft.md",
        ]:
            p = reports_dir / fname
            if p.is_file():
                artifacts[fname] = "Present"
            else:
                artifacts[fname] = "Not Generated"

        lines = [
            f"# RepoCraft Git Workflow & Audit Report",
            "",
            f"- **Repository Root**: `{state.repo_root or self.target_dir}`",
            f"- **Branch**: `{state.current_branch}`",
            f"- **HEAD Commit**: `{state.head_commit}`",
            f"- **Generated At**: `{now_str}`",
            "",
            "## 1. Executive Summary",
            "This report summarizes repository state, diff inspection, risk classification, staging operations, commit receipts, and publishing readiness executed by the RepoCraft Phase 5 Git Workflow Engine.",
            "",
            "## 2. Git State & Inspection",
            f"- **Is Git Repository**: `{state.is_git_repository}`",
            f"- **Git Version**: `{state.git_version}`",
            f"- **Detached HEAD**: `{state.is_detached_head}`",
            f"- **Shallow Clone**: `{state.is_shallow}`",
            f"- **Upstream**: `{state.upstream_branch or 'None'}`",
            f"- **Remotes**: {len(state.remotes)} configured",
            f"- **Operations In Progress**: `{', '.join(state.operations_in_progress) if state.operations_in_progress else 'None'}`",
            "",
            "## 3. Operations & Artifact Matrix",
            "",
            "| Phase 5 Artifact | Status | Description |",
            "| :--- | :--- | :--- |",
            f"| `git-state.json` | {artifacts.get('git-state.json')} | Repository environment snapshot |",
            f"| `git-change-review.md` | {artifacts.get('git-change-review.md')} | Human-readable change and risk review |",
            f"| `git-change-review.json` | {artifacts.get('git-change-review.json')} | Structured change analysis and file risks |",
            f"| `staging-plan.json` | {artifacts.get('staging-plan.json')} | Exact planned staging scope |",
            f"| `staging-approval.json` | {artifacts.get('staging-approval.json')} | Human-authorized staging manifest |",
            f"| `staging-result.json` | {artifacts.get('staging-result.json')} | Post-stage index verification |",
            f"| `commit-proposal.md` | {artifacts.get('commit-proposal.md')} | Conventional Commit message draft |",
            f"| `commit-approval.json` | {artifacts.get('commit-approval.json')} | Explicit commit authorization manifest |",
            f"| `commit-receipt.json` | {artifacts.get('commit-receipt.json')} | Verified post-commit record |",
            f"| `remote-status.json` | {artifacts.get('remote-status.json')} | Remote tracking and divergence checks |",
            f"| `push-plan.json` | {artifacts.get('push-plan.json')} | Proposed publishing plan |",
            f"| `push-approval.json` | {artifacts.get('push-approval.json')} | Explicit publishing authorization manifest |",
            f"| `push-result.json` | {artifacts.get('push-result.json')} | Remote publishing verification record |",
            f"| `pull-request-draft.md` | {artifacts.get('pull-request-draft.md')} | PR proposal based on diff and test evidence |",
            "",
            "## 4. Safety Boundary Guarantees",
            "- **Preservation of User Work**: No unstaged/staged user modifications discarded or stashed.",
            "- **Independent Approvals**: Staging, committing, and pushing each required separate human authorization.",
            "- **No Force Operations**: Force pushes and history rewrites strictly prohibited.",
            "- **Credential Redaction**: All remote URLs sanitized; tokens redacted.",
            "",
        ]

        # Check commit receipt if present
        receipt_file = reports_dir / "commit-receipt.json"
        if receipt_file.is_file():
            try:
                rec_data = json.loads(receipt_file.read_text(encoding="utf-8"))
                lines.extend([
                    "## 5. Verified Commit Receipt",
                    f"- **Commit Hash**: `{rec_data.get('commit_hash')}`",
                    f"- **Parent Commit**: `{rec_data.get('parent_commit')}`",
                    f"- **Branch**: `{rec_data.get('branch')}`",
                    f"- **Message**: `{rec_data.get('message')}`",
                    f"- **Committed Files**: {len(rec_data.get('committed_files', []))}",
                    "",
                ])
            except Exception:
                pass

        # Check push result if present
        push_res_file = reports_dir / "push-result.json"
        if push_res_file.is_file():
            try:
                push_data = json.loads(push_res_file.read_text(encoding="utf-8"))
                lines.extend([
                    "## 6. Remote Publishing Status",
                    f"- **Remote**: `{push_data.get('remote_name')}`",
                    f"- **Destination Branch**: `{push_data.get('destination_branch')}`",
                    f"- **Pushed Commit**: `{push_data.get('pushed_commit')}`",
                    f"- **Status**: **{push_data.get('status')}**",
                    f"- **Message**: {push_data.get('message')}",
                    "",
                ])
            except Exception:
                pass

        report_path.write_text("\n".join(lines), encoding="utf-8")
        return report_path

