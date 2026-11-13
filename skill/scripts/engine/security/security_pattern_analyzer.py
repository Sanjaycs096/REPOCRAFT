"""Module C — Application Security Pattern Analyzer for RepoCraft Phase 3.

Scans codebase for common dangerous coding patterns including:
- SQL injection risks (concatenation / format strings in queries)
- Command injection (shell=True, os.system, child_process.exec)
- Dynamic code evaluation (eval, exec)
- Unsafe deserialization (pickle.loads, yaml.load without SafeLoader)
- Insecure CORS configurations (wildcard origins)
- Insecure cookie / session flags (secure=False, httpOnly=False)
- Weak cryptographic algorithms (MD5, SHA1 for security, Math.random)
- Frontend DOM injection (dangerouslySetInnerHTML, innerHTML)
"""
from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .secret_scanner import is_binary_file, redact_string
from .types import SecurityPatternFinding, SecuritySeverity

IGNORE_DIRS = {
    ".git",
    "node_modules",
    "vendor",
    "venv",
    ".venv",
    "env",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    "dist",
    "build",
    "coverage",
    ".next",
    ".nuxt",
}

MAX_FILE_SIZE = 1_000_000  # 1MB limit for pattern scanning


# Rule specifications: (rule_id, category, severity, confidence, pattern, explanation, impact, remediation)
SECURITY_RULES: List[Dict[str, Any]] = [
    {
        "rule_id": "SEC-SQL-001",
        "category": "SQL_INJECTION",
        "severity": SecuritySeverity.HIGH,
        "confidence": "HIGH",
        "pattern": re.compile(
            r"""(?:execute|cursor\.execute|db\.query|raw_query|query)\s*\(\s*(?:f["'][^"']*(?:SELECT|INSERT|UPDATE|DELETE|DROP|ALTER|WHERE)[^"']*\{|["'][^"']*(?:SELECT|INSERT|UPDATE|DELETE|DROP|ALTER|WHERE)[^"']*["']\s*%)""",
            re.IGNORECASE,
        ),
        "explanation": "SQL query dynamically formatted or formatted using string interpolation/modulo rather than parameterized queries.",
        "impact": "May allow SQL Injection attacks allowing unauthorized database access or modification.",
        "remediation": "Use parameterized queries or ORM query builder interfaces.",
    },
    {
        "rule_id": "SEC-SQL-002",
        "category": "SQL_INJECTION",
        "severity": SecuritySeverity.MEDIUM,
        "confidence": "MEDIUM",
        "pattern": re.compile(
            r"""(?:execute|db\.query)\s*\(\s*["'][^"']*(?:SELECT|INSERT|UPDATE|DELETE)[^"']*["']\s*\+""",
            re.IGNORECASE,
        ),
        "explanation": "SQL query assembled via string concatenation.",
        "impact": "Risk of SQL injection vulnerability if concatenated variable originates from user input.",
        "remediation": "Replace string concatenation with parameterized query parameters.",
    },
    {
        "rule_id": "SEC-CMD-001",
        "category": "COMMAND_INJECTION",
        "severity": SecuritySeverity.HIGH,
        "confidence": "HIGH",
        "pattern": re.compile(
            r"""subprocess\.(?:Popen|call|run|check_call|check_output)\s*\([^)]*shell\s*=\s*True""",
            re.IGNORECASE,
        ),
        "explanation": "Subprocess execution with shell=True enabled.",
        "impact": "Enables shell metacharacter injection if arguments include unescaped untrusted inputs.",
        "remediation": "Avoid shell=True. Pass command arguments as a list of strings instead.",
    },
    {
        "rule_id": "SEC-CMD-002",
        "category": "COMMAND_INJECTION",
        "severity": SecuritySeverity.HIGH,
        "confidence": "HIGH",
        "pattern": re.compile(r"""\bos\.system\s*\(""", re.IGNORECASE),
        "explanation": "Direct invocation of os.system().",
        "impact": "Executes shell commands without argument escaping, vulnerable to command injection.",
        "remediation": "Use subprocess.run with a list of arguments and shell=False.",
    },
    {
        "rule_id": "SEC-CMD-003",
        "category": "COMMAND_INJECTION",
        "severity": SecuritySeverity.HIGH,
        "confidence": "MEDIUM",
        "pattern": re.compile(
            r"""child_process\.(?:exec|execSync)\s*\([^)]*\+""",
            re.IGNORECASE,
        ),
        "explanation": "Node.js child_process.exec() with concatenated command string.",
        "impact": "May allow command injection if variables contain untrusted input.",
        "remediation": "Use child_process.execFile or spawn with argument array.",
    },
    {
        "rule_id": "SEC-EVAL-001",
        "category": "DYNAMIC_CODE_EVALUATION",
        "severity": SecuritySeverity.HIGH,
        "confidence": "HIGH",
        "pattern": re.compile(r"""\b(?:eval|exec)\s*\(""", re.IGNORECASE),
        "explanation": "Dynamic code evaluation via eval() or exec().",
        "impact": "Arbitrary code execution if untrusted input reaches the evaluation engine.",
        "remediation": "Refactor to use static data parsing (e.g. ast.literal_eval, json.loads) or dispatch tables.",
    },
    {
        "rule_id": "SEC-DESER-001",
        "category": "UNSAFE_DESERIALIZATION",
        "severity": SecuritySeverity.CRITICAL,
        "confidence": "HIGH",
        "pattern": re.compile(r"""\bpickle\.(?:loads|load)\s*\(""", re.IGNORECASE),
        "explanation": "Python pickle deserialization detected.",
        "impact": "Pickle serialization can execute arbitrary Python code during unpickling.",
        "remediation": "Use safe serialization formats like JSON, MessagePack, or Protocol Buffers.",
    },
    {
        "rule_id": "SEC-DESER-002",
        "category": "UNSAFE_DESERIALIZATION",
        "severity": SecuritySeverity.HIGH,
        "confidence": "HIGH",
        "pattern": re.compile(r"""yaml\.load\s*\([^)]*(?:Loader\s*=\s*yaml\.(?:Loader|FullLoader|UnsafeLoader)|(?!\bSafeLoader\b)[^),]*\))""", re.IGNORECASE),
        "explanation": "YAML deserialization without yaml.SafeLoader.",
        "impact": "Unsafe YAML loading can instantiate arbitrary Python objects and execute code.",
        "remediation": "Always use yaml.safe_load() or yaml.load(..., Loader=yaml.SafeLoader).",
    },
    {
        "rule_id": "SEC-CORS-001",
        "category": "INSECURE_CORS",
        "severity": SecuritySeverity.MEDIUM,
        "confidence": "HIGH",
        "pattern": re.compile(
            r"""(?:Access-Control-Allow-Origin["']?\s*[:=]\s*["']\*["']|cors\s*\(\s*\{\s*origin\s*:\s*["']\*["']|CORS_ALLOW_ALL_ORIGINS\s*=\s*True|allow_origins\s*=\s*\[\s*["']\*["']\s*\])""",
            re.IGNORECASE,
        ),
        "explanation": "Wildcard CORS origin policy allowing any origin to make cross-origin requests.",
        "impact": "Allows untrusted origins to read authenticated response data if credentials/headers are permitted.",
        "remediation": "Restrict allowed origins to explicit trusted domain names.",
    },
    {
        "rule_id": "SEC-COOKIE-001",
        "category": "INSECURE_COOKIE",
        "severity": SecuritySeverity.LOW,
        "confidence": "HIGH",
        "pattern": re.compile(
            r"""(?:(?:set_cookie|cookie)\s*\([^)]*(?:secure\s*=\s*False|httponly\s*=\s*False)|(?:secure|httpOnly)\s*:\s*false)""",
            re.IGNORECASE,
        ),
        "explanation": "Cookie configured with secure=False or httpOnly=False.",
        "impact": "Cookies may be leaked over unencrypted HTTP connections or accessed via client-side scripts.",
        "remediation": "Ensure cookies use secure=True, httpOnly=True, and appropriate SameSite policy.",
    },
    {
        "rule_id": "SEC-CRYPTO-001",
        "category": "WEAK_CRYPTOGRAPHY",
        "severity": SecuritySeverity.MEDIUM,
        "confidence": "HIGH",
        "pattern": re.compile(
            r"""(?:hashlib\.(?:md5|sha1)\s*\(|createHash\s*\(\s*["'](?:md5|sha1)["']\))""",
            re.IGNORECASE,
        ),
        "explanation": "Use of broken/weak cryptographic hash algorithm (MD5 or SHA1).",
        "impact": "Collision attacks make MD5 and SHA1 unsuitable for password hashing, digital signatures, or integrity checks.",
        "remediation": "Use SHA-256/SHA-512 for checksums, or bcrypt/argon2 for password hashing.",
    },
    {
        "rule_id": "SEC-DOM-001",
        "category": "FRONTEND_DOM_INJECTION",
        "severity": SecuritySeverity.HIGH,
        "confidence": "HIGH",
        "pattern": re.compile(
            r"""(?:dangerouslySetInnerHTML\s*=|innerHTML\s*=|v-html\s*=|document\.write\s*\()""",
            re.IGNORECASE,
        ),
        "explanation": "Direct insertion of unescaped HTML content into the DOM.",
        "impact": "Cross-Site Scripting (XSS) if untrusted input is inserted without sanitization.",
        "remediation": "Use safe DOM text manipulation methods or sanitize HTML with DOMPurify.",
    },
]


