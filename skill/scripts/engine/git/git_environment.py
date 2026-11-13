"""Module 3.2 — Git Environment Inspector for RepoCraft Phase 5.

Inspects Git availability, repository structure, branch, HEAD, detached state,
in-progress operations (merge/rebase/cherry-pick/revert), configured remotes with
credential redaction, and signing configuration.
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import List, Optional, Tuple

from .git_types import RemoteInfo, RepositoryState


def redact_url(url: str) -> Tuple[str, bool]:
    """Redact embedded credentials and tokens from URLs.

    Returns:
        (sanitized_url, was_redacted)
    """
    if not url:
        return "", False

    was_redacted = False
    sanitized = url

    # Matches http(s)://user:pass@host
    if re.search(r"://([^:@\s]+):([^@\s]+)@", sanitized):
        sanitized = re.sub(r"://([^:@\s]+):([^@\s]+)@", r"://\1:***@", sanitized)
        was_redacted = True

    # Matches http(s)://token@host or http(s)://x-token-auth:token@host
    if re.search(r"://([^:@\s]+)@", sanitized):
        # Only redact if not already sanitized
        if ":***@" not in sanitized:
            sanitized = re.sub(r"://([^:@\s]+)@", r"://***@", sanitized)
            was_redacted = True

    # Matches git@host with credentials or token parameters
    if re.search(r"(\?|&)token=[^&\s]+", sanitized):
        sanitized = re.sub(r"(\?|&)token=[^&\s]+", r"\1token=***", sanitized)
        was_redacted = True

    return sanitized, was_redacted


class GitEnvironment:
    """Safely inspects Git environment and repository state."""

    def __init__(self, target_dir: str):
        self.target_dir = Path(target_dir).resolve()
        self.git_bin = shutil.which("git")

    def run_cmd(
        self,
        args: List[str],
        timeout: int = 15,
        cwd: Optional[Path] = None,
    ) -> Tuple[int, str, str]:
        """Execute a git command safely using argument array without shell=True."""
        if not self.git_bin:
            return -1, "", "git executable not found in PATH"

        work_dir = str(cwd or self.target_dir)
        try:
            proc = subprocess.run(
                [self.git_bin, *args],
                cwd=work_dir,
                capture_output=True,
                text=True,
                check=False,
                encoding="utf-8",
                errors="replace",
                timeout=timeout,
            )
            return proc.returncode, proc.stdout.rstrip("\r\n"), proc.stderr.rstrip("\r\n")
        except subprocess.TimeoutExpired:
            return -2, "", f"Git command timed out after {timeout} seconds"
        except Exception as exc:
            return -1, "", f"Failed to execute git command: {exc}"

    def inspect_state(self) -> RepositoryState:
        """Inspect and return the current repository state snapshot."""
        if not self.git_bin:
            return RepositoryState(
                is_git_repository=False,
                warning="git executable is not installed or not in PATH.",
            )

        # 1. Check Git version
        code, out, _ = self.run_cmd(["--version"])
        git_version = out.strip() if code == 0 else "UNKNOWN"

        # 2. Check if inside work tree
        code, out, _ = self.run_cmd(["rev-parse", "--is-inside-work-tree"])
        if code != 0 or out.lower() != "true":
            return RepositoryState(
                is_git_repository=False,
                git_version=git_version,
                repo_root=str(self.target_dir),
                warning="Target directory is not a Git repository.",
            )

        # 3. Repository root
        code, repo_root, _ = self.run_cmd(["rev-parse", "--show-toplevel"])
        if code != 0:
            repo_root = str(self.target_dir)
        else:
            repo_root = str(Path(repo_root).resolve())

        # 4. Current branch and detached HEAD
        is_detached = False
        code, branch, _ = self.run_cmd(["branch", "--show-current"])
        branch = branch.strip()
        if code != 0 or not branch:
            code, head_ref, _ = self.run_cmd(["rev-parse", "--abbrev-ref", "HEAD"])
            head_ref = head_ref.strip()
            if head_ref == "HEAD":
                is_detached = True
                branch = "(detached HEAD)"
            else:
                branch = head_ref if head_ref else "UNKNOWN"

        # 5. HEAD commit
        code, head_commit, _ = self.run_cmd(["rev-parse", "HEAD"])
        head_commit = head_commit.strip() if code == 0 else ""

        # 6. Shallow clone
        code, is_shallow_str, _ = self.run_cmd(["rev-parse", "--is-shallow-repository"])
        is_shallow = is_shallow_str.strip().lower() == "true" if code == 0 else False
        if not is_shallow and (Path(repo_root) / ".git" / "shallow").exists():
            is_shallow = True

        # 7. Upstream branch
        upstream_branch = None
        code, upstream_str, _ = self.run_cmd(["rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}"])
        if code == 0 and upstream_str.strip():
            upstream_branch = upstream_str.strip()

        # 8. Operations in progress
        operations_in_progress = self._detect_operations_in_progress(Path(repo_root))

        # 9. Remotes
        remotes = self._inspect_remotes()

        # 10. Signing and identity
        code, gpg_sign, _ = self.run_cmd(["config", "--bool", "commit.gpgsign"])
        commit_signing_enabled = gpg_sign.strip().lower() == "true" if code == 0 else False

        code, user_name, _ = self.run_cmd(["config", "user.name"])
        u_name = user_name.strip() if code == 0 and user_name.strip() else None

        code, user_email, _ = self.run_cmd(["config", "user.email"])
        u_email = user_email.strip() if code == 0 and user_email.strip() else None

        return RepositoryState(
            is_git_repository=True,
            git_version=git_version,
            repo_root=repo_root,
            current_branch=branch,
            head_commit=head_commit,
            is_detached_head=is_detached,
            is_shallow=is_shallow,
            upstream_branch=upstream_branch,
            operations_in_progress=operations_in_progress,
            remotes=remotes,
            commit_signing_enabled=commit_signing_enabled,
            user_name=u_name,
            user_email=u_email,
        )

    def _detect_operations_in_progress(self, repo_root: Path) -> List[str]:
        """Detect any Git operations in progress (merge, rebase, cherry-pick, revert)."""
        ops: List[str] = []
        git_dir = repo_root / ".git"

        # If .git is a file (e.g. worktree or submodule), read gitdir
        if git_dir.is_file():
            try:
                content = git_dir.read_text(encoding="utf-8").strip()
                if content.startswith("gitdir:"):
                    git_dir = Path(content.split(":", 1)[1].strip())
                    if not git_dir.is_absolute():
                        git_dir = repo_root / git_dir
            except Exception:
                pass

        if not git_dir.is_dir():
            return ops

        if (git_dir / "MERGE_HEAD").exists():
            ops.append("MERGE")
        if (git_dir / "rebase-merge").exists() or (git_dir / "rebase-apply").exists():
            ops.append("REBASE")
        if (git_dir / "CHERRY_PICK_HEAD").exists():
            ops.append("CHERRY_PICK")
        if (git_dir / "REVERT_HEAD").exists():
            ops.append("REVERT")

        return ops

    def _inspect_remotes(self) -> List[RemoteInfo]:
        """List configured remotes with sanitized URLs."""
        code, out, _ = self.run_cmd(["remote", "-v"])
        if code != 0 or not out:
            return []

        remotes_dict: dict[str, dict[str, str]] = {}
        redacted_flags: dict[str, bool] = {}

        for line in out.splitlines():
            line = line.strip()
            if not line:
                continue
            parts = line.split()
            if len(parts) >= 2:
                name = parts[0]
                raw_url = parts[1]
                kind = parts[2].strip("()") if len(parts) >= 3 else "fetch"

                sanitized, was_redacted = redact_url(raw_url)
                if name not in remotes_dict:
                    remotes_dict[name] = {"fetch": "", "push": ""}
                    redacted_flags[name] = False

                if kind == "fetch":
                    remotes_dict[name]["fetch"] = sanitized
                elif kind == "push":
                    remotes_dict[name]["push"] = sanitized

                if was_redacted:
                    redacted_flags[name] = True

        result: List[RemoteInfo] = []
        for name, urls in remotes_dict.items():
            result.append(
                RemoteInfo(
                    name=name,
                    fetch_url=urls.get("fetch") or urls.get("push", ""),
                    push_url=urls.get("push") or urls.get("fetch", ""),
                    is_credential_redacted=redacted_flags.get(name, False),
                )
            )
        return result
