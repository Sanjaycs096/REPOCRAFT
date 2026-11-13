"""Module D — Approval Manager for RepoCraft Phase 4.

Enforces explicit human authorization boundaries:
- Generates approval-manifest.json
- Verifies explicit per-repair approval before execution
- Validates that approval matches the exact repair ID and unchanged patch hash
- Rejects missing approval, mismatched IDs, and invalid general permissions
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .patch_generator import sha256_of_text
from .repair_types import RepairRiskLevel, RepairTask


class ApprovalManager:
    """Manages generation, storage, and validation of repair approvals."""

    def __init__(self, approval_file: Optional[str] = None):
        self.approval_file = Path(approval_file).resolve() if approval_file else None
        self._approvals_cache: Optional[Dict[str, Any]] = None

    def _load_approvals(self) -> Dict[str, Any]:
        if self._approvals_cache is not None:
            return self._approvals_cache
        if not self.approval_file or not self.approval_file.is_file():
            self._approvals_cache = {}
            return self._approvals_cache
        try:
            content = self.approval_file.read_text(encoding="utf-8", errors="replace")
            data = json.loads(content)
            self._approvals_cache = data if isinstance(data, dict) else {}
        except Exception:
            self._approvals_cache = {}
        return self._approvals_cache

    def generate_manifest(self, tasks: List[RepairTask], output_path: Path) -> Path:
        """Generate approval-manifest.json containing all tasks and their approval status."""
        manifest_data: Dict[str, Any] = {
            "version": "1.0",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "tasks": [],
        }

        for t in tasks:
            patch_hashes = [p.new_content_hash or "" for p in t.proposed_changes]
            combined_hash = sha256_of_text("::".join(patch_hashes))

            task_entry = {
                "repair_id": t.repair_id,
                "title": t.title,
                "description": t.description,
                "category": t.category.value,
                "risk_level": t.risk_level.value,
                "affected_files": t.affected_files,
                "proposed_changes_summary": [p.diff_or_description for p in t.proposed_changes],
                "expected_patch_hash": combined_hash,
                "approval_required": t.approval_required,
                "approved": False if t.approval_required else True,
                "approved_by": None if t.approval_required else "system_autonomous_policy",
                "approval_timestamp": None if t.approval_required else datetime.now(timezone.utc).isoformat(),
            }
            manifest_data["tasks"].append(task_entry)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(manifest_data, indent=2) + "\n", encoding="utf-8")
        return output_path

    def is_repair_approved(self, task: RepairTask) -> Tuple[bool, str]:
        """Verify whether a specific repair task has received valid authorization."""
        # 1. Low-risk tasks that do not require approval
        if not task.approval_required and task.risk_level == RepairRiskLevel.LOW:
            return True, "Autonomous low-risk repair permitted by policy."

        # 2. Critical risk repairs can NEVER be executed automatically or via general approval
        if task.risk_level == RepairRiskLevel.CRITICAL:
            return False, "CRITICAL risk repairs are strictly prohibited from autonomous/batch execution."

        # 3. Check approval manifest presence
        if not self.approval_file or not self.approval_file.is_file():
            return False, f"Approval manifest file is missing or not provided for {task.repair_id}."

        approvals_data = self._load_approvals()
        tasks_list = approvals_data.get("tasks", [])
        if isinstance(tasks_list, dict):
            # If tasks is a dict keyed by repair_id
            entry = tasks_list.get(task.repair_id)
        else:
            entry = next((item for item in tasks_list if isinstance(item, dict) and item.get("repair_id") == task.repair_id), None)

        if not entry:
            return False, f"Repair ID '{task.repair_id}' not found in approval manifest."

        if not entry.get("approved"):
            return False, f"Repair '{task.repair_id}' is marked unapproved or pending approval."

        # 4. Check for patch integrity / hash invalidation
        task_combined_hash = sha256_of_text("::".join(p.new_content_hash or "" for p in task.proposed_changes))
        expected_hash = entry.get("expected_patch_hash")
        if expected_hash and expected_hash != task_combined_hash:
            return False, f"Approval invalidated: proposed patch for '{task.repair_id}' has changed since approval."

        return True, f"Explicit approval verified for '{task.repair_id}' by {entry.get('approved_by', 'user')}."
