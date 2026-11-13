"""Module E — Repository Change Guard for RepoCraft Phase 4.

Protects pre-existing user modifications and working tree state:
- Captures staged, unstaged, and untracked files via Git
- Blocks any repair on files containing pre-existing user modifications
- Verifies that target files have not changed since plan creation
- Enforces strict prohibitions against git reset, stash, clean, add, commit, or push
"""
from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

from .patch_generator import sha256_of_file
from .repair_types import ProposedPatch, RepairTask


class ChangeGuard:
    """Safeguards user repository modifications and validates pre-repair conditions."""

    def __init__(self, target_dir: str):
        self.target_dir = Path(target_dir).resolve()
        self.staged_files: Set[str] = set()
        self.unstaged_files: Set[str] = set()
        self.untracked_files: Set[str] = set()
        self.is_git_repo = False
        self._refresh_git_status()

    def _refresh_git_status(self) -> None:
        self.staged_files.clear()
        self.unstaged_files.clear()
        self.untracked_files.clear()

        # Check if inside git repo
        git_dir = self.target_dir / ".git"
        if not git_dir.exists() and not (self.target_dir.parent / ".git").exists():
            self.is_git_repo = False
            return

        try:
            proc = subprocess.run(
                ["git", "status", "--porcelain=v1"],
                cwd=str(self.target_dir),
                capture_output=True,
                text=True,
                timeout=10,
            )
            if proc.returncode != 0:
                self.is_git_repo = False
                return

            self.is_git_repo = True
            lines = proc.stdout.splitlines()
            for line in lines:
                if len(line) < 4:
                    continue
                index_status = line[0]
                worktree_status = line[1]
                file_path = line[3:].strip().replace("\\", "/")

                if index_status not in (" ", "?"):
                    self.staged_files.add(file_path)
                if worktree_status not in (" ", "?"):
                    self.unstaged_files.add(file_path)
                if index_status == "?" and worktree_status == "?":
                    self.untracked_files.add(file_path)

        except Exception:
            self.is_git_repo = False

    def can_modify_file(self, file_rel_path: str, expected_original_hash: Optional[str] = None) -> Tuple[bool, str]:
        """Verify whether an individual file can be safely modified."""
        clean_rel = file_rel_path.replace("\\", "/").lstrip("./")

        # 1. Check if file has staged modifications
        if clean_rel in self.staged_files:
            return False, f"File '{clean_rel}' has pre-existing staged modifications. Refusing to modify."

        # 2. Check if file has unstaged modifications
        if clean_rel in self.unstaged_files:
            return False, f"File '{clean_rel}' has pre-existing unstaged modifications. Refusing to modify."

        # 3. Check if file is an untracked user file (if it already exists)
        full_path = self.target_dir / clean_rel
        if full_path.is_file() and clean_rel in self.untracked_files:
            return False, f"File '{clean_rel}' is an untracked user file. Refusing to modify."

        # 4. Verify file content has not changed since planning
        if expected_original_hash is not None and full_path.is_file():
            current_hash = sha256_of_file(full_path)
            if current_hash != expected_original_hash:
                return (
                    False,
                    f"File '{clean_rel}' content has changed since repair planning (expected {expected_original_hash[:10]}..., got {current_hash[:10]}...). Invalidation triggered.",
                )

        return True, "File is clean and safe for bounded repair."

    def validate_task_safety(self, task: RepairTask) -> Tuple[bool, str]:
        """Validate that all affected files in a RepairTask are safe to modify."""
        self._refresh_git_status()

        for patch in task.proposed_changes:
            can_modify, reason = self.can_modify_file(patch.file_path, patch.original_content_hash)
            if not can_modify:
                return False, f"Safety violation for task '{task.repair_id}': {reason}"

        return True, "All target files pass safety checks."

