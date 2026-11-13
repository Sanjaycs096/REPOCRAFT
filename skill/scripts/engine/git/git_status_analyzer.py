"""Module 3.3 — Git Status Analyzer for RepoCraft Phase 5.

Reliably parses Git status using machine-readable porcelain formats.
Handles staged, unstaged, untracked, ignored, deleted, renamed, and conflicted files,
including paths containing spaces and non-standard characters.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

from .git_environment import GitEnvironment
from .git_types import GitStatusEntry


class GitStatusAnalyzer:
    """Parses and analyzes Git status with machine-readable precision."""

    def __init__(self, target_dir: str, env: Optional[GitEnvironment] = None):
        self.target_dir = Path(target_dir).resolve()
        self.env = env or GitEnvironment(str(self.target_dir))

    def get_status_entries(self, include_ignored: bool = False) -> List[GitStatusEntry]:
        """Retrieve and parse all git status entries using porcelain -z format."""
        cmd = ["status", "--porcelain=v1", "-z"]
        if include_ignored:
            cmd.append("--ignored")

        code, out, err = self.env.run_cmd(cmd)
        if code != 0:
            return []

        entries: List[GitStatusEntry] = []
        tokens = out.split("\0")
        i = 0
        while i < len(tokens):
            raw = tokens[i]
            if not raw:
                i += 1
                continue

            if len(raw) < 3:
                i += 1
                continue

            index_status = raw[0]
            worktree_status = raw[1]
            file_path = raw[3:].strip().replace("\\", "/")

            orig_path = None
            # In porcelain -z, a rename/copy puts the destination path first, and the original path in the next token
            if index_status in ("R", "C") or worktree_status in ("R", "C"):
                if i + 1 < len(tokens):
                    orig_path = tokens[i + 1].strip().replace("\\", "/")
                    i += 1

            unmerged = (
                (index_status == "U" or worktree_status == "U")
                or (index_status == "A" and worktree_status == "A")
                or (index_status == "D" and worktree_status == "D")
            )

            staged = (index_status not in (" ", "?", "!") and not unmerged)
            unstaged = (worktree_status not in (" ", "?", "!") and not unmerged)
            untracked = (index_status == "?" and worktree_status == "?")
            ignored = (index_status == "!" and worktree_status == "!")

            entries.append(
                GitStatusEntry(
                    file_path=file_path,
                    index_status=index_status,
                    worktree_status=worktree_status,
                    staged=staged,
                    unstaged=unstaged,
                    untracked=untracked,
                    ignored=ignored,
                    unmerged=unmerged,
                    orig_path=orig_path,
                )
            )
            i += 1

        return entries

    def get_staged_files(self) -> List[str]:
        """Return list of staged file paths."""
        return [e.file_path for e in self.get_status_entries() if e.staged]

    def get_unstaged_files(self) -> List[str]:
        """Return list of unstaged file paths."""
        return [e.file_path for e in self.get_status_entries() if e.unstaged]

    def get_untracked_files(self) -> List[str]:
        """Return list of untracked file paths."""
        return [e.file_path for e in self.get_status_entries() if e.untracked]

    def has_unmerged_conflicts(self) -> bool:
        """Check if any files have unmerged conflict markers."""
        return any(e.unmerged for e in self.get_status_entries())
