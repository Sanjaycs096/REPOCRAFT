"""Git baseline intelligence analyzer for RepoCraft.

Extracts repository Git state, remotes, branches, commits, and uncommitted modifications safely.
Credentials in remote URLs are redacted.
Pre-existing user modifications are identified and treated as user-owned.
"""
from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path
from typing import List, Optional, Tuple

from .types import GitBaseline, GitRemote


def redact_remote_url(url: str) -> str:
    """Redact embedded passwords or auth tokens from git remote URLs."""
    if not url:
        return url
    # Matches http(s)://user:pass@host or https://token@host
    redacted = re.sub(r"://([^:@\s]+):([^@\s]+)@", r"://\1:***@", url)
    redacted = re.sub(r"://([^:@\s]+)@", r"://***@", redacted)
    return redacted


def run_git_cmd(repo_root: Path, args: List[str]) -> Tuple[int, str, str]:
    """Execute a read-only git command safely."""
    git_bin = shutil.which("git")
    if not git_bin:
        return -1, "", "git executable not found in PATH"
    try:
        proc = subprocess.run(
            [git_bin, *args],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            check=False,
            encoding="utf-8",
            errors="replace",
        )
        return proc.returncode, proc.stdout.rstrip("\r\n"), proc.stderr.rstrip("\r\n")
    except Exception as exc:
        return -1, "", str(exc)


def analyze_git_baseline(repo_root: Path) -> GitBaseline:
    """Analyze Git repository baseline state safely and non-destructively."""
    # Check if directory has a .git directory or parent git repo
    code, out, err = run_git_cmd(repo_root, ["rev-parse", "--is-inside-work-tree"])
    if code != 0 or out.lower() != "true":
        return GitBaseline(
            is_git_repository=False,
            warning="Target directory is not a Git repository or Git worktree.",
        )

    # Branch and detached HEAD
    is_detached = False
    code, branch, _ = run_git_cmd(repo_root, ["branch", "--show-current"])
    if code != 0 or not branch:
        # Check if detached HEAD
        code, head_name, _ = run_git_cmd(repo_root, ["rev-parse", "--abbrev-ref", "HEAD"])
        if head_name == "HEAD":
            is_detached = True
            branch = "(detached HEAD)"
        else:
            branch = head_name if head_name else "UNKNOWN"

    # HEAD commit details
    head_hash: Optional[str] = None
    head_short: Optional[str] = None
    head_date: Optional[str] = None
    head_author: Optional[str] = None

    code, commit_info, _ = run_git_cmd(
        repo_root, ["log", "-1", "--format=%H%n%h%n%cI%n%an <%ae>"]
    )
    if code == 0 and commit_info:
        parts = commit_info.splitlines()
        if len(parts) >= 1:
            head_hash = parts[0]
        if len(parts) >= 2:
            head_short = parts[1]
        if len(parts) >= 3:
            head_date = parts[2]
        if len(parts) >= 4:
            head_author = parts[3]

    # Shallow clone check
    code, is_shallow_str, _ = run_git_cmd(
        repo_root, ["rev-parse", "--is-shallow-repository"]
    )
    is_shallow = (code == 0 and is_shallow_str.lower() == "true")

    # Submodules check
    has_submodules = (repo_root / ".gitmodules").is_file()

    # Remotes
    remotes: List[GitRemote] = []
    code, remotes_raw, _ = run_git_cmd(repo_root, ["remote", "-v"])
    if code == 0 and remotes_raw:
        seen_remotes = set()
        for line in remotes_raw.splitlines():
            line = line.strip()
            if not line:
                continue
            parts = line.split()
            if len(parts) >= 2:
                r_name = parts[0]
                r_url = parts[1]
                key = (r_name, r_url)
                if key not in seen_remotes:
                    seen_remotes.add(key)
                    remotes.append(GitRemote(name=r_name, url=redact_remote_url(r_url)))

    # Staged, Unstaged, and Untracked files using git status --porcelain=v1
    staged_files: List[str] = []
    unstaged_files: List[str] = []
    untracked_files: List[str] = []

    code, status_raw, _ = run_git_cmd(
        repo_root, ["status", "--porcelain=v1", "--untracked-files=all"]
    )
    if code == 0 and status_raw:
        for line in status_raw.splitlines():
            if len(line) < 3:
                continue
            idx_status = line[0]
            work_status = line[1]
            file_path = line[3:].strip()
            # If path was renamed: "R  old -> new"
            if " -> " in file_path:
                file_path = file_path.split(" -> ")[1].strip()

            if idx_status == "?":
                untracked_files.append(file_path)
            else:
                if idx_status not in (" ", "?"):
                    staged_files.append(file_path)
                if work_status not in (" ", "?"):
                    unstaged_files.append(file_path)

    total_pre_existing = len(staged_files) + len(unstaged_files) + len(untracked_files)
    warning = None
    if total_pre_existing > 0:
        warning = (
            f"Repository contains {total_pre_existing} pre-existing user modification(s) "
            f"({len(staged_files)} staged, {len(unstaged_files)} unstaged, "
            f"{len(untracked_files)} untracked). All pre-existing work is user-owned "
            f"and must not be modified, overwritten, or committed by RepoCraft."
        )

    return GitBaseline(
        is_git_repository=True,
        current_branch=branch,
        head_commit=head_hash,
        head_commit_short=head_short,
        head_commit_date=head_date,
        head_commit_author=head_author,
        is_detached_head=is_detached,
        is_shallow=is_shallow,
        has_submodules=has_submodules,
        remotes=remotes,
        staged_files=staged_files,
        unstaged_files=unstaged_files,
        untracked_files=untracked_files,
        pre_existing_modifications_count=total_pre_existing,
        warning=warning,
    )
