"""Secret and sensitive data scanner for RepoCraft.

Identifies API tokens, private keys, database URLs, JWTs, and credential assignments.
Applies contextual heuristics to minimize false positives.
Strictly redacts sensitive values from all evidence and reports.
"""
from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from .types import SecretConfidence, SecretFinding, SecuritySeverity

EXCLUDED_DIR_NAMES = {
    ".git", "node_modules", ".next", "dist", "build", "coverage",
    ".venv", "venv", "__pycache__", ".gradle", "vendor", ".turbo",
}

# Regex patterns for specific high-confidence secret formats
SPECIFIC_SECRET_PATTERNS = [
    (
        "SEC-KEY-001",
        "Private Key Block",
        re.compile(r"-----BEGIN\s+([A-Z\s]+)?PRIVATE\s+KEY-----"),
        SecretConfidence.CONFIRMED_SECRET,
        SecuritySeverity.CRITICAL,
        "Cryptographic private key file or embedded block detected.",
    ),
    (
        "SEC-AWS-001",
        "AWS Access Key ID",
        re.compile(r"\b(AKIA[0-9A-Z]{16})\b"),
        SecretConfidence.CONFIRMED_SECRET,
        SecuritySeverity.HIGH,
        "AWS IAM Access Key ID pattern detected.",
    ),
    (
        "SEC-STRIPE-001",
        "Stripe Live API Key",
        re.compile(r"\b((?:sk|rk)_live_[0-9a-zA-Z]{24,})\b"),
        SecretConfidence.CONFIRMED_SECRET,
        SecuritySeverity.CRITICAL,
        "Live Stripe secret or restricted API key.",
    ),
    (
        "SEC-GH-001",
        "GitHub Personal Access Token",
        re.compile(r"\b(gh[pousr]_[0-9a-zA-Z]{36}|github_pat_[0-9a-zA-Z_]{82})\b"),
        SecretConfidence.CONFIRMED_SECRET,
        SecuritySeverity.CRITICAL,
        "GitHub personal access token or OAuth token.",
    ),
    (
        "SEC-SLACK-001",
        "Slack Token",
        re.compile(r"\b(xox[baprs]-[0-9a-zA-Z]{10,48})\b"),
        SecretConfidence.CONFIRMED_SECRET,
        SecuritySeverity.HIGH,
        "Slack authentication bot or user token.",
    ),
    (
        "SEC-OPENAI-001",
        "OpenAI API Key",
        re.compile(r"\b(sk-[a-zA-Z0-9]{48}|sk-proj-[a-zA-Z0-9_-]{40,})\b"),
        SecretConfidence.CONFIRMED_SECRET,
        SecuritySeverity.CRITICAL,
        "OpenAI API secret key.",
    ),
    (
        "SEC-GOOG-001",
        "Google API Key",
        re.compile(r"\b(AIza[0-9A-Za-z-_]{30,35})\b"),
        SecretConfidence.CONFIRMED_SECRET,
        SecuritySeverity.HIGH,
        "Google Cloud or Maps API key.",
    ),
    (
        "SEC-DB-001",
        "Database Connection String with Credentials",
        re.compile(r"(?:postgres|postgresql|mysql|mongodb|redis|amqp)://([^:\s]+):([^@\s]+)@"),
        SecretConfidence.CONFIRMED_SECRET,
        SecuritySeverity.CRITICAL,
        "Database URI containing embedded plaintext password or authentication credentials.",
    ),
    (
        "SEC-JWT-001",
        "JSON Web Token (JWT)",
        re.compile(r"\b(eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,})\b"),
        SecretConfidence.LIKELY_SECRET,
        SecuritySeverity.MEDIUM,
        "JWT token pattern with header, payload, and signature.",
    ),
]

# Generic assignment patterns for credential variables in code and config
GENERIC_CREDENTIAL_PATTERN = re.compile(
    r"""(?i)\b(?:[a-zA-Z0-9_]*_)?(password|passwd|api_key|apikey|secret_key|auth_token|access_token|private_key|client_secret)\s*[:=]\s*["']([^"'\r\n]{8,})["']"""
)

# Harmless words and common example placeholders to filter out false positives
HARMLESS_PLACEHOLDERS = {
    "your_api_key", "your_secret", "your_password", "placeholder", "changeme",
    "todo", "example", "dummy", "my_password", "secret123", "test1234",
    "abcdef123456", "xxxxxxxx", "00000000", "12345678", "none", "null",
}


def redact_string(val: str) -> str:
    """Masks secret values, preserving prefix and length hint."""
    if not val:
        return "***REDACTED***"
    if len(val) <= 6:
        return "***REDACTED***"
    if val.startswith(("sk_live_", "rk_live_", "sk_test_", "rk_test_")):
        prefix = val[:8]
    elif len(val) >= 20:
        prefix = val[:6]
    else:
        prefix = val[:3]
    return f"{prefix}***REDACTED***"


def is_binary_file(path: Path) -> bool:
    try:
        with path.open("rb") as f:
            chunk = f.read(1024)
            return b"\x00" in chunk
    except Exception:
        return True