def scan_security_patterns(target_dir: str) -> List[SecurityPatternFinding]:
    """Scan codebase for dangerous application security patterns."""
    findings: List[SecurityPatternFinding] = []
    root_path = Path(target_dir).resolve()
    finding_idx = 1

    for current_dir, dirs, files in os.walk(root_path):
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS and not d.startswith(".")]

        for filename in files:
            file_path = Path(current_dir) / filename
            rel_path = file_path.relative_to(root_path).as_posix()

            try:
                if file_path.stat().st_size > MAX_FILE_SIZE:
                    continue
            except OSError:
                continue

            if is_binary_file(file_path):
                continue

            # Determine if this is a test file (test files have lower risk confidence)
            is_test_file = (
                "test" in rel_path.lower()
                or "spec" in rel_path.lower()
                or filename.startswith("test_")
                or filename.endswith("_test.py")
                or filename.endswith(".spec.ts")
                or filename.endswith(".test.js")
            )

            try:
                with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                    lines = f.readlines()
            except Exception:
                continue

            for line_idx, line in enumerate(lines, start=1):
                # Avoid matching our own security rule definitions or engine comments
                if "rule_id" in line and "SEC-" in line:
                    continue

                for rule in SECURITY_RULES:
                    match = rule["pattern"].search(line)
                    if match:
                        matched_text = match.group(0)
                        redacted = redact_string(matched_text)

                        # Adjust severity if found in a test file
                        severity = rule["severity"]
                        confidence = rule["confidence"]
                        if is_test_file:
                            if severity in (SecuritySeverity.CRITICAL, SecuritySeverity.HIGH):
                                severity = SecuritySeverity.LOW
                            confidence = "LOW"

                        finding = SecurityPatternFinding(
                            finding_id=f"PAT-{finding_idx:03d}",
                            rule_id=rule["rule_id"],
                            category=rule["category"],
                            severity=severity,
                            confidence=confidence,
                            file_path=rel_path,
                            line_number=line_idx,
                            redacted_evidence=redacted,
                            explanation=rule["explanation"],
                            potential_impact=rule["impact"],
                            recommended_remediation=rule["remediation"],
                            requires_manual_verification=True,
                        )
                        findings.append(finding)
                        finding_idx += 1

    return findings
