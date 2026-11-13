"""Module 3.13 — Remote Inspector for RepoCraft Phase 5.

Inspects remote configurations, branch tracking, divergence, and publishing readiness.
Sanitizes credentials, defaults to offline execution, and produces remote-status.json and push-plan.json.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .git_environment import GitEnvironment
from .git_types import (
    OperationStatus,
    PushApproval,
    PushMode,
    PushPlan,
    RemoteInfo,
)


class RemoteInspector:
    """Safely inspects remote repositories and branch tracking configuration."""

    def __init__(self, target_dir: str, env: Optional[GitEnvironment] = None):
        self.target_dir = Path(target_dir).resolve()
        self.env = env or GitEnvironment(str(self.target_dir))

    def inspect_remote_status(self) -> Dict[str, Any]:
        """Inspect remotes and current branch upstream tracking."""
        state = self.env.inspect_state()

        upstream = state.upstream_branch
        ahead_count = 0
        behind_count = 0
        is_diverged = False
        is_behind = False

        if upstream:
            # Check divergence: git rev-list --left-right --count HEAD...@{u}
            code, out, _ = self.env.run_cmd(["rev-list", "--left-right", "--count", f"HEAD...{upstream}"])
            if code == 0 and out.strip():
                parts = out.strip().split()
                if len(parts) >= 2:
                    try:
                        ahead_count = int(parts[0])
                        behind_count = int(parts[1])
                        is_behind = behind_count > 0
                        is_diverged = ahead_count > 0 and behind_count > 0
                    except ValueError:
                        pass

        default_remote = state.remotes[0] if state.remotes else None

        return {
            "repository_path": str(self.target_dir),
            "current_branch": state.current_branch,
            "head_commit": state.head_commit,
            "upstream_branch": upstream,
            "ahead_count": ahead_count,
            "behind_count": behind_count,
            "is_diverged": is_diverged,
            "is_behind": is_behind,
            "has_remotes": len(state.remotes) > 0,
            "remotes": [r.to_dict() for r in state.remotes],
        }

    def plan_push(
        self,
        remote_name: Optional[str] = None,
        destination_branch: Optional[str] = None,
    ) -> PushPlan:
        """Create a PushPlan proposing publishing destination and checks."""
        status_info = self.inspect_remote_status()
        state = self.env.inspect_state()

        now_str = datetime.now(timezone.utc).isoformat()
        plan_id = f"PUSH-PLAN-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"

        if not state.remotes:
            return PushPlan(
                plan_id=plan_id,
                timestamp=now_str,
                remote_name=remote_name or "origin",
                sanitized_remote_url="",
                source_branch=state.current_branch,
                destination_branch=destination_branch or state.current_branch,
                commit_hash=state.head_commit,
                status=OperationStatus.BLOCKED,
            )

        target_remote_name = remote_name or state.remotes[0].name
        matching_remotes = [r for r in state.remotes if r.name == target_remote_name]
        selected_remote = matching_remotes[0] if matching_remotes else state.remotes[0]

        dest_branch = destination_branch or state.current_branch

        # Determine expected remote base commit hash if tracking exists
        expected_remote_base = None
        if status_info["upstream_branch"]:
            code, upstream_head, _ = self.env.run_cmd(["rev-parse", status_info["upstream_branch"]])
            if code == 0 and upstream_head.strip():
                expected_remote_base = upstream_head.strip()

        status = OperationStatus.PASSED
        if status_info["is_diverged"]:
            status = OperationStatus.CONFLICT
        elif status_info["is_behind"]:
            status = OperationStatus.BLOCKED

        return PushPlan(
            plan_id=plan_id,
            timestamp=now_str,
            remote_name=selected_remote.name,
            sanitized_remote_url=selected_remote.push_url,
            source_branch=state.current_branch,
            destination_branch=dest_branch,
            commit_hash=state.head_commit,
            expected_remote_base=expected_remote_base,
            push_mode=PushMode.NORMAL,
            is_diverged=status_info["is_diverged"],
            is_behind=status_info["is_behind"],
            is_protected=False,
            status=status,
        )

    def write_remote_status_and_push_plan(
        self, push_plan: PushPlan, output_dir: Path
    ) -> Tuple[Path, Path, Path]:
        """Write remote-status.json, push-plan.json, and template push-approval.json."""
        output_dir.mkdir(parents=True, exist_ok=True)
        status_path = output_dir / "remote-status.json"
        plan_path = output_dir / "push-plan.json"
        approval_path = output_dir / "push-approval.json"

        status_info = self.inspect_remote_status()
        status_path.write_text(json.dumps(status_info, indent=2), encoding="utf-8")
        plan_path.write_text(json.dumps(push_plan.to_dict(), indent=2), encoding="utf-8")

        approval = PushApproval(
            approval_id=f"APP-{push_plan.plan_id}",
            repository_id=str(self.target_dir),
            remote_name=push_plan.remote_name,
            sanitized_remote_url=push_plan.sanitized_remote_url,
            source_branch=push_plan.source_branch,
            destination_branch=push_plan.destination_branch,
            commit_hash=push_plan.commit_hash,
            expected_remote_base=push_plan.expected_remote_base,
            push_mode=push_plan.push_mode,
            approved=False,  # Defaults to False
            engine_version="0.6.0",
            status=OperationStatus.APPROVAL_REQUIRED,
        )
        approval_path.write_text(json.dumps(approval.to_dict(), indent=2), encoding="utf-8")

        return status_path, plan_path, approval_path

