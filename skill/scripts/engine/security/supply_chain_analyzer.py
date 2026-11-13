"""Module E — Supply Chain & Repository Integrity Auditor for RepoCraft Phase 3.

Audits CI/CD and repository files for supply chain vulnerabilities:
- GitHub Actions unpinned action references (using tags/branches instead of commit SHAs)
- Overly broad workflow permissions (write-all, missing permissions restriction)
- Dangerous pull_request_target triggers checking out untrusted PR branches
- Direct interpolation of untrusted github.event context into run scripts (script injection)
- Printing secrets to workflow run logs (echo ${{ secrets.* }})
- Suspicious compiled binaries committed to repository tree (.exe, .dll, .so, etc.)
"""
from __future__ import annotations

import os
import re
from pathlib import Path
from typing import List

from .types import SecuritySeverity, SupplyChainFinding

SUSPICIOUS_EXTENSIONS = {
    ".exe": "Windows executable",
    ".dll": "Windows dynamic link library",
    ".so": "Linux shared object library",
    ".dylib": "macOS dynamic library",
    ".bin": "Binary executable blob",
}

IGNORE_DIRS = {
    ".git",
    "node_modules",
    "venv",
    ".venv",
    "build",
    "dist",
    "target",
    "bin",
    "obj",
}


def audit_supply_chain(target_dir: str) -> List[SupplyChainFinding]:
    """Audit repository for supply-chain risks in workflows and file assets."""
    findings: List[SupplyChainFinding] = []
    root = Path(target_dir).resolve()
    idx = 1

    # 1. Audit GitHub Actions workflows
    workflows_dir = root / ".github" / "workflows"
    if workflows_dir.is_dir():
        for wf_file in sorted(workflows_dir.glob("*.y*ml")):
            wf_rel = wf_file.relative_to(root).as_posix()
            try:
                content = wf_file.read_text(encoding="utf-8", errors="replace")
                lines = content.splitlines()
            except Exception:
                continue

            # Check for pull_request_target
            has_pr_target = False
            has_untrusted_checkout = False
            has_permissions_block = False
            has_write_all = False

            for line_idx, line in enumerate(lines, start=1):
                stripped = line.strip()

                if "pull_request_target" in stripped:
                    has_pr_target = True

                if "permissions: write-all" in stripped:
                    has_write_all = True
                    findings.append(
                        SupplyChainFinding(
                            finding_id=f"SC-{idx:03d}",
                            category="WORKFLOW_PERMISSIONS",
                            severity=SecuritySeverity.HIGH,
                            workflow_path=wf_rel,
                            line_number=line_idx,
                            issue="Workflow grants write-all permissions",
                            explanation="The workflow declares 'permissions: write-all', granting write access to all GitHub repository scopes including code, issues, and pull requests.",
                            recommendation="Adopt the principle of least privilege; grant only specific permissions (e.g. contents: read, pull-requests: write).",
                        )
                    )
                    idx += 1

                if re.match(r"^permissions:\s*", stripped):
                    has_permissions_block = True

                # Check action pinning
                uses_match = re.search(r"uses:\s*([^#\s]+)", stripped)
                if uses_match:
                    action_ref = uses_match.group(1).strip()
                    # Skip local action references like ./ or docker://
                    if not action_ref.startswith(("./", "docker://")):
                        if "@" in action_ref:
                            act_name, version = action_ref.split("@", 1)
                            # Check if version is a full 40-hex-char SHA
                            if not re.fullmatch(r"[0-9a-fA-F]{40}", version):
                                findings.append(
                                    SupplyChainFinding(
                                        finding_id=f"SC-{idx:03d}",
                                        category="MUTABLE_ACTION_REFERENCE",
                                        severity=SecuritySeverity.LOW,
                                        workflow_path=wf_rel,
                                        line_number=line_idx,
                                        issue=f"Action '{act_name}' pinned to mutable reference '@{version}'",
                                        explanation=f"Actions pinned to mutable tags or branches can be modified or hijacked upstream without notice.",
                                        recommendation=f"Pin action '{act_name}' to an immutable commit SHA (e.g. {act_name}@<commit-sha> # {version}).",
                                    )
                                )
                                idx += 1

                # Check script injection via ${{ github.event.* }} in run steps
                if "run:" in stripped or "run: |" in stripped:
                    # Look ahead a few lines for context expressions
                    for look_idx in range(line_idx - 1, min(line_idx + 10, len(lines))):
                        sub_line = lines[look_idx]
                        if re.search(
                            r"\$\{\{\s*github\.event\.(?:issue\.title|issue\.body|pull_request\.title|pull_request\.body|comment\.body|head_commit\.message)\s*\}\}",
                            sub_line,
                        ):
                            findings.append(
                                SupplyChainFinding(
                                    finding_id=f"SC-{idx:03d}",
                                    category="WORKFLOW_SCRIPT_INJECTION",
                                    severity=SecuritySeverity.CRITICAL,
                                    workflow_path=wf_rel,
                                    line_number=look_idx + 1,
                                    issue="Untrusted GitHub event context interpolated into shell script",
                                    explanation="Direct inline expansion of user-controllable input (PR/issue titles or bodies) into a shell script allows command injection.",
                                    recommendation="Pass GitHub event values via environment variables rather than direct script interpolation.",
                                )
                            )
                            idx += 1
                            break

                # Check secret exposure in logs: echo ${{ secrets.* }}
                if re.search(r"echo\s+.*(?:\$\{\{\s*secrets\.\w+\s*\}\})", stripped, re.IGNORECASE):
                    findings.append(
                        SupplyChainFinding(
                            finding_id=f"SC-{idx:03d}",
                            category="SECRET_LOG_EXPOSURE",
                            severity=SecuritySeverity.HIGH,
                            workflow_path=wf_rel,
                            line_number=line_idx,
                            issue="Secret interpolated directly into echo command",
                            explanation="Echoing secrets may result in their accidental disclosure in workflow execution logs.",
                            recommendation="Avoid printing secrets to stdout; use masked environment variables or dedicated action inputs.",
                        )
                    )
                    idx += 1

                # Check untrusted checkout in PR target
                if has_pr_target and re.search(r"ref:\s*\$\{\{\s*github\.event\.pull_request\.head\.sha\s*\}\}", stripped):
                    has_untrusted_checkout = True

            if has_pr_target and has_untrusted_checkout:
                findings.append(
                    SupplyChainFinding(
                        finding_id=f"SC-{idx:03d}",
                        category="RISKY_PR_TARGET",
                        severity=SecuritySeverity.HIGH,
                        workflow_path=wf_rel,
                        line_number=None,
                        issue="pull_request_target checks out untrusted pull request HEAD",
                        explanation="pull_request_target triggers run with read/write repo access and secrets access. Checking out untrusted PR head allows arbitrary code execution in privileged context.",
                        recommendation="Do not check out untrusted pull request code in pull_request_target workflows. Use pull_request trigger instead.",
                    )
                )
                idx += 1

    # 2. Audit suspicious committed binary files in source tree
    for current_dir, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS and not d.startswith(".")]

        for filename in files:
            file_path = Path(current_dir) / filename
            ext = file_path.suffix.lower()
            if ext in SUSPICIOUS_EXTENSIONS:
                rel = file_path.relative_to(root).as_posix()
                findings.append(
                    SupplyChainFinding(
                        finding_id=f"SC-{idx:03d}",
                        category="COMMITTED_BINARY",
                        severity=SecuritySeverity.MEDIUM,
                        workflow_path=rel,
                        line_number=None,
                        issue=f"Committed executable/binary file detected: {filename}",
                        explanation=f"Repository contains a compiled binary ({SUSPICIOUS_EXTENSIONS[ext]}). Pre-compiled binaries bypass code review and present supply chain tamper risks.",
                        recommendation="Build binaries from source in CI/CD rather than committing compiled executables to the repository.",
                    )
                )
                idx += 1

    return findings

