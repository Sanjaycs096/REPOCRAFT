"""Main orchestrator for RepoCraft Repository Intelligence Engine.

Coordinates discovery, file inventory, git baseline, architecture extraction,
governance discovery, test/CI discovery, health assessment, and report generation.
"""
from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .architecture import ArchitectureAnalyzer
from .discovery import EcosystemDetector
from .file_inventory import build_inventory
from .git_analyzer import analyze_git_baseline
from .governance import GovernanceAnalyzer
from .health_assessor import HealthAssessor
from .report_generator import ReportGenerator
from .testing_ci import TestingAndCIDiscovery
from .types import FileCategory, RepositoryIntelligenceReport


class IntelligenceEngine:
    """End-to-end repository intelligence analyzer."""

    def __init__(self, target_dir: Path, output_dir: Optional[Path] = None):
        self.target_dir = target_dir.resolve()
        if output_dir:
            self.output_dir = output_dir.resolve()
        else:
            # Default location: ../repocraft-reports outside target repository
            self.output_dir = (self.target_dir.parent / "repocraft-reports").resolve()

    def run(self) -> Tuple[RepositoryIntelligenceReport, Dict[str, Path]]:
        """Run complete intelligence workflow and generate reports."""
        # 1. Git Baseline
        git_baseline = analyze_git_baseline(self.target_dir)

        # 2. File Inventory
        inventory, category_counts, excluded_dirs = build_inventory(self.target_dir)

        # 3. Discovery (Ecosystem, languages, manifests, entry points)
        eco = EcosystemDetector(self.target_dir, inventory)
        languages = eco.detect_languages()
        package_managers, manifests, lockfiles = eco.detect_package_managers_and_manifests()
        frameworks = eco.detect_frameworks_and_tech()
        entry_points = eco.detect_entry_points()
        is_monorepo, monorepo_packages = eco.detect_monorepo()
        detected_types = eco.detect_project_types(is_monorepo)

        # Discover directories
        source_dirs = sorted(list(set(
            item.relative_path.split("/")[0]
            for item in inventory
            if item.category == FileCategory.SOURCE and "/" in item.relative_path
        )))
        test_dirs = sorted(list(set(
            item.relative_path.split("/")[0]
            for item in inventory
            if item.category == FileCategory.TESTING and "/" in item.relative_path
        )))
        asset_dirs = sorted(list(set(
            item.relative_path.split("/")[0]
            for item in inventory
            if item.category == FileCategory.ASSETS and "/" in item.relative_path
        )))
        config_files = sorted([
            item.relative_path
            for item in inventory
            if item.category == FileCategory.CONFIGURATION
        ])
        doc_files = sorted([
            item.relative_path
            for item in inventory
            if item.category == FileCategory.DOCUMENTATION
        ])

        # 4. Architecture
        arch_analyzer = ArchitectureAnalyzer(self.target_dir, inventory)
        architecture = arch_analyzer.analyze()

        # 5. Governance
        gov_analyzer = GovernanceAnalyzer(self.target_dir, inventory)
        governance = gov_analyzer.analyze()

        # 6. Testing & CI/CD
        test_ci_discovery = TestingAndCIDiscovery(self.target_dir, inventory)
        discovered_commands, cicd_workflows = test_ci_discovery.discover()

        # 7. Health Assessment
        assessor = HealthAssessor(
            repo_root=self.target_dir,
            inventory=inventory,
            git_baseline=git_baseline,
            governance=governance,
            discovered_commands=discovered_commands,
            cicd_workflows=cicd_workflows,
            category_counts=category_counts,
        )
        findings = assessor.assess()

        # 8. Safe warnings & unknowns
        safe_warnings = []
        if git_baseline.warning:
            safe_warnings.append(git_baseline.warning)
        sensitive_count = sum(1 for item in inventory if item.is_sensitive)
        if sensitive_count > 0:
            safe_warnings.append(
                f"{sensitive_count} sensitive/secret filename(s) detected. "
                "Metadata recorded; file contents were strictly unread and unprinted."
            )

        unknowns_and_limitations = [
            "Static analysis only. Discovered test and build commands were not executed.",
            "Dynamic runtime behaviors and remote API configurations are unverified.",
            "No dependencies were installed; no project source files were altered.",
            "All recommendations are evidence-based proposals requiring maintainer review.",
        ]

        # Compile report
        report = RepositoryIntelligenceReport(
            repo_root=str(self.target_dir),
            project_name=self.target_dir.name,
            detected_types=detected_types,
            languages=languages,
            frameworks=frameworks,
            package_managers=package_managers,
            manifests=manifests,
            entry_points=entry_points,
            source_directories=source_dirs,
            asset_directories=asset_dirs,
            configuration_files=config_files,
            test_directories=test_dirs,
            documentation_files=doc_files,
            cicd_workflows=cicd_workflows,
            is_monorepo=is_monorepo,
            monorepo_packages=monorepo_packages,
            file_inventory_summary={
                "total_files": len(inventory),
                "category_counts": category_counts,
                "excluded_directories": excluded_dirs,
                "sensitive_files_detected": sensitive_count,
            },
            git_baseline=git_baseline,
            governance=governance,
            discovered_commands=discovered_commands,
            architecture=architecture,
            findings=findings,
            unknowns_and_limitations=unknowns_and_limitations,
            safe_warnings=safe_warnings,
        )

        # 9. Generate Reports
        gen = ReportGenerator(report, self.output_dir)
        output_files = gen.generate_all()

        return report, output_files

