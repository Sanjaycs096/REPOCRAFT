"""Module D — Configuration & Deployment Security Auditor for RepoCraft Phase 3.

Audits repository configuration and deployment files for security risks:
- Missing or insufficient .gitignore (unignored .env, .pem, .key, credentials)
- Missing or insufficient .dockerignore
- Insecure Dockerfile configurations (root user, :latest tags, curl|sh, embedded secrets, EXPOSE 22)
- Dangerous development/debug flags in configuration files (DEBUG=True)
"""
from __future__ import annotations

import os
import re
from pathlib import Path
from typing import List, Optional

from .types import ConfigurationFinding, SecuritySeverity

CRITICAL_GITIGNORE_PATTERNS = [
    (".env", "Environment file containing potential secrets"),
    ("*.key", "Private key files"),
    ("*.pem", "Certificate and private key files"),
    ("credentials.json", "Credential files"),
    ("id_rsa", "SSH private keys"),
]

RECOMMENDED_GITIGNORE_PATTERNS = [
    (".venv", "Virtual environment directory"),
    ("node_modules", "Node.js dependencies directory"),
    ("__pycache__", "Python bytecode cache"),
]


def _read_lines(file_path: Path) -> List[str]:
    try:
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            return f.readlines()
    except Exception:
        return []


