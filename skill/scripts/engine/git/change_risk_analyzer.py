"""Module 3.5 — Change Risk Analyzer for RepoCraft Phase 5.

Classifies changed files and diff hunks by risk level (LOW, MEDIUM, HIGH, CRITICAL, UNKNOWN).
Detects sensitive files, authentication/crypto/payment code, secret patterns, and test assertion weakening.
"""
from __future__ import annotations

import os
import re
from pathlib import Path
from typing import List, Tuple

from .git_types import ChangeFile, ChangeRisk

# Sensitive file and directory regexes
AUTH_PATTERNS = [
    re.compile(r"(auth|login|session|jwt|oauth|sso|permission|rbac|credential)", re.I),
]
CRYPTO_PATTERNS = [
    re.compile(r"(crypto|cipher|encrypt|decrypt|hash|signature|key_deriv)", re.I),
]
PAYMENT_PATTERNS = [
    re.compile(r"(payment|billing|stripe|paypal|checkout|invoice|pricing)", re.I),
]
MIGRATION_PATTERNS = [
    re.compile(r"(migration|alembic|db/schema|flyway|liquibase)", re.I),
]
LICENSE_PATTERNS = [
    re.compile(r"^license(\.(md|txt))?$", re.I),
    re.compile(r"^copying(\.(md|txt))?$", re.I),
]
CICD_PATTERNS = [
    re.compile(r"^\.github/(workflows|actions)/", re.I),
    re.compile(r"^\.gitlab-ci\.yml$", re.I),
    re.compile(r"^azure-pipelines\.yml$", re.I),
]
DEPENDENCY_PATTERNS = [
    re.compile(r"(package\.json|package-lock\.json|yarn\.lock|pnpm-lock\.yaml|pyproject\.toml|poetry\.lock|Pipfile(\.lock)?|requirements\.txt|Cargo\.(toml|lock)|go\.(mod|sum)|pom\.xml|build\.gradle(\.kts)?)$", re.I),
]
PROD_CONFIG_PATTERNS = [
    re.compile(r"(docker-compose.*prod.*\.ya?ml|kubernetes/|k8s/|helm/|terraform/|\.env\.prod)", re.I),
]
DOC_PATTERNS = [
    re.compile(r"\.(md|rst|txt|adoc)$", re.I),
    re.compile(r"^(docs/|documentation/)", re.I),
    re.compile(r"^README(\.[a-zA-Z0-9]+)?$", re.I),
    re.compile(r"^(CONTRIBUTING|CHANGELOG|CODE_OF_CONDUCT)(\.[a-zA-Z0-9]+)?$", re.I),
]

# Sensitive content patterns (redacted immediately)
SECRET_CONTENT_PATTERNS = [
    (re.compile(r"-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----"), "Private key header"),
    (re.compile(r"(api[_-]?key|access[_-]?token|auth[_-]?token|secret[_-]?key)\s*[:=]\s*['\"][0-9a-zA-Z\-_]{8,}['\"]", re.I), "API or Auth token assignment"),
    (re.compile(r"(AKIA[0-9A-Z]{16})"), "AWS Access Key ID"),
    (re.compile(r"ghp_[0-9a-zA-Z]{36}"), "GitHub Personal Access Token"),
]

TEST_ASSERTION_PATTERN = re.compile(r"^\s*-\s*(assert\s|expect\(|\.should\b|self\.assert)", re.I)


