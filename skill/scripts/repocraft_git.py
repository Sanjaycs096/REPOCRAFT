#!/usr/bin/env python3
"""RepoCraft Phase 5 — CLI Interface for Git Review, Conditional Commit & Publishing.

Supports subcommands:
- inspect: Read-only Git environment snapshot
- review: Change analysis and risk classification
- plan-stage: Deterministic staging plan generation
- stage-approved: Apply verified staging approval
- draft-commit: Propose Conventional Commit message
- commit-approved: Execute verified commit approval
- inspect-remote: Inspect remote configuration and tracking
- plan-push: Propose publishing plan and checks
- push-approved: Execute verified remote push
- draft-pr: Generate evidence-backed PR proposal
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import List, Optional

# Ensure RepoCraft package modules can be imported
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Reconfigure standard streams to UTF-8 with replacement for Windows / non-UTF-8 consoles
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
if hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from engine.git import (
    GitOrchestrator,
    OperationStatus,
)


def build_parser() -> argparse.ArgumentParser:
    """Build CLI argument parser with subcommands."""
    parser = argparse.ArgumentParser(
        prog="repocraft_git",
        description="RepoCraft Phase 5: Git Review, Conditional Commit & Publishing Engine",
    )
    subparsers = parser.add_subparsers(dest="command", help="Git workflow subcommand")

    # 1. inspect
    p_inspect = subparsers.add_parser("inspect", help="Inspect Git environment and state (read-only)")
    p_inspect.add_argument("--target-dir", default=".", help="Target repository directory")
    p_inspect.add_argument("--reports-dir", default=None, help="Optional reports output directory")
    p_inspect.add_argument("--json", action="store_true", help="Print state as JSON")

    # 2. review
    p_review = subparsers.add_parser("review", help="Review repository changes and classify risk")
    p_review.add_argument("--target-dir", default=".", help="Target repository directory")
    p_review.add_argument("--reports-dir", default=".repocraft/reports", help="Reports directory")

    # 3. plan-stage
    p_plan_stage = subparsers.add_parser("plan-stage", help="Generate deterministic staging plan")
    p_plan_stage.add_argument("--target-dir", default=".", help="Target repository directory")
    p_plan_stage.add_argument("--reports-dir", default=".repocraft/reports", help="Reports directory")
    p_plan_stage.add_argument("--files", nargs="*", default=None, help="Explicit file paths to plan for staging")

    # 4. stage-approved
    p_stage = subparsers.add_parser("stage-approved", help="Stage changes using verified staging approval")
    p_stage.add_argument("--target-dir", default=".", help="Target repository directory")
    p_stage.add_argument("--manifest", required=True, help="Path to staging-approval.json")
    p_stage.add_argument("--reports-dir", default=None, help="Reports directory")

    # 5. draft-commit
    p_draft_commit = subparsers.add_parser("draft-commit", help="Draft commit message from staged changes")
    p_draft_commit.add_argument("--target-dir", default=".", help="Target repository directory")
    p_draft_commit.add_argument("--reports-dir", default=".repocraft/reports", help="Reports directory")

    # 6. commit-approved
    p_commit = subparsers.add_parser("commit-approved", help="Execute commit using verified commit approval")
    p_commit.add_argument("--target-dir", default=".", help="Target repository directory")
    p_commit.add_argument("--manifest", required=True, help="Path to commit-approval.json")
    p_commit.add_argument("--reports-dir", default=None, help="Reports directory")

    # 7. inspect-remote
    p_insp_remote = subparsers.add_parser("inspect-remote", help="Inspect remote configuration and divergence")
    p_insp_remote.add_argument("--target-dir", default=".", help="Target repository directory")
    p_insp_remote.add_argument("--reports-dir", default=None, help="Reports directory")
    p_insp_remote.add_argument("--json", action="store_true", help="Print remote status as JSON")

    # 8. plan-push
    p_plan_push = subparsers.add_parser("plan-push", help="Plan publishing to remote repository")
    p_plan_push.add_argument("--target-dir", default=".", help="Target repository directory")
    p_plan_push.add_argument("--reports-dir", default=".repocraft/reports", help="Reports directory")
    p_plan_push.add_argument("--remote", default=None, help="Remote name (e.g. origin)")
    p_plan_push.add_argument("--dest-branch", default=None, help="Destination branch")

    # 9. push-approved
    p_push = subparsers.add_parser("push-approved", help="Publish commit to remote with verified approval")
    p_push.add_argument("--target-dir", default=".", help="Target repository directory")
    p_push.add_argument("--manifest", required=True, help="Path to push-approval.json")
    p_push.add_argument("--reports-dir", default=None, help="Reports directory")

    # 10. draft-pr
    p_pr = subparsers.add_parser("draft-pr", help="Draft pull request proposal")
    p_pr.add_argument("--target-dir", default=".", help="Target repository directory")
    p_pr.add_argument("--reports-dir", default=".repocraft/reports", help="Reports directory")
    p_pr.add_argument("--target-branch", default=None, help="Target upstream branch (default: main)")

    return parser


def main(args: Optional[List[str]] = None) -> int:
    """CLI entrypoint."""
    parser = build_parser()
    parsed = parser.parse_args(args)

    if not parsed.command:
        parser.print_help()
        return 1

    target_dir = Path(parsed.target_dir).resolve()
    if not target_dir.exists():
        sys.stderr.write(f"Error: Target directory '{target_dir}' does not exist.\n")
        return 1

    orchestrator = GitOrchestrator(str(target_dir))

    try:
        # 1. inspect
        if parsed.command == "inspect":
            rep_dir = Path(parsed.reports_dir).resolve() if parsed.reports_dir else None
            data = orchestrator.inspect(rep_dir)
            if getattr(parsed, "json", False):
                print(json.dumps(data, indent=2))
            else:
                print(f"Git Repository: {data.get('is_git_repository')}")
                print(f"Branch: {data.get('current_branch')}")
                print(f"HEAD: {data.get('head_commit')}")
                print(f"Remotes: {len(data.get('remotes', []))}")
            return 0 if data.get("is_git_repository") else 7

        # 2. review
        elif parsed.command == "review":
            rep_dir = Path(parsed.reports_dir).resolve()
            review_data = orchestrator.review(rep_dir)
            print(f"Review completed: {review_data.get('review_id')}")
            print(f"Overall Risk: {review_data.get('overall_risk')}")
            print(f"Files Evaluated: {len(review_data.get('files', []))}")
            return 0

        # 3. plan-stage
        elif parsed.command == "plan-stage":
            rep_dir = Path(parsed.reports_dir).resolve()
            plan_data = orchestrator.plan_stage(rep_dir, parsed.files)
            print(f"Staging Plan: {plan_data.get('plan_id')}")
            print(f"Planned Files: {len(plan_data.get('approved_files', []))}")
            print(f"Excluded Files: {len(plan_data.get('excluded_files', []))}")
            return 0

        # 4. stage-approved
        elif parsed.command == "stage-approved":
            manifest_path = Path(parsed.manifest).resolve()
            rep_dir = Path(parsed.reports_dir).resolve() if parsed.reports_dir else None
            result = orchestrator.stage_approved(manifest_path, rep_dir)
            print(f"Staging Result: {result.status.value}")
            if result.error_message:
                print(f"Error: {result.error_message}")
            if result.status == OperationStatus.PASSED:
                print(f"Staged {len(result.staged_files)} files successfully.")
                return 0
            elif result.status == OperationStatus.REJECTED:
                return 3
            elif result.status == OperationStatus.BLOCKED:
                return 4
            else:
                return 2

        # 5. draft-commit
        elif parsed.command == "draft-commit":
            rep_dir = Path(parsed.reports_dir).resolve()
            proposal = orchestrator.draft_commit(rep_dir)
            print(f"Commit Proposal: {proposal.get('proposal_id')}")
            print(f"Summary: {proposal.get('summary')}")
            return 0

        # 6. commit-approved
        elif parsed.command == "commit-approved":
            manifest_path = Path(parsed.manifest).resolve()
            rep_dir = Path(parsed.reports_dir).resolve() if parsed.reports_dir else None
            receipt = orchestrator.commit_approved(manifest_path, rep_dir)
            print(f"Commit Status: {receipt.status.value}")
            if receipt.error_message:
                print(f"Error: {receipt.error_message}")
            if receipt.status == OperationStatus.PASSED:
                print(f"Created Commit: {receipt.commit_hash}")
                return 0
            elif receipt.status == OperationStatus.REJECTED:
                return 3
            elif receipt.status == OperationStatus.BLOCKED:
                return 4
            else:
                return 5

        # 7. inspect-remote
        elif parsed.command == "inspect-remote":
            rep_dir = Path(parsed.reports_dir).resolve() if parsed.reports_dir else None
            data = orchestrator.inspect_remote(rep_dir)
            if getattr(parsed, "json", False):
                print(json.dumps(data, indent=2))
            else:
                print(f"Current Branch: {data.get('current_branch')}")
                print(f"Upstream: {data.get('upstream_branch') or 'None'}")
                print(f"Ahead: {data.get('ahead_count')}, Behind: {data.get('behind_count')}")
                print(f"Diverged: {data.get('is_diverged')}")
            return 0

        # 8. plan-push
        elif parsed.command == "plan-push":
            rep_dir = Path(parsed.reports_dir).resolve()
            push_plan = orchestrator.plan_push(rep_dir, parsed.remote, parsed.dest_branch)
            print(f"Push Plan: {push_plan.get('plan_id')}")
            print(f"Target Remote: {push_plan.get('remote_name')}")
            print(f"Destination Branch: {push_plan.get('destination_branch')}")
            if push_plan.get("status") == OperationStatus.CONFLICT.value:
                return 6
            elif push_plan.get("status") == OperationStatus.BLOCKED.value:
                return 4
            return 0

        # 9. push-approved
        elif parsed.command == "push-approved":
            manifest_path = Path(parsed.manifest).resolve()
            rep_dir = Path(parsed.reports_dir).resolve() if parsed.reports_dir else None
            publish_res = orchestrator.push_approved(manifest_path, rep_dir)
            print(f"Publish Status: {publish_res.status.value}")
            print(f"Message: {publish_res.message}")
            if publish_res.status == OperationStatus.PASSED:
                return 0
            elif publish_res.status == OperationStatus.REJECTED:
                return 3
            elif publish_res.status == OperationStatus.BLOCKED:
                return 4
            else:
                return 6

        # 10. draft-pr
        elif parsed.command == "draft-pr":
            rep_dir = Path(parsed.reports_dir).resolve()
            draft = orchestrator.draft_pr(rep_dir, parsed.target_branch)
            print(f"PR Draft: {draft.draft_id}")
            print(f"Title: {draft.title}")
            return 0

    except Exception as exc:
        sys.stderr.write(f"Unexpected error: {exc}\n")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())