def audit_configuration(target_dir: str) -> List[ConfigurationFinding]:
    """Audit configuration files and deployment setups for security issues."""
    findings: List[ConfigurationFinding] = []
    root = Path(target_dir).resolve()
    idx = 1

    # 1. Audit .gitignore
    gitignore_path = root / ".gitignore"
    if not gitignore_path.exists():
        findings.append(
            ConfigurationFinding(
                finding_id=f"CFG-{idx:03d}",
                category="GITIGNORE",
                severity=SecuritySeverity.HIGH,
                file_path=".gitignore",
                line_number=None,
                issue="Missing .gitignore file",
                explanation="Repository lacks a .gitignore file, increasing the risk of accidentally committing sensitive credentials, build artifacts, or local configuration.",
                recommended_action="Create a .gitignore file covering environment variables, private keys, dependencies, and build artifacts.",
                requires_approval=True,
            )
        )
        idx += 1
    else:
        gitignore_content = gitignore_path.read_text(encoding="utf-8", errors="replace")
        gitignore_lines = [line.strip() for line in gitignore_content.splitlines()]

        for pattern, desc in CRITICAL_GITIGNORE_PATTERNS:
            # Check if pattern or general prefix is in .gitignore
            matched = any(
                p == pattern
                or (pattern.startswith("*.") and p.endswith(pattern[1:]))
                or (pattern == ".env" and (p == ".env" or p == ".env*" or p == "*.env"))
                for p in gitignore_lines
                if p and not p.startswith("#")
            )
            if not matched:
                findings.append(
                    ConfigurationFinding(
                        finding_id=f"CFG-{idx:03d}",
                        category="GITIGNORE",
                        severity=SecuritySeverity.HIGH if pattern in (".env", "*.key", "*.pem") else SecuritySeverity.LOW,
                        file_path=".gitignore",
                        line_number=None,
                        issue=f".gitignore missing rule for '{pattern}'",
                        explanation=f".gitignore does not explicitly exclude '{pattern}' ({desc}), posing an exposure hazard if created in the workspace.",
                        recommended_action=f"Add '{pattern}' to .gitignore.",
                        requires_approval=True,
                    )
                )
                idx += 1

    # 2. Audit Dockerfiles and .dockerignore
    dockerfiles: List[Path] = []
    for current_dir, _, files in os.walk(root):
        if any(ignored in current_dir for ignored in [".git", "node_modules", "venv", ".venv"]):
            continue
        for file in files:
            if file == "Dockerfile" or file.startswith("Dockerfile.") or file.endswith(".dockerfile"):
                dockerfiles.append(Path(current_dir) / file)

    dockerignore_path = root / ".dockerignore"
    if dockerfiles and not dockerignore_path.exists():
        findings.append(
            ConfigurationFinding(
                finding_id=f"CFG-{idx:03d}",
                category="DOCKERIGNORE",
                severity=SecuritySeverity.MEDIUM,
                file_path=".dockerignore",
                line_number=None,
                issue="Missing .dockerignore in project using Docker",
                explanation="Dockerfile is present but .dockerignore is missing. The Docker build context may inadvertently include .git history, secrets, and large local files.",
                recommended_action="Create .dockerignore excluding .git, .env, secrets, and development caches.",
                requires_approval=True,
            )
        )
        idx += 1
    elif dockerfiles and dockerignore_path.exists():
        dockerignore_lines = [
            line.strip() for line in _read_lines(dockerignore_path) if line.strip() and not line.strip().startswith("#")
        ]
        docker_needs = [(".git", "Git metadata directory"), (".env", "Environment secret file")]
        for d_pat, d_desc in docker_needs:
            if not any(d_pat in l for l in dockerignore_lines):
                findings.append(
                    ConfigurationFinding(
                        finding_id=f"CFG-{idx:03d}",
                        category="DOCKERIGNORE",
                        severity=SecuritySeverity.MEDIUM,
                        file_path=".dockerignore",
                        line_number=None,
                        issue=f".dockerignore missing rule for '{d_pat}'",
                        explanation=f".dockerignore does not exclude '{d_pat}' ({d_desc}), which may be copied into images during build.",
                        recommended_action=f"Add '{d_pat}' to .dockerignore.",
                        requires_approval=True,
                    )
                )
                idx += 1

    # Audit each Dockerfile
    for df in dockerfiles:
        df_rel = df.relative_to(root).as_posix()
        df_lines = _read_lines(df)
        has_user_instruction = False

        for line_idx, line in enumerate(df_lines, start=1):
            stripped = line.strip()
            if stripped.startswith("#"):
                continue

            # Check USER instruction
            if re.match(r"^USER\s+", stripped, re.IGNORECASE):
                has_user_instruction = True

            # Check unpinned / :latest base image
            from_match = re.match(r"^FROM\s+([^\s]+)", stripped, re.IGNORECASE)
            if from_match:
                img = from_match.group(1).lower()
                if img != "scratch" and (":" not in img or img.endswith(":latest")):
                    findings.append(
                        ConfigurationFinding(
                            finding_id=f"CFG-{idx:03d}",
                            category="DOCKERFILE",
                            severity=SecuritySeverity.LOW,
                            file_path=df_rel,
                            line_number=line_idx,
                            issue=f"Dockerfile uses unpinned or :latest base image '{img}'",
                            explanation="Base images using ':latest' or lacking an explicit version tag can lead to unpredictable builds and supply chain breakage.",
                            recommended_action=f"Pin '{img}' to a specific version tag or digest SHA.",
                            requires_approval=True,
                        )
                    )
                    idx += 1

            # Check COPY/ADD of sensitive files
            if re.search(r"\b(?:COPY|ADD)\s+.*(?:\.env|\.pem|\.key|id_rsa)", stripped, re.IGNORECASE):
                findings.append(
                    ConfigurationFinding(
                        finding_id=f"CFG-{idx:03d}",
                        category="DOCKERFILE",
                        severity=SecuritySeverity.HIGH,
                        file_path=df_rel,
                        line_number=line_idx,
                        issue="Dockerfile copies sensitive files into container image",
                        explanation="Copying secrets directly into container image embeds them into image layers, exposing them to anyone with pull access.",
                        recommended_action="Use BuildKit secrets mount (--mount=type=secret) or runtime environment injection.",
                        requires_approval=True,
                    )
                )
                idx += 1

            # Check exposed SSH port 22
            if re.match(r"^EXPOSE\s+.*(?:\b22\b)", stripped, re.IGNORECASE):
                findings.append(
                    ConfigurationFinding(
                        finding_id=f"CFG-{idx:03d}",
                        category="DOCKERFILE",
                        severity=SecuritySeverity.MEDIUM,
                        file_path=df_rel,
                        line_number=line_idx,
                        issue="Dockerfile exposes SSH port 22",
                        explanation="Running an SSH server inside a container is an anti-pattern that expands attack surface.",
                        recommended_action="Remove SSH daemon from container; use docker exec or container orchestration tools for debugging.",
                        requires_approval=True,
                    )
                )
                idx += 1

            # Check curl/wget pipe to sh/bash
            if re.search(r"(?:curl|wget)[^|]*\|\s*(?:sh|bash)", stripped, re.IGNORECASE):
                findings.append(
                    ConfigurationFinding(
                        finding_id=f"CFG-{idx:03d}",
                        category="DOCKERFILE",
                        severity=SecuritySeverity.MEDIUM,
                        file_path=df_rel,
                        line_number=line_idx,
                        issue="Dockerfile pipes remote download directly into shell",
                        explanation="Piping unverified curl/wget output directly into sh/bash bypasses integrity verification and opens supply chain risks.",
                        recommended_action="Download the installer, verify its checksum, and run it as separate steps.",
                        requires_approval=True,
                    )
                )
                idx += 1

        # Check if USER instruction was never specified
        if not has_user_instruction and len(df_lines) > 3:
            findings.append(
                ConfigurationFinding(
                    finding_id=f"CFG-{idx:03d}",
                    category="DOCKERFILE",
                    severity=SecuritySeverity.LOW,
                    file_path=df_rel,
                    line_number=None,
                    issue="Dockerfile does not specify a non-root USER",
                    explanation="Containers running as root increase potential damage in the event of a container breakout vulnerability.",
                    recommended_action="Add a non-root USER instruction before the ENTRYPOINT or CMD.",
                    requires_approval=True,
                )
            )
            idx += 1

    # 3. Audit Debug / Development flags in configuration files
    config_candidates = [
        "settings.py",
        "config.py",
        "app.py",
        "application.yml",
        "application.properties",
        ".env.example",
    ]

    for candidate in config_candidates:
        c_path = root / candidate
        if not c_path.exists():
            continue
        rel = candidate
        lines = _read_lines(c_path)
        for line_idx, line in enumerate(lines, start=1):
            if re.search(r"^\s*DEBUG\s*=\s*True\b", line, re.IGNORECASE):
                findings.append(
                    ConfigurationFinding(
                        finding_id=f"CFG-{idx:03d}",
                        category="CONFIG_FLAG",
                        severity=SecuritySeverity.MEDIUM,
                        file_path=rel,
                        line_number=line_idx,
                        issue=f"DEBUG mode enabled in {candidate}",
                        explanation="Running applications with DEBUG=True in production can expose sensitive stack traces, debug consoles, and secret configuration.",
                        recommended_action="Ensure DEBUG is disabled or read dynamically from environment variables defaulting to False in production.",
                        requires_approval=True,
                    )
                )
                idx += 1

    return findings
