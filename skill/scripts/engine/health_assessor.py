"""Repository health and risk assessment engine for RepoCraft.

Evaluates repository organization, documentation, testing, CI/CD, security hygiene,
and Git baseline health against evidence-based rules.
Never inflates severity or claims unverified security.
"""
from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Set

from .types import (
    DiscoveredCommand,
    EvidenceLevel,
    FileCategory,
    FileInventoryItem,
    GitBaseline,
    GovernanceItem,
    HealthFinding,
    Severity,
)


class HealthAssessor:
    """Produces prioritized, evidence-backed findings and recommendations."""

    def __init__(
        self,
        repo_root: Path,
        inventory: List[FileInventoryItem],
        git_baseline: GitBaseline,
        governance: Dict[str, GovernanceItem],
        discovered_commands: List[DiscoveredCommand],
        cicd_workflows: List[str],
        category_counts: Dict[str, int],
    ):
        self.repo_root = repo_root
        self.inventory = inventory
        self.git_baseline = git_baseline
        self.governance = governance
        self.discovered_commands = discovered_commands
        self.cicd_workflows = cicd_workflows
        self.category_counts = category_counts
        self.paths_set: Set[str] = {item.relative_path for item in inventory}
        self.findings: List[HealthFinding] = []
        self._counter = 1

    def assess(self) -> List[HealthFinding]:
        self.findings.clear()
        self._assess_security()
        self._assess_git_governance()
        self._assess_documentation()
        self._assess_testing_and_ci()
        self._assess_hygiene_and_config()
        self._assess_project_organization()

        # Sort findings: CRITICAL -> HIGH -> MEDIUM -> LOW -> INFO
        severity_order = {
            Severity.CRITICAL: 0,
            Severity.HIGH: 1,
            Severity.MEDIUM: 2,
            Severity.LOW: 3,
            Severity.INFO: 4,
        }
        self.findings.sort(key=lambda f: (severity_order[f.severity], f.finding_id))
        return self.findings

    def _next_id(self, domain: str) -> str:
        fid = f"FINDING-{domain.upper()}-{self._counter:03d}"
        self._counter += 1
        return fid

    def _assess_security(self) -> None:
        # Check for committed or untracked sensitive files (.env, keys)
        sensitive_items = [item for item in self.inventory if item.is_sensitive]
        if sensitive_items:
            for item in sensitive_items:
                self.findings.append(
                    HealthFinding(
                        finding_id=self._next_id("SEC"),
                        category="Security",
                        severity=Severity.HIGH,
                        evidence_level=EvidenceLevel.VERIFIED,
                        evidence=f"Sensitive filename '{item.relative_path}' detected in repository.",
                        explanation=(
                            "Environment files, private keys, or credential templates in the repository tree "
                            "risk exposing secrets or accidentally leaking credentials if committed."
                        ),
                        suggested_action=(
                            "Ensure the file is explicitly added to .gitignore and verified that no live secrets are stored."
                        ),
                        requires_approval=True,
                        target_phase=3,
                    )
                )

        # Check for missing SECURITY.md
        sec_item = self.governance.get("security_policy")
        if not sec_item or not sec_item.exists:
            self.findings.append(
                HealthFinding(
                    finding_id=self._next_id("SEC"),
                    category="Security Governance",
                    severity=Severity.MEDIUM,
                    evidence_level=EvidenceLevel.VERIFIED,
                    evidence="No SECURITY.md policy found in repository root or .github/.",
                    explanation=(
                        "A security policy clarifies vulnerability reporting channels and response commitments for maintainers."
                    ),
                    suggested_action="Draft and review a project-appropriate SECURITY.md vulnerability reporting guide.",
                    requires_approval=True,
                    target_phase=3,
                )
            )

    def _assess_git_governance(self) -> None:
        if not self.git_baseline.is_git_repository:
            self.findings.append(
                HealthFinding(
                    finding_id=self._next_id("GIT"),
                    category="Git Baseline",
                    severity=Severity.HIGH,
                    evidence_level=EvidenceLevel.VERIFIED,
                    evidence="Target directory is not a Git worktree or Git repository.",
                    explanation="RepoCraft relies on Git history and worktree safety to establish baselines and isolate changes.",
                    suggested_action="Initialize a Git repository and commit an initial baseline before applying automated repairs.",
                    requires_approval=True,
                    target_phase=1,
                )
            )
            return

        if self.git_baseline.pre_existing_modifications_count > 0:
            self.findings.append(
                HealthFinding(
                    finding_id=self._next_id("GIT"),
                    category="Git Baseline",
                    severity=Severity.LOW,
                    evidence_level=EvidenceLevel.VERIFIED,
                    evidence=(
                        f"Found {len(self.git_baseline.staged_files)} staged, "
                        f"{len(self.git_baseline.unstaged_files)} unstaged, and "
                        f"{len(self.git_baseline.untracked_files)} untracked pre-existing files."
                    ),
                    explanation=(
                        "Pre-existing modifications belong to the user. RepoCraft will protect them and never "
                        "modify, stash, or commit user-owned modifications."
                    ),
                    suggested_action="User may commit or stash pending changes before invoking maintenance phases.",
                    requires_approval=False,
                    target_phase=1,
                )
            )

        if not (self.repo_root / ".gitignore").is_file():
            self.findings.append(
                HealthFinding(
                    finding_id=self._next_id("GIT"),
                    category="Git Hygiene",
                    severity=Severity.MEDIUM,
                    evidence_level=EvidenceLevel.VERIFIED,
                    evidence="No .gitignore file detected in repository root.",
                    explanation="Missing .gitignore increases the risk of committing dependencies, temporary files, and secrets.",
                    suggested_action="Create an ecosystem-tailored .gitignore file.",
                    requires_approval=True,
                    target_phase=2,
                )
            )

    def _assess_documentation(self) -> None:
        readme = self.governance.get("readme")
        if not readme or not readme.exists:
            self.findings.append(
                HealthFinding(
                    finding_id=self._next_id("DOC"),
                    category="Documentation",
                    severity=Severity.HIGH,
                    evidence_level=EvidenceLevel.VERIFIED,
                    evidence="No README file (README.md, README.rst, or README.txt) found in repository root.",
                    explanation="A README is essential for onboarding, usage instructions, and project purpose.",
                    suggested_action="Author an evidence-backed README.md detailing project architecture, installation, and usage.",
                    requires_approval=True,
                    target_phase=2,
                )
            )
        elif readme.is_empty or readme.size_bytes < 50:
            self.findings.append(
                HealthFinding(
                    finding_id=self._next_id("DOC"),
                    category="Documentation",
                    severity=Severity.MEDIUM,
                    evidence_level=EvidenceLevel.VERIFIED,
                    evidence=f"README exists at '{readme.relative_path}' but is incomplete ({readme.size_bytes} bytes).",
                    explanation="The existing README lacks substantive project details or setup documentation.",
                    suggested_action="Expand the README with verified tech stack, prerequisites, and execution commands.",
                    requires_approval=True,
                    target_phase=2,
                )
            )

        license_item = self.governance.get("license")
        if not license_item or not license_item.exists:
            self.findings.append(
                HealthFinding(
                    finding_id=self._next_id("DOC"),
                    category="Documentation & Governance",
                    severity=Severity.MEDIUM,
                    evidence_level=EvidenceLevel.VERIFIED,
                    evidence="No LICENSE file detected in repository root.",
                    explanation=(
                        "Without a clear license, standard copyright applies and downstream users/maintainers have no defined rights."
                    ),
                    suggested_action="Maintainer should select and approve an open-source or proprietary software license.",
                    requires_approval=True,
                    target_phase=2,
                )
            )

        contributing = self.governance.get("contributing")
        if not contributing or not contributing.exists:
            self.findings.append(
                HealthFinding(
                    finding_id=self._next_id("DOC"),
                    category="Documentation & Governance",
                    severity=Severity.LOW,
                    evidence_level=EvidenceLevel.VERIFIED,
                    evidence="No CONTRIBUTING.md guidelines detected.",
                    explanation="Clear contribution guidelines help external and internal contributors follow repository conventions.",
                    suggested_action="Add a CONTRIBUTING.md guide with setup, testing, and PR conventions.",
                    requires_approval=True,
                    target_phase=2,
                )
            )

    def _assess_testing_and_ci(self) -> None:
        has_tests = self.category_counts.get(FileCategory.TESTING.value, 0) > 0
        has_test_cmds = any("test" in c.gate_name.lower() for c in self.discovered_commands)

        if not has_tests and not has_test_cmds:
            self.findings.append(
                HealthFinding(
                    finding_id=self._next_id("TEST"),
                    category="Quality Assurance",
                    severity=Severity.HIGH,
                    evidence_level=EvidenceLevel.VERIFIED,
                    evidence="No test files or test runner configuration discovered.",
                    explanation="Untested repositories present regression risks during automated and manual maintenance.",
                    suggested_action="Configure a modern test runner (e.g. pytest, vitest) and introduce baseline test suites.",
                    requires_approval=True,
                    target_phase=3,
                )
            )

        if not self.cicd_workflows:
            self.findings.append(
                HealthFinding(
                    finding_id=self._next_id("CICD"),
                    category="CI/CD Automation",
                    severity=Severity.MEDIUM,
                    evidence_level=EvidenceLevel.VERIFIED,
                    evidence="No CI/CD pipeline workflows (.github/workflows/, .gitlab-ci.yml, etc.) discovered.",
                    explanation="Automated verification on pull requests is missing, requiring manual check execution.",
                    suggested_action="Introduce a GitHub Actions workflow to run linting, typechecking, and automated tests.",
                    requires_approval=True,
                    target_phase=3,
                )
            )

    def _assess_hygiene_and_config(self) -> None:
        # Check for editorconfig
        if ".editorconfig" not in self.paths_set:
            self.findings.append(
                HealthFinding(
                    finding_id=self._next_id("HYG"),
                    category="Repository Hygiene",
                    severity=Severity.INFO,
                    evidence_level=EvidenceLevel.VERIFIED,
                    evidence="No .editorconfig found in repository root.",
                    explanation=".editorconfig helps maintain consistent indentation and encoding across diverse IDEs.",
                    suggested_action="Consider providing a root .editorconfig file.",
                    requires_approval=False,
                    target_phase=2,
                )
            )

    def _assess_project_organization(self) -> None:
        source_count = self.category_counts.get(FileCategory.SOURCE.value, 0)
        root_source_files = [
            item.relative_path
            for item in self.inventory
            if item.category == FileCategory.SOURCE and "/" not in item.relative_path
        ]
        # If there are many source files sitting loose in root
        if len(root_source_files) > 5:
            self.findings.append(
                HealthFinding(
                    finding_id=self._next_id("ORG"),
                    category="Project Organization",
                    severity=Severity.LOW,
                    evidence_level=EvidenceLevel.VERIFIED,
                    evidence=f"{len(root_source_files)} source files located directly in root directory.",
                    explanation="Organizing source code into a dedicated 'src/' or package directory improves maintainability.",
                    suggested_action="Evaluate grouping root application files into a structured source folder.",
                    requires_approval=True,
                    target_phase=2,
                )
            )

