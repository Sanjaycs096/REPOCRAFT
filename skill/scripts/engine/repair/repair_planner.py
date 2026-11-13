"""Module C — Evidence-Based Repair Planner for RepoCraft Phase 4.

Synthesizes normalized findings into prioritized, structured RepairTasks with:
- Concrete ProposedPatches where safely supported
- Explicit risk ratings and approval requirements
- Root-cause keys to prevent retry circumvention
- Priority ranking (1 = highest)
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import List, Optional

from .patch_generator import PatchGenerator, sha256_of_file
from .repair_classifier import classify_finding
from .repair_types import (
    ExecutionDisposition,
    NormalizedFinding,
    ProposedPatch,
    RepairCategory,
    RepairRiskLevel,
    RepairStatus,
    RepairTask,
)


class RepairPlanner:
    """Plans structured, prioritized repair tasks based on ingested evidence."""

    def __init__(self, target_dir: str):
        self.target_dir = Path(target_dir).resolve()
        self.patch_gen = PatchGenerator(str(self.target_dir))
        self._task_counter = 1

    def _next_task_id(self) -> str:
        tid = f"REP-{self._task_counter:03d}"
        self._task_counter += 1
        return tid

    def plan_repairs(self, findings: List[NormalizedFinding]) -> List[RepairTask]:
        """Construct prioritized repair tasks from normalized findings."""
        tasks: List[RepairTask] = []
        self._task_counter = 1

        for finding in findings:
            category, risk_level, disposition = classify_finding(finding)

            # Determine priority
            if risk_level == RepairRiskLevel.CRITICAL:
                priority = 1
            elif category == RepairCategory.SECURITY_HARDENING:
                priority = 2
            elif category == RepairCategory.TEST_FAILURE_CORRECTION:
                priority = 3
            elif category in (RepairCategory.SAFE_CONFIGURATION_CORRECTION, RepairCategory.MISSING_CONFIGURATION):
                priority = 4
            elif category in (RepairCategory.DOCUMENTATION_CORRECTION, RepairCategory.README_IMPROVEMENT):
                priority = 5
            elif category == RepairCategory.NAMING_AND_ORGANIZATION:
                priority = 6
            else:
                priority = 7

            # Derive root cause key
            affected = finding.affected_files[0] if finding.affected_files else "repo"
            root_cause_key = f"{category.value}::{affected}::{finding.source_id}"

            # Attempt to construct concrete ProposedPatch for supported operations
            patches = self._generate_patches_for_finding(finding, category)

            # If no patch could be constructed for an autonomous candidate, escalate to APPROVAL_REQUIRED or MANUAL
            if not patches and disposition == ExecutionDisposition.AUTONOMOUS_CANDIDATE:
                disposition = ExecutionDisposition.APPROVAL_REQUIRED

            # Approval is required if risk is not LOW or if explicitly required
            approval_required = (risk_level != RepairRiskLevel.LOW) or (disposition != ExecutionDisposition.AUTONOMOUS_CANDIDATE)

            task = RepairTask(
                repair_id=self._next_task_id(),
                source_finding_ids=[finding.stable_id, finding.source_id],
                title=f"Repair {category.value.lower().replace('_', ' ')} in {affected}",
                description=finding.description,
                category=category,
                severity=finding.severity,
                confidence=finding.confidence,
                risk_level=risk_level,
                affected_files=finding.affected_files,
                proposed_changes=patches,
                expected_benefit=f"Resolves {finding.description} safely under evidence validation.",
                potential_side_effects="Low impact bounded modification." if risk_level == RepairRiskLevel.LOW else "Requires human review of behavioral side effects.",
                dependencies=[],
                approval_required=approval_required,
                validation_commands=finding.validation_requirements or ["local_syntax_check"],
                rollback_strategy="Restore verified original file from repair backup.",
                estimated_scope="LINE" if any(p.patch_type == "text_replace" for p in patches) else "FILE",
                priority=priority,
                disposition=disposition,
                status=RepairStatus.REPAIR_PLANNED,
                root_cause_key=root_cause_key,
            )
            tasks.append(task)

        # Sort deterministically by priority, risk level, and ID
        tasks.sort(key=lambda t: (t.priority, t.risk_level.value, t.repair_id))
        return tasks

    def _generate_patches_for_finding(
        self, finding: NormalizedFinding, category: RepairCategory
    ) -> List[ProposedPatch]:
        patches: List[ProposedPatch] = []
        desc = finding.description
        remed = finding.proposed_remediation

        # 1. Missing .gitignore rule
        if category in (RepairCategory.SAFE_CONFIGURATION_CORRECTION, RepairCategory.MISSING_CONFIGURATION):
            if ".gitignore missing rule for" in desc:
                m = re.search(r"missing rule for '([^']+)'", desc)
                if m:
                    rule = m.group(1)
                    patch = self.patch_gen.generate_gitignore_rule_patch(rule)
                    patches.append(patch)
            elif "Missing .gitignore file" in desc:
                patch = self.patch_gen.generate_gitignore_rule_patch(".env\n*.key\n*.pem\nnode_modules/\n.venv/\n")
                patches.append(patch)

        # 2. Documentation link or command correction
        elif category in (RepairCategory.DOCUMENTATION_CORRECTION, RepairCategory.README_IMPROVEMENT):
            # Check if affected file exists
            if finding.affected_files:
                fpath = finding.affected_files[0]
                full_path = self.target_dir / fpath
                if full_path.is_file():
                    # Check for explicit broken link replacement
                    link_match = re.search(r"replace '([^']+)' with '([^']+)'", remed, re.IGNORECASE)
                    if link_match:
                        target_t = link_match.group(1)
                        replace_t = link_match.group(2)
                        p = self.patch_gen.generate_exact_text_patch(fpath, target_t, replace_t)
                        if p:
                            patches.append(p)
                    # Check for command replacement
                    cmd_match = re.search(r"command '([^']+)' to '([^']+)'", remed, re.IGNORECASE)
                    if cmd_match:
                        target_t = cmd_match.group(1)
                        replace_t = cmd_match.group(2)
                        p = self.patch_gen.generate_exact_text_patch(fpath, target_t, replace_t)
                        if p:
                            patches.append(p)

        return patches

