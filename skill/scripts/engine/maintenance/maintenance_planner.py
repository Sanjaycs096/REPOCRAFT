"""Maintenance planner module for RepoCraft.

Aggregates findings across Phase 1 intelligence and Phase 2 maintenance modules
to produce a unified, prioritized, actionable maintenance plan.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional


class MaintenanceTask:
    def __init__(
        self,
        task_id: str,
        category: str,
        priority: str,  # P1, P2, P3, P4
        risk: str,      # LOW, MEDIUM, HIGH, CRITICAL
        description: str,
        evidence: str,
        expected_benefit: str,
        affected_files: List[str],
        dependencies: List[str],
        requires_approval: bool,
        suggested_implementation: str,
        validation_procedure: str,
        target_phase: int = 2,
    ):
        self.task_id = task_id
        self.category = category
        self.priority = priority
        self.risk = risk
        self.description = description
        self.evidence = evidence
        self.expected_benefit = expected_benefit
        self.affected_files = affected_files
        self.dependencies = dependencies
        self.requires_approval = requires_approval
        self.suggested_implementation = suggested_implementation
        self.validation_procedure = validation_procedure
        self.target_phase = target_phase

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "category": self.category,
            "priority": self.priority,
            "risk": self.risk,
            "description": self.description,
            "evidence": self.evidence,
            "expected_benefit": self.expected_benefit,
            "affected_files": self.affected_files,
            "dependencies": self.dependencies,
            "requires_approval": self.requires_approval,
            "suggested_implementation": self.suggested_implementation,
            "validation_procedure": self.validation_procedure,
            "target_phase": self.target_phase,
        }


class MaintenancePlanner:
    """Combines Phase 1 recommendations with Phase 2 maintenance analysis."""

    def __init__(
        self,
        phase1_findings: List[Dict[str, Any]],
        org_findings: List[Any],
        unused_files: List[Any],
        readme_audit: Any,
        doc_audit: Any,
        license_audit: Any,
        presentation_audit: Any,
    ):
        self.phase1_findings = phase1_findings
        self.org_findings = org_findings
        self.unused_files = unused_files
        self.readme_audit = readme_audit
        self.doc_audit = doc_audit
        self.license_audit = license_audit
        self.presentation_audit = presentation_audit
        self._counter = 1

    def _next_id(self, domain: str) -> str:
        tid = f"TASK-{domain.upper()}-{self._counter:03d}"
        self._counter += 1
        return tid

    def create_plan(self) -> List[MaintenanceTask]:
        tasks: List[MaintenanceTask] = []

        # 1. Organization Tasks
        for org in self.org_findings:
            tasks.append(
                MaintenanceTask(
                    task_id=self._next_id("ORG"),
                    category="Codebase Organization",
                    priority="P2",
                    risk=org.risk_level,
                    description=org.reason,
                    evidence=org.evidence,
                    expected_benefit="Improves repository navigation, reduces duplication, and cleans up directory structure.",
                    affected_files=[org.current_path] + ([org.proposed_path] if org.proposed_path else []),
                    dependencies=[],
                    requires_approval=org.requires_approval,
                    suggested_implementation=f"Relocate or consolidate '{org.current_path}'.",
                    validation_procedure=org.validation_steps,
                    target_phase=2,
                )
            )

        # 2. README & Documentation Tasks
        if not self.readme_audit.exists:
            tasks.append(
                MaintenanceTask(
                    task_id=self._next_id("DOC"),
                    category="Documentation",
                    priority="P1",
                    risk="LOW",
                    description="Author repository README.md from evidence-backed draft.",
                    evidence="No README file exists in repository root.",
                    expected_benefit="Provides immediate clarity, onboarding guidance, and setup instructions for developers.",
                    affected_files=["README.md"],
                    dependencies=[],
                    requires_approval=True,
                    suggested_implementation="Review and apply generated 'README-improved.md' draft.",
                    validation_procedure="Verify all sections accurately represent project entry points and commands.",
                    target_phase=2,
                )
            )
        elif self.readme_audit.overall_score < 70 or self.readme_audit.placeholders_detected:
            tasks.append(
                MaintenanceTask(
                    task_id=self._next_id("DOC"),
                    category="Documentation",
                    priority="P2",
                    risk="LOW",
                    description="Enhance existing README.md with missing sections and remove placeholders.",
                    evidence=f"README completeness score is {self.readme_audit.overall_score}/100. Placeholders: {', '.join(self.readme_audit.placeholders_detected) or 'None'}.",
                    expected_benefit="Eliminates placeholder content and clarifies setup, usage, and testing workflows.",
                    affected_files=["README.md"],
                    dependencies=[],
                    requires_approval=True,
                    suggested_implementation="Incorporate missing sections from 'README-improved.md'.",
                    validation_procedure="Review diff against original README.",
                    target_phase=2,
                )
            )

        # 3. Governance Policies
        for missing_gov in self.doc_audit.missing_governance:
            tasks.append(
                MaintenanceTask(
                    task_id=self._next_id("GOV"),
                    category="Repository Governance",
                    priority="P3",
                    risk="LOW",
                    description=f"Add standard {missing_gov} policy.",
                    evidence=f"No {missing_gov} file detected in repository.",
                    expected_benefit=f"Clarifies community conventions and expectations via {missing_gov}.",
                    affected_files=[missing_gov],
                    dependencies=[],
                    requires_approval=True,
                    suggested_implementation=f"Adopt the generated draft for {missing_gov}.",
                    validation_procedure=f"Review text of {missing_gov} for project alignment.",
                    target_phase=2,
                )
            )

        # 4. Broken links / Missing images
        if self.doc_audit.broken_links or self.doc_audit.missing_images:
            affected = list(set([b.doc_path for b in self.doc_audit.broken_links + self.doc_audit.missing_images]))
            tasks.append(
                MaintenanceTask(
                    task_id=self._next_id("DOC"),
                    category="Documentation Hygiene",
                    priority="P2",
                    risk="LOW",
                    description="Fix broken internal documentation links and missing local media references.",
                    evidence=f"Found {len(self.doc_audit.broken_links)} broken link(s) and {len(self.doc_audit.missing_images)} missing image reference(s).",
                    expected_benefit="Restores reliable documentation navigation and eliminates broken images.",
                    affected_files=affected,
                    dependencies=[],
                    requires_approval=True,
                    suggested_implementation="Update relative paths in affected markdown documents to valid target files.",
                    validation_procedure="Rerun documentation auditor to confirm 0 broken links.",
                    target_phase=2,
                )
            )

        # 5. Licensing Tasks
        if not self.license_audit.has_license_file:
            tasks.append(
                MaintenanceTask(
                    task_id=self._next_id("LIC"),
                    category="Licensing & Compliance",
                    priority="P1",
                    risk="HIGH",
                    description="Project maintainer must select and add a LICENSE file.",
                    evidence="No LICENSE or COPYING file discovered.",
                    expected_benefit="Defines legal permissions and protection for maintainers and downstream consumers.",
                    affected_files=["LICENSE"],
                    dependencies=[],
                    requires_approval=True,
                    suggested_implementation="User/Maintainer chooses and approves explicit license text (MIT, Apache-2.0, etc.).",
                    validation_procedure="Verify LICENSE file text matches intended licensing strategy.",
                    target_phase=2,
                )
            )
        elif self.license_audit.inconsistencies:
            tasks.append(
                MaintenanceTask(
                    task_id=self._next_id("LIC"),
                    category="Licensing & Compliance",
                    priority="P2",
                    risk="MEDIUM",
                    description="Reconcile conflicting license declarations between manifest and LICENSE file.",
                    evidence="; ".join(self.license_audit.inconsistencies),
                    expected_benefit="Avoids conflicting legal signals in package repositories and source distributions.",
                    affected_files=list(self.license_audit.manifest_declarations.keys()) + ([self.license_audit.license_path] if self.license_audit.license_path else []),
                    dependencies=[],
                    requires_approval=True,
                    suggested_implementation="Align manifest license field with LICENSE file terms.",
                    validation_procedure="Confirm package manifest declarations match LICENSE file.",
                    target_phase=2,
                )
            )

        # 6. Unused File Evaluation Tasks
        confirmed_unused = [u for u in self.unused_files if u.confidence.value == "CONFIRMED_UNUSED"]
        if confirmed_unused:
            tasks.append(
                MaintenanceTask(
                    task_id=self._next_id("CLN"),
                    category="Repository Hygiene",
                    priority="P3",
                    risk="LOW",
                    description="Review and prune confirmed obsolete temporary files.",
                    evidence=f"Discovered {len(confirmed_unused)} temporary/backup file(s): {', '.join(c.relative_path for c in confirmed_unused[:3])}.",
                    expected_benefit="Keeps git worktree clean and prevents accidental check-ins of temporary files.",
                    affected_files=[c.relative_path for c in confirmed_unused],
                    dependencies=[],
                    requires_approval=True,
                    suggested_implementation="Review candidate list and remove verified obsolete temporary files.",
                    validation_procedure="Ensure no build or test scripts depended on deleted temporary files.",
                    target_phase=2,
                )
            )

        # Priority sort: P1 -> P2 -> P3 -> P4
        priority_order = {"P1": 0, "P2": 1, "P3": 2, "P4": 3}
        tasks.sort(key=lambda t: (priority_order.get(t.priority, 9), t.task_id))
        return tasks

