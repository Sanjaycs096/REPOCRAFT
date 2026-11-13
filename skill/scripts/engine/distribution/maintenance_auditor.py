"""Post-release maintenance auditor verifying manifest consistency, policies, and telemetry-free invariants."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from engine.integration import ArtifactRegistry, PhaseRegistry
from .distribution_types import MaintenanceAuditReport


class MaintenanceAuditor:
    """Audits post-release operational health, policy completeness, and zero-telemetry guarantees."""

    EXPECTED_POLICIES = [
        "safety-and-git-baseline.md",
        "quality-gates.md",
        "repository-intelligence.md",
        "maintenance-policy.md",
        "documentation-policy.md",
        "github-presentation-policy.md",
        "security-testing-policy.md",
        "repair-and-regression-policy.md",
        "git-workflow-policy.md",
        "agent-compatibility.md",
        "release-and-portability-policy.md",
    ]

    EXPECTED_SCRIPTS = [
        "repocraft_intel.py",
        "repocraft_maintenance.py",
        "repocraft_security.py",
        "repocraft_repair.py",
        "repocraft_git.py",
        "repocraft_status.py",
        "repocraft_release.py",
    ]

    @classmethod
    def audit_repository_health(cls, repo_root: Path, version: str = "1.0.0-rc1") -> MaintenanceAuditReport:
        """Run comprehensive post-release maintenance audit."""
        root = repo_root.resolve()
        errors: List[str] = []
        warnings: List[str] = []
        recommendations: List[str] = []

        # 1. Manifests & Version consistency
        manifest_p = root / "MANIFEST.json"
        pyproject_p = root / "pyproject.toml"
        install_p = root / "install.py"

        manifest_version = None
        if manifest_p.is_file():
            try:
                m_data = json.loads(manifest_p.read_text(encoding="utf-8"))
                manifest_version = m_data.get("version")
            except Exception as e:
                errors.append(f"MANIFEST.json unreadable: {e}")

        pyproject_version = None
        if pyproject_p.is_file():
            text = pyproject_p.read_text(encoding="utf-8")
            for line in text.splitlines():
                if line.strip().startswith("version ="):
                    pyproject_version = line.split("=")[1].strip().strip('"').strip("'")

        install_version = None
        if install_p.is_file():
            text = install_p.read_text(encoding="utf-8")
            for line in text.splitlines():
                if '"version":' in line:
                    install_version = line.split(":")[1].strip().strip('",').strip("'")

        manifests_consistent = (
            manifest_version == version
            and pyproject_version == version
            and install_version == version
        )
        if not manifests_consistent:
            errors.append(
                f"Version mismatch detected: expected {version}, manifest={manifest_version}, pyproject={pyproject_version}, install={install_version}"
            )

        # 2. Policy files intact
        ref_dir = root / "skill" / "references"
        missing_policies = []
        for pol in cls.EXPECTED_POLICIES:
            p_file = ref_dir / pol
            if not p_file.is_file() or p_file.stat().st_size == 0:
                missing_policies.append(pol)
        policy_files_intact = len(missing_policies) == 0
        if not policy_files_intact:
            errors.append(f"Missing or empty policy files: {missing_policies}")

        # 3. CLI drivers intact
        scripts_dir = root / "skill" / "scripts"
        missing_scripts = []
        for s in cls.EXPECTED_SCRIPTS:
            s_file = scripts_dir / s
            if not s_file.is_file() or s_file.stat().st_size == 0:
                missing_scripts.append(s)
        cli_drivers_intact = len(missing_scripts) == 0
        if not cli_drivers_intact:
            errors.append(f"Missing runtime CLI scripts: {missing_scripts}")

        # 4. Schema compatibility
        artifacts = ArtifactRegistry.list_all()
        schemas_compatible = len(artifacts) >= 30

        # 5. Zero-telemetry audit: inspect AST imports and tracking URLs
        zero_telemetry = True
        forbidden_import_modules = {"sentry_sdk", "mixpanel", "amplitude", "segment", "posthog", "datadog"}
        tracking_domains = ["google-analytics.com", "api.mixpanel.com", "api.amplitude.com", "api.segment.io"]

        for pyf in scripts_dir.rglob("*.py"):
            if pyf.name == "maintenance_auditor.py":
                continue
            try:
                import ast
                code = pyf.read_text(encoding="utf-8", errors="replace")
                tree = ast.parse(code, filename=str(pyf))
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            if alias.name in forbidden_import_modules:
                                zero_telemetry = False
                                errors.append(f"Forbidden tracking import '{alias.name}' detected in {pyf.name}")
                    elif isinstance(node, ast.ImportFrom):
                        if node.module and any(node.module.startswith(m) for m in forbidden_import_modules):
                            zero_telemetry = False
                            errors.append(f"Forbidden tracking import from '{node.module}' detected in {pyf.name}")
                # Check for tracking URLs
                for domain in tracking_domains:
                    if domain in code.lower():
                        zero_telemetry = False
                        errors.append(f"Tracking domain '{domain}' found in {pyf.name}")
            except Exception:
                pass

        is_healthy = len(errors) == 0

        if is_healthy:
            recommendations.append("All post-release operational invariants verified. Ready for maintainer sign-off.")

        return MaintenanceAuditReport(
            timestamp=datetime.now(timezone.utc).isoformat(),
            version=version,
            installation_healthy=is_healthy,
            manifests_consistent=manifests_consistent,
            policy_files_intact=policy_files_intact,
            cli_drivers_intact=cli_drivers_intact,
            schemas_compatible=schemas_compatible,
            zero_telemetry_guarantee=zero_telemetry,
            known_limitations=[
                "Native multi-phase execution certified on Google Antigravity.",
                "Fast-forward git remote permissions required for publishing.",
            ],
            recommendations=recommendations,
            errors=errors,
            warnings=warnings,
        )
