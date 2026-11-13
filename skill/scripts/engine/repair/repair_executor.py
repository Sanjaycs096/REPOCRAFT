"""Module G — Safe Repair Executor for RepoCraft Phase 4.

Applies bounded, policy-permitted patches to target project files under strict safety checks:
- Verifies ChangeGuard preconditions before modification
- Creates and verifies backups before touching files
- Applies deterministic text replacements or file creations
- Records post-change SHA256 hashes
- Strictly prevents unauthorized operations (deletions, license overwrites, unapproved security changes)
"""
from __future__ import annotations

from pathlib import Path
from typing import List, Optional, Tuple

from .backup_manager import BackupManager
from .change_guard import ChangeGuard
from .patch_generator import sha256_of_file, sha256_of_text
from .repair_types import ProposedPatch, RepairCategory, RepairRiskLevel, RepairStatus, RepairTask


class RepairExecutor:
    """Executes validated and authorized repair tasks."""

    def __init__(self, target_dir: str, backup_manager: BackupManager, change_guard: ChangeGuard):
        self.target_dir = Path(target_dir).resolve()
        self.backup_mgr = backup_manager
        self.change_guard = change_guard

    def execute_task(self, task: RepairTask, is_approved: bool) -> Tuple[bool, str, List[str]]:
        """Apply all patches in a RepairTask.

        Returns:
            (success, message, modified_files)
        """
        # 1. Authorization check
        if task.approval_required and not is_approved:
            task.status = RepairStatus.REPAIR_BLOCKED
            return False, f"Task '{task.repair_id}' requires explicit approval before execution.", []

        # 2. Strict policy boundaries (Forbidden categories first)
        if task.category == RepairCategory.LICENSE_AND_LEGAL:
            task.status = RepairStatus.REPAIR_BLOCKED
            return False, "Automatic selection or modification of licenses is strictly forbidden.", []

        if task.category == RepairCategory.DEAD_CODE_REVIEW:
            task.status = RepairStatus.REPAIR_BLOCKED
            return False, "Automatic deletion of unused file candidates is strictly forbidden.", []

        if task.risk_level == RepairRiskLevel.CRITICAL:
            task.status = RepairStatus.REPAIR_BLOCKED
            return False, f"CRITICAL risk task '{task.repair_id}' cannot be executed automatically.", []

        # 3. ChangeGuard validation
        can_run, guard_reason = self.change_guard.validate_task_safety(task)
        if not can_run:
            task.status = RepairStatus.REPAIR_BLOCKED
            return False, f"Change guard rejected task '{task.repair_id}': {guard_reason}", []

        # 4. Check that task has concrete patches
        if not task.proposed_changes:
            task.status = RepairStatus.REPAIR_BLOCKED
            return False, f"Task '{task.repair_id}' does not have any executable patches.", []

        modified_files: List[str] = []

        # 5. Create backups for all affected files
        for patch in task.proposed_changes:
            backup_rec, backup_msg = self.backup_mgr.create_backup(
                str(self.target_dir), task.repair_id, patch.file_path
            )
            if backup_rec is None:
                task.status = RepairStatus.REPAIR_BLOCKED
                return False, f"Pre-repair backup failed for '{patch.file_path}': {backup_msg}", modified_files

        # 6. Apply patches
        for patch in task.proposed_changes:
            full_path = self.target_dir / patch.file_path

            if patch.patch_type == "text_replace":
                if not full_path.is_file():
                    task.status = RepairStatus.REPAIR_BLOCKED
                    return False, f"Target file '{patch.file_path}' does not exist for text replacement.", modified_files

                content = full_path.read_text(encoding="utf-8", errors="replace")

                # Verify original hash
                if patch.original_content_hash and sha256_of_text(content) != patch.original_content_hash:
                    task.status = RepairStatus.REPAIR_BLOCKED
                    return False, f"File '{patch.file_path}' content hash mismatch before patch application.", modified_files

                if patch.target_text:
                    if patch.target_text not in content:
                        task.status = RepairStatus.REPAIR_BLOCKED
                        return False, f"Target string not found in '{patch.file_path}'.", modified_files
                    new_content = content.replace(patch.target_text, patch.replacement_text or "")
                elif patch.full_content:
                    new_content = patch.full_content
                else:
                    task.status = RepairStatus.REPAIR_BLOCKED
                    return False, f"Invalid text_replace patch without target_text or full_content in '{patch.file_path}'.", modified_files

                full_path.write_text(new_content, encoding="utf-8")
                new_hash = sha256_of_text(new_content)
                self.backup_mgr.update_post_change_hash(task.repair_id, patch.file_path, new_hash)
                modified_files.append(patch.file_path)

            elif patch.patch_type == "file_create":
                if full_path.is_file():
                    task.status = RepairStatus.REPAIR_BLOCKED
                    return False, f"File '{patch.file_path}' already exists; cannot execute file_create patch.", modified_files

                full_path.parent.mkdir(parents=True, exist_ok=True)
                new_content = patch.full_content or ""
                full_path.write_text(new_content, encoding="utf-8")
                new_hash = sha256_of_text(new_content)
                self.backup_mgr.update_post_change_hash(task.repair_id, patch.file_path, new_hash)
                modified_files.append(patch.file_path)

            else:
                task.status = RepairStatus.REPAIR_BLOCKED
                return False, f"Unsupported patch type '{patch.patch_type}' in '{patch.file_path}'.", modified_files

        task.status = RepairStatus.REPAIR_APPLIED
        return True, f"Successfully applied {len(modified_files)} patch(es) for task '{task.repair_id}'.", modified_files
