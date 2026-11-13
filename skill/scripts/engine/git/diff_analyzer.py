"""Module 3.4 — Diff Analyzer for RepoCraft Phase 5.

Inspects actual working-tree and staged diffs.
Captures changed paths, additions, deletions, renames, binary files, mode changes,
and hunk boundaries with bounded inspection limits.
"""
from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .git_environment import GitEnvironment
from .git_status_analyzer import GitStatusAnalyzer
from .git_types import ChangeFile, ChangeHunk, ChangeType, sha256_of_text

MAX_DIFF_LINES = 5000
MAX_FILE_BYTES = 5 * 1024 * 1024  # 5 MB


class DiffAnalyzer:
    """Analyzes Git diffs and parses structured hunk boundaries."""

    def __init__(self, target_dir: str, env: Optional[GitEnvironment] = None):
        self.target_dir = Path(target_dir).resolve()
        self.env = env or GitEnvironment(str(self.target_dir))
        self.status_analyzer = GitStatusAnalyzer(str(self.target_dir), self.env)

    def analyze_changes(self) -> List[ChangeFile]:
        """Analyze all working-tree, staged, and untracked changes."""
        files_dict: Dict[str, ChangeFile] = {}

        # 1. Parse staged diff
        staged_files = self._parse_diff(cached=True)
        for cf in staged_files:
            cf.staged = True
            files_dict[cf.file_path] = cf

        # 2. Parse unstaged working-tree diff
        unstaged_files = self._parse_diff(cached=False)
        for cf in unstaged_files:
            if cf.file_path in files_dict:
                existing = files_dict[cf.file_path]
                existing.unstaged = True
                existing.added_lines += cf.added_lines
                existing.deleted_lines += cf.deleted_lines
                existing.hunks.extend(cf.hunks)
                if cf.diff_text:
                    existing.diff_text += "\n" + cf.diff_text
            else:
                cf.unstaged = True
                files_dict[cf.file_path] = cf

        # 3. Add untracked files
        untracked = self.status_analyzer.get_untracked_files()
        for path_str in untracked:
            if path_str not in files_dict:
                cf = self._analyze_untracked_file(path_str)
                files_dict[path_str] = cf

        return list(files_dict.values())

    def get_staged_diff_text(self) -> str:
        """Return raw diff text of current staged changes."""
        code, out, _ = self.env.run_cmd(["diff", "--cached"])
        return out if code == 0 else ""

    def get_staged_diff_hash(self) -> str:
        """Compute SHA-256 hash of current staged diff."""
        return sha256_of_text(self.get_staged_diff_text())

    def _parse_diff(self, cached: bool = False) -> List[ChangeFile]:
        """Run git diff and parse output into structured ChangeFile records."""
        cmd = ["diff", "--no-color", "-U3"]
        if cached:
            cmd.append("--cached")

        code, out, _ = self.env.run_cmd(cmd)
        if code != 0 or not out:
            return []

        return self._parse_raw_diff(out)

    def _parse_raw_diff(self, diff_text: str) -> List[ChangeFile]:
        """Parse raw unified git diff into ChangeFile objects."""
        lines = diff_text.splitlines()
        change_files: List[ChangeFile] = []
        current_file: Optional[ChangeFile] = None
        current_hunk: Optional[ChangeHunk] = None
        file_diff_lines: List[str] = []

        hunk_header_re = re.compile(r"^@@\s+-(\d+)(?:,(\d+))?\s+\+(\d+)(?:,(\d+))?\s+@@(.*)")

        for line in lines:
            if line.startswith("diff --git "):
                # Finish previous file
                if current_file:
                    if current_hunk:
                        current_file.hunks.append(current_hunk)
                        current_hunk = None
                    current_file.diff_text = "\n".join(file_diff_lines)
                    change_files.append(current_file)

                file_diff_lines = [line]
                current_hunk = None

                # Extract path
                # diff --git a/path b/path
                parts = line.split(" ")
                rel_path = parts[2][2:] if len(parts) >= 3 and parts[2].startswith("a/") else "unknown"
                if len(parts) >= 4 and parts[3].startswith("b/"):
                    rel_path = parts[3][2:]

                current_file = ChangeFile(
                    file_path=rel_path,
                    change_type=ChangeType.MODIFIED,
                )
                continue

            if not current_file:
                continue

            file_diff_lines.append(line)

            if line.startswith("new file mode "):
                current_file.change_type = ChangeType.ADDED
                current_file.new_mode = line.replace("new file mode ", "").strip()
            elif line.startswith("deleted file mode "):
                current_file.change_type = ChangeType.DELETED
                current_file.old_mode = line.replace("deleted file mode ", "").strip()
            elif line.startswith("similarity index "):
                current_file.change_type = ChangeType.RENAMED
            elif line.startswith("rename from "):
                current_file.change_type = ChangeType.RENAMED
            elif line.startswith("Binary files ") or "differ" in line and "Binary" in line:
                current_file.is_binary = True

            match = hunk_header_re.match(line)
            if match:
                if current_hunk:
                    current_file.hunks.append(current_hunk)

                old_start = int(match.group(1))
                old_lines = int(match.group(2)) if match.group(2) else 1
                new_start = int(match.group(3))
                new_lines = int(match.group(4)) if match.group(4) else 1
                header = line

                hunk_id = f"{current_file.file_path}:H{len(current_file.hunks) + 1}:{new_start}"
                current_hunk = ChangeHunk(
                    hunk_id=hunk_id,
                    old_start=old_start,
                    old_lines=old_lines,
                    new_start=new_start,
                    new_lines=new_lines,
                    header=header,
                    lines=[line],
                )
            elif current_hunk:
                current_hunk.lines.append(line)
                if line.startswith("+") and not line.startswith("+++"):
                    current_hunk.added_count += 1
                    current_file.added_lines += 1
                elif line.startswith("-") and not line.startswith("---"):
                    current_hunk.deleted_count += 1
                    current_file.deleted_lines += 1

        if current_file:
            if current_hunk:
                current_file.hunks.append(current_hunk)
            current_file.diff_text = "\n".join(file_diff_lines)
            change_files.append(current_file)

        return change_files

    def _analyze_untracked_file(self, rel_path: str) -> ChangeFile:
        """Analyze an untracked file safely."""
        full_path = self.target_dir / rel_path
        is_binary = False
        is_oversized = False
        added_lines = 0

        try:
            if full_path.exists():
                size = full_path.stat().st_size
                if size > MAX_FILE_BYTES:
                    is_oversized = True
                else:
                    try:
                        content = full_path.read_bytes()
                        if b"\0" in content:
                            is_binary = True
                        else:
                            added_lines = len(content.splitlines())
                    except Exception:
                        is_binary = True
        except Exception:
            pass

        return ChangeFile(
            file_path=rel_path,
            change_type=ChangeType.UNTRACKED,
            untracked=True,
            is_binary=is_binary,
            is_oversized=is_oversized,
            added_lines=added_lines,
            deleted_lines=0,
        )