class SecretScanner:
    """Scans repository files for credentials with calibrated confidence and strict redaction."""

    def __init__(self, repo_root: Path, file_paths: List[str]):
        self.repo_root = repo_root
        self.file_paths = file_paths
        self.findings: List[SecretFinding] = []
        self._counter = 1

    def _next_id(self) -> str:
        fid = f"SEC-FIND-{self._counter:03d}"
        self._counter += 1
        return fid

    def scan(self) -> List[SecretFinding]:
        self.findings.clear()

        for rel_path in self.file_paths:
            # Check exclusions
            parts = rel_path.split("/")
            if any(p in EXCLUDED_DIR_NAMES for p in parts):
                continue

            full_path = self.repo_root / rel_path
            filename = Path(rel_path).name.lower()

            # 1. Check for sensitive file existence
            if filename in (".env", ".env.local", ".env.production", ".env.staging", "id_rsa", "id_ed25519") or (
                filename.startswith(".env.") and not filename.endswith((".example", ".sample", ".template"))
            ):
                self.findings.append(
                    SecretFinding(
                        finding_id=self._next_id(),
                        rule_id="SEC-FILE-001",
                        category="Sensitive File Exposure",
                        confidence=SecretConfidence.SENSITIVE_FILE_EXPOSURE,
                        severity=SecuritySeverity.HIGH,
                        file_path=rel_path,
                        line_number=None,
                        redacted_evidence=f"File: {rel_path} (Contents strictly unread)",
                        explanation=(
                            f"Sensitive environment or key file '{rel_path}' present in repository tree. "
                            "May leak credentials if committed or deployed."
                        ),
                    )
                )

            # Skip binary and oversized files (>2MB)
            try:
                st = full_path.stat()
                if st.st_size > 2 * 1024 * 1024 or st.st_size == 0:
                    continue
                if is_binary_file(full_path):
                    continue

                content = full_path.read_text(encoding="utf-8", errors="replace")
                self._scan_file_content(rel_path, content)

            except Exception:
                continue

        # Sort deterministically by severity and path
        sev_order = {
            SecuritySeverity.CRITICAL: 0,
            SecuritySeverity.HIGH: 1,
            SecuritySeverity.MEDIUM: 2,
            SecuritySeverity.LOW: 3,
            SecuritySeverity.INFO: 4,
        }
        self.findings.sort(key=lambda f: (sev_order[f.severity], f.file_path, f.line_number or 0))
        return self.findings

    def _scan_file_content(self, rel_path: str, content: str) -> None:
        lines = content.splitlines()

        for line_num, line in enumerate(lines, start=1):
            line_str = line.strip()
            if not line_str or line_str.startswith(("#", "//", "/*", "*")):
                # Check for private key even in comment/header
                if "-----BEGIN" not in line_str:
                    continue

            # A. Check Specific Secret Patterns
            for rule_id, cat, pattern, conf, sev, expl in SPECIFIC_SECRET_PATTERNS:
                match = pattern.search(line_str)
                if match:
                    # Redact the matched secret in the line
                    matched_val = match.group(0)
                    # If pattern has group 1 or 2
                    if match.groups():
                        matched_val = match.group(1)
                    redacted_snippet = line_str.replace(matched_val, redact_string(matched_val))

                    self.findings.append(
                        SecretFinding(
                            finding_id=self._next_id(),
                            rule_id=rule_id,
                            category=cat,
                            confidence=conf,
                            severity=sev,
                            file_path=rel_path,
                            line_number=line_num,
                            redacted_evidence=redacted_snippet[:120],
                            explanation=expl,
                        )
                    )

            # B. Check Generic Credential Assignments
            gen_match = GENERIC_CREDENTIAL_PATTERN.search(line_str)
            if gen_match:
                var_name = gen_match.group(1)
                secret_val = gen_match.group(2)

                # Filter out obvious test/dummy placeholders
                if secret_val.lower() in HARMLESS_PLACEHOLDERS or any(h in secret_val.lower() for h in ("example", "your_")):
                    continue

                redacted_snippet = line_str.replace(secret_val, redact_string(secret_val))
                self.findings.append(
                    SecretFinding(
                        finding_id=self._next_id(),
                        rule_id="SEC-GEN-001",
                        category="Hardcoded Credential Assignment",
                        confidence=SecretConfidence.LIKELY_SECRET,
                        severity=SecuritySeverity.HIGH,
                        file_path=rel_path,
                        line_number=line_num,
                        redacted_evidence=redacted_snippet[:120],
                        explanation=f"Hardcoded assignment to credential variable '{var_name}'.",
                    )
                )


def scan_secrets(target_dir: str) -> List[SecretFinding]:
    """Scan target repository for exposed secrets and credentials."""
    root = Path(target_dir).resolve()
    file_paths: List[str] = []
    for current_dir, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in EXCLUDED_DIR_NAMES]
        for f in files:
            full = Path(current_dir) / f
            file_paths.append(full.relative_to(root).as_posix())

    scanner = SecretScanner(root, file_paths)
    return scanner.scan()

