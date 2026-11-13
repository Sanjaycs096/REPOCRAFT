"""Module 3.10 — Commit Message Generator for RepoCraft Phase 5.

Generates Conventional Commit proposals from verified staged changes.
Produces commit-proposal.md and initial commit-approval.json template.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .diff_analyzer import DiffAnalyzer
from .git_environment import GitEnvironment
from .git_status_analyzer import GitStatusAnalyzer
from .git_types import (
    CommitApproval,
    CommitProposal,
    OperationStatus,
    sha256_of_text,
)


class CommitMessageGenerator:
    """Proposes clear, conventional commit messages based on verified staged changes."""

    def __init__(self, target_dir: str, env: Optional[GitEnvironment] = None):
        self.target_dir = Path(target_dir).resolve()
        self.env = env or GitEnvironment(str(self.target_dir))
        self.status_analyzer = GitStatusAnalyzer(str(self.target_dir), self.env)
        self.diff_analyzer = DiffAnalyzer(str(self.target_dir), self.env)

    def generate_proposal(self) -> CommitProposal:
        """Analyze staged diff and synthesize a Conventional Commit proposal."""
        staged_files = self.status_analyzer.get_staged_files()
        diff_text = self.diff_analyzer.get_staged_diff_text()
        diff_hash = sha256_of_text(diff_text)

        now_str = datetime.now(timezone.utc).isoformat()
        prop_id = f"PROP-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"

        if not staged_files:
            return CommitProposal(
                proposal_id=prop_id,
                timestamp=now_str,
                summary="chore: empty commit proposal (no staged changes)",
                body="No files are currently staged in the index.",
                full_message="chore: empty commit proposal (no staged changes)",
                commit_type="chore",
                staged_patch_hash=diff_hash,
                staged_files=[],
            )

        commit_type, scope = self._infer_type_and_scope(staged_files)
        summary = self._generate_summary(commit_type, scope, staged_files)
        body = self._generate_body(staged_files, diff_text)
        full_message = f"{summary}\n\n{body}" if body else summary

        return CommitProposal(
            proposal_id=prop_id,
            timestamp=now_str,
            summary=summary,
            body=body,
            full_message=full_message,
            commit_type=commit_type,
            scope=scope,
            breaking_change=False,
            staged_patch_hash=diff_hash,
            staged_files=staged_files,
        )

    def write_proposal_and_manifest(
        self, proposal: CommitProposal, output_dir: Path
    ) -> Tuple[Path, Path]:
        """Write commit-proposal.md and template commit-approval.json."""
        output_dir.mkdir(parents=True, exist_ok=True)
        md_path = output_dir / "commit-proposal.md"
        json_path = output_dir / "commit-approval.json"

        # 1. Write proposal Markdown
        md_lines = [
            f"# Proposed Commit Message — `{proposal.proposal_id}`",
            "",
            f"- **Timestamp**: `{proposal.timestamp}`",
            f"- **Type**: `{proposal.commit_type}`",
            f"- **Scope**: `{proposal.scope or 'none'}`",
            f"- **Staged Files**: {len(proposal.staged_files)}",
            f"- **Staged Diff SHA-256**: `{proposal.staged_patch_hash}`",
            "",
            "## Commit Message",
            "```gitcommit",
            proposal.full_message,
            "```",
            "",
            "## Staged Files",
        ]
        for f in proposal.staged_files:
            md_lines.append(f"- `{f}`")
        md_lines.append("")

        md_path.write_text("\n".join(md_lines), encoding="utf-8")

        # 2. Write commit approval template
        state = self.env.inspect_state()
        approval = CommitApproval(
            approval_id=f"APP-{proposal.proposal_id}",
            repository_id=str(self.target_dir),
            branch=state.current_branch,
            parent_commit=state.head_commit,
            commit_message=proposal.full_message,
            commit_message_hash=sha256_of_text(proposal.full_message),
            staged_patch_hash=proposal.staged_patch_hash,
            approved_files=proposal.staged_files,
            approved=False,  # Defaults to False until user approves
            engine_version="0.6.0",
            status=OperationStatus.APPROVAL_REQUIRED,
        )
        json_path.write_text(json.dumps(approval.to_dict(), indent=2), encoding="utf-8")

        return md_path, json_path

    def _infer_type_and_scope(self, staged_files: List[str]) -> Tuple[str, Optional[str]]:
        """Infer Conventional Commit type and optional scope from file paths."""
        all_docs = all(f.lower().endswith((".md", ".rst", ".txt")) or "doc" in f.lower() for f in staged_files)
        if all_docs:
            return "docs", None

        all_tests = all("test" in f.lower() for f in staged_files)
        if all_tests:
            return "test", None

        all_ci = all(".github" in f or "ci" in f.lower() for f in staged_files)
        if all_ci:
            return "ci", "workflow"

        if any(f.endswith((".json", ".toml", ".yaml", ".yml", ".lock")) for f in staged_files):
            return "chore", "config"

        # Check for single common directory
        scopes = set()
        for f in staged_files:
            parts = f.replace("\\", "/").split("/")
            if len(parts) > 1:
                scopes.add(parts[0])

        scope = list(scopes)[0] if len(scopes) == 1 else None
        return "chore", scope

    def _generate_summary(self, commit_type: str, scope: Optional[str], staged_files: List[str]) -> str:
        """Formulate concise summary line."""
        prefix = f"{commit_type}({scope}):" if scope else f"{commit_type}:"
        if len(staged_files) == 1:
            file_name = Path(staged_files[0]).name
            summary = f"{prefix} update {file_name}"
        else:
            summary = f"{prefix} update {len(staged_files)} repository files"
        return summary[:72]

    def _generate_body(self, staged_files: List[str], diff_text: str) -> str:
        """Generate descriptive commit message body."""
        lines = ["Apply verified repository modifications:"]
        for f in staged_files[:10]:
            lines.append(f"- {f}")
        if len(staged_files) > 10:
            lines.append(f"- ... and {len(staged_files) - 10} more files")
        return "\n".join(lines)

