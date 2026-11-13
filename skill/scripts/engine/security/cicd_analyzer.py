"""Module I — CI/CD Workflow Analyzer for RepoCraft Phase 3.

Audits CI/CD configurations across multiple providers:
- GitHub Actions (.github/workflows/)
- GitLab CI (.gitlab-ci.yml)
- CircleCI (.circleci/config.yml)
- Azure Pipelines (azure-pipelines.yml)
- Bitbucket Pipelines (bitbucket-pipelines.yml)
"""
from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from .types import CicdWorkflowAudit

CI_FILES = [
    (".gitlab-ci.yml", "GitLab CI"),
    (".circleci/config.yml", "CircleCI"),
    ("azure-pipelines.yml", "Azure Pipelines"),
    ("bitbucket-pipelines.yml", "Bitbucket Pipelines"),
    (".travis.yml", "Travis CI"),
]


def audit_github_workflow(wf_path: Path, root: Path) -> CicdWorkflowAudit:
    """Audit a single GitHub Actions workflow file."""
    rel_path = wf_path.relative_to(root).as_posix()
    content = wf_path.read_text(encoding="utf-8", errors="replace")
    lines = content.splitlines()

    triggers: List[str] = []
    issues: List[str] = []
    jobs_count = 0
    has_test_step = False
    has_build_step = False
    has_lint_step = False
    has_unpinned_actions = False
    has_broad_permissions = False
    has_risky_pr_triggers = False

    # Extract triggers
    in_on_block = False
    on_indent = 0

    for idx, line in enumerate(lines):
        stripped = line.strip()

        # Check 'on:' triggers
        if re.match(r"^on:\s*$", line):
            in_on_block = True
            on_indent = len(line) - len(line.lstrip())
            continue
        elif re.match(r"^on:\s*\[(.*)\]", line):
            trig_raw = re.match(r"^on:\s*\[(.*)\]", line).group(1)
            triggers.extend([t.strip().strip("'\"") for t in trig_raw.split(",") if t.strip()])
        elif re.match(r"^on:\s*(\w+)", line):
            triggers.append(re.match(r"^on:\s*(\w+)", line).group(1))

        if in_on_block:
            current_indent = len(line) - len(line.lstrip())
            if current_indent <= on_indent and stripped and not stripped.startswith("#"):
                in_on_block = False
            else:
                m = re.match(r"^\s*([a-zA-Z_]+)\s*:", line)
                if m:
                    triggers.append(m.group(1))

        # Check jobs count
        if re.match(r"^\s{2}[a-zA-Z0-9_-]+:\s*$", line) and "jobs:" in lines[max(0, idx - 10) : idx]:
            jobs_count += 1

        # Check step patterns
        line_lower = stripped.lower()
        if any(t in line_lower for t in ["pytest", "npm test", "npm run test", "cargo test", "go test", "mvn test", "test:"]):
            has_test_step = True
        if any(b in line_lower for b in ["npm run build", "cargo build", "mvn package", "gradle build", "go build", "build:"]):
            has_build_step = True
        if any(l in line_lower for l in ["eslint", "flake8", "ruff", "lint", "golangci-lint", "clippy"]):
            has_lint_step = True

        # Check unpinned actions
        uses_m = re.search(r"uses:\s*([^#\s]+)", stripped)
        if uses_m:
            ref = uses_m.group(1).strip()
            if not ref.startswith(("./", "docker://")) and "@" in ref:
                _, ver = ref.split("@", 1)
                if not re.fullmatch(r"[0-9a-fA-F]{40}", ver):
                    has_unpinned_actions = True

        # Check permissions
        if "permissions: write-all" in stripped:
            has_broad_permissions = True

        # Check PR target
        if "pull_request_target" in stripped:
            has_risky_pr_triggers = True

    if has_broad_permissions:
        issues.append("Declares broad 'permissions: write-all' authorization.")
    if has_unpinned_actions:
        issues.append("Uses mutable action references without SHA-1 pinning.")
    if has_risky_pr_triggers:
        issues.append("Uses 'pull_request_target' trigger; ensure PR code is not executed in privileged context.")
    if not has_test_step and not has_build_step:
        issues.append("Workflow has neither automated test nor build steps.")

    return CicdWorkflowAudit(
        workflow_file=rel_path,
        triggers=list(set(triggers)),
        jobs_count=max(jobs_count, 1 if "jobs:" in content else 0),
        has_test_step=has_test_step,
        has_build_step=has_build_step,
        has_lint_step=has_lint_step,
        has_unpinned_actions=has_unpinned_actions,
        has_broad_permissions=has_broad_permissions,
        has_risky_pr_triggers=has_risky_pr_triggers,
        issues=issues,
    )


def audit_cicd(target_dir: str) -> List[CicdWorkflowAudit]:
    """Audit all CI/CD pipelines in the repository."""
    root = Path(target_dir).resolve()
    audits: List[CicdWorkflowAudit] = []

    # 1. GitHub Actions
    gh_dir = root / ".github" / "workflows"
    if gh_dir.is_dir():
        for wf_file in sorted(gh_dir.glob("*.y*ml")):
            audits.append(audit_github_workflow(wf_file, root))

    # 2. Other CI platforms
    for ci_file, platform_name in CI_FILES:
        path = root / ci_file
        if path.exists():
            rel_path = path.relative_to(root).as_posix()
            content = path.read_text(encoding="utf-8", errors="replace").lower()

            has_test = any(t in content for t in ["test", "pytest", "npm test", "cargo test"])
            has_build = any(b in content for b in ["build", "compile", "package"])
            has_lint = any(l in content for l in ["lint", "eslint", "flake8"])

            audits.append(
                CicdWorkflowAudit(
                    workflow_file=rel_path,
                    triggers=["push", "merge_request"] if "gitlab" in platform_name.lower() else ["push"],
                    jobs_count=1,
                    has_test_step=has_test,
                    has_build_step=has_build,
                    has_lint_step=has_lint,
                    has_unpinned_actions=False,
                    has_broad_permissions=False,
                    has_risky_pr_triggers=False,
                    issues=[] if has_test else ["Pipeline does not contain explicit test execution steps."],
                )
            )

    return audits