class ChangeRiskAnalyzer:
    """Evaluates risk profile for repository modifications."""

    def evaluate_file(self, cf: ChangeFile) -> ChangeFile:
        """Classify risk for a single ChangeFile based on path and diff content."""
        risk_reasons: List[str] = []
        sensitive_patterns: List[str] = []
        path_lower = cf.file_path.lower()
        file_name = Path(cf.file_path).name.lower()

        # 1. CRITICAL: License changes
        if any(p.search(file_name) for p in LICENSE_PATTERNS):
            cf.risk = ChangeRisk.CRITICAL
            risk_reasons.append("License file modification requires legal and human review.")

        # 2. CRITICAL: Auth, crypto, payment, database migrations
        elif any(p.search(path_lower) for p in AUTH_PATTERNS):
            cf.risk = ChangeRisk.CRITICAL
            risk_reasons.append("Authentication or authorization logic modification.")
        elif any(p.search(path_lower) for p in CRYPTO_PATTERNS):
            cf.risk = ChangeRisk.CRITICAL
            risk_reasons.append("Cryptographic implementation modification.")
        elif any(p.search(path_lower) for p in PAYMENT_PATTERNS):
            cf.risk = ChangeRisk.CRITICAL
            risk_reasons.append("Payment or financial transaction logic modification.")
        elif any(p.search(path_lower) for p in MIGRATION_PATTERNS):
            cf.risk = ChangeRisk.CRITICAL
            risk_reasons.append("Database schema migration modification.")

        # 3. HIGH: CI/CD, Dependencies, Production config
        elif any(p.search(cf.file_path) for p in CICD_PATTERNS):
            cf.risk = ChangeRisk.HIGH
            risk_reasons.append("CI/CD pipeline workflow configuration change.")
        elif any(p.search(file_name) for p in DEPENDENCY_PATTERNS):
            cf.risk = ChangeRisk.HIGH
            risk_reasons.append("Dependency manifest or lockfile change.")
        elif any(p.search(path_lower) for p in PROD_CONFIG_PATTERNS):
            cf.risk = ChangeRisk.HIGH
            risk_reasons.append("Production infrastructure or deployment configuration.")

        # 4. LOW: Documentation, markdown, comments
        elif any(p.search(cf.file_path) for p in DOC_PATTERNS):
            cf.risk = ChangeRisk.LOW
            risk_reasons.append("Documentation and project metadata change.")

        # 5. UNKNOWN or default
        elif cf.is_binary:
            cf.risk = ChangeRisk.UNKNOWN
            risk_reasons.append("Binary file modification cannot be verified via text diff.")
        else:
            cf.risk = ChangeRisk.MEDIUM
            risk_reasons.append("General application source code modification.")

        # Inspect diff content for secret patterns and test assertion weakening
        if cf.diff_text:
            for pat, desc in SECRET_CONTENT_PATTERNS:
                if pat.search(cf.diff_text):
                    sensitive_patterns.append(desc)
                    # Escalate to CRITICAL if secrets found
                    cf.risk = ChangeRisk.CRITICAL
                    risk_reasons.append(f"Potential secret detected: {desc}")

            # Check for test assertion deletion (assertion weakening)
            if "test" in path_lower:
                deleted_assertions = 0
                for line in cf.diff_text.splitlines():
                    if line.startswith("-") and not line.startswith("---"):
                        if TEST_ASSERTION_PATTERN.match(line):
                            deleted_assertions += 1
                if deleted_assertions > 0:
                    cf.risk = ChangeRisk.HIGH if cf.risk != ChangeRisk.CRITICAL else ChangeRisk.CRITICAL
                    risk_reasons.append(f"Test assertion weakening detected: {deleted_assertions} assertions removed.")

        cf.risk_reasons = risk_reasons
        cf.sensitive_patterns = sensitive_patterns

        # Formulate recommendation and approval requirement
        if cf.risk == ChangeRisk.CRITICAL:
            cf.approval_requirement = "MANUAL_REMEDIATION_ONLY"
            cf.recommendation = "Do not stage or commit automatically. Review and resolve manually."
        elif cf.risk == ChangeRisk.HIGH:
            cf.approval_requirement = "EXPLICIT_PER_FILE_APPROVAL"
            cf.recommendation = "Review carefully before staging; explicit approval required."
        elif cf.risk == ChangeRisk.MEDIUM:
            cf.approval_requirement = "STAGING_APPROVAL_REQUIRED"
            cf.recommendation = "Standard review; approve only verified changes."
        elif cf.risk == ChangeRisk.LOW:
            cf.approval_requirement = "STAGING_APPROVAL_REQUIRED"
            cf.recommendation = "Safe candidate for staging."
        else:
            cf.approval_requirement = "MANUAL_INSPECTION_REQUIRED"
            cf.recommendation = "Inspect binary or unknown file before staging."

        return cf

    def evaluate_all(self, files: List[ChangeFile]) -> Tuple[List[ChangeFile], ChangeRisk]:
        """Classify all files and determine overall repository change risk."""
        evaluated: List[ChangeFile] = []
        highest_risk = ChangeRisk.LOW

        risk_order = {
            ChangeRisk.LOW: 1,
            ChangeRisk.MEDIUM: 2,
            ChangeRisk.HIGH: 3,
            ChangeRisk.CRITICAL: 4,
            ChangeRisk.UNKNOWN: 3,
        }

        for f in files:
            res = self.evaluate_file(f)
            evaluated.append(res)
            if risk_order.get(res.risk, 1) > risk_order.get(highest_risk, 1):
                highest_risk = res.risk

        return evaluated, highest_risk

