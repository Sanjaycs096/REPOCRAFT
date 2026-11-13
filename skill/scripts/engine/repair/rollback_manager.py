"""Module K — Rollback Manager for RepoCraft Phase 4.

Safely rolls back RepoCraft-owned modifications from verified backups:
- Verifies post-change SHA256 before restoring
- Prevents overwriting user modifications made after RepoCraft's repair (ROLLBACK_BLOCKED_USER_MODIFICATION)
- Restores original file from backup and verifies original SHA256
- Removes newly created files if file did not exist prior to repair
- Generates rollback report
"""
from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .backup_manager import BackupManager
from .patch_generator import sha256_of_file
from .repair_types import BackupRecord, RollbackState


class RollbackManager:
    """Executes safe, verified rollbacks of RepoCraft modifications."""

    def __init__(self, target_dir: str, backup_manager: BackupManager):
        self.target_dir = Path(target_dir).resolve()
        self.backup_mgr = backup_manager
        self.rollback_history: List[Dict[str, Any]] = []

    def rollback_repair(self, repair_id: str, affected_files: List[str], reason: str) -> Dict[str, Any]:
        """Roll back all files modified by a specific repair task."""
        results: Dict[str, Any] = {
            "repair_id": repair_id,
            "reason": reason,
            "overall_state": RollbackState.ROLLBACK_COMPLETED.value,
            "file_outcomes": {},
        }

        all_success = True

        for file_rel in affected_files:
            clean_rel = file_rel.replace("\\", "/").lstrip("./")
            record = self.backup_mgr.get_backup_record(repair_id, clean_rel)
            target_path = self.target_dir / clean_rel

            # 1. Check if backup record exists
            if not record:
                results["file_outcomes"][clean_rel] = {
                    "state": RollbackState.ROLLBACK_BACKUP_MISSING.value,
                    "reason": "No backup record found for this file and repair.",
                }
                all_success = False
                continue

            # 2. Check if file did not pre-exist (created by RepoCraft)
            if not record.original_sha256:
                if target_path.is_file():
                    # Check if user edited the created file
                    curr_hash = sha256_of_file(target_path)
                    if record.post_change_sha256 and curr_hash != record.post_change_sha256:
                        results["file_outcomes"][clean_rel] = {
                            "state": RollbackState.ROLLBACK_BLOCKED_USER_MODIFICATION.value,
                            "reason": "File was edited by user after creation. Rollback blocked to protect user modifications.",
                        }
                        all_success = False
                        continue

                    # Safe to delete newly created file
                    try:
                        target_path.unlink()
                        results["file_outcomes"][clean_rel] = {
                            "state": RollbackState.ROLLBACK_COMPLETED.value,
                            "reason": "Newly created file removed cleanly.",
                        }
                    except Exception as exc:
                        results["file_outcomes"][clean_rel] = {
                            "state": RollbackState.ROLLBACK_FAILED.value,
                            "reason": f"Failed to delete created file: {str(exc)}",
                        }
                        all_success = False
                else:
                    results["file_outcomes"][clean_rel] = {
                        "state": RollbackState.ROLLBACK_NOT_REQUIRED.value,
                        "reason": "File already absent.",
                    }
                continue

            # 3. Check backup file existence
            backup_file = Path(record.backup_path)
            if not backup_file.is_file():
                results["file_outcomes"][clean_rel] = {
                    "state": RollbackState.ROLLBACK_BACKUP_MISSING.value,
                    "reason": f"Backup file '{record.backup_path}' is missing.",
                }
                all_success = False
                continue

            # 4. Check if user modified the file after RepoCraft applied repair
            if target_path.is_file():
                current_hash = sha256_of_file(target_path)
                if record.post_change_sha256 and current_hash != record.post_change_sha256:
                    # User modified file after repair!
                    results["file_outcomes"][clean_rel] = {
                        "state": RollbackState.ROLLBACK_BLOCKED_USER_MODIFICATION.value,
                        "reason": f"File '{clean_rel}' has been modified by user after RepoCraft repair (current hash {current_hash[:10]}... != post-repair {record.post_change_sha256[:10]}...). Rollback blocked to prevent data loss.",
                    }
                    all_success = False
                    continue

            # 5. Restore file from backup
            try:
                shutil.copy2(backup_file, target_path)
                # Verify original hash
                restored_hash = sha256_of_file(target_path)
                if restored_hash != record.original_sha256:
                    results["file_outcomes"][clean_rel] = {
                        "state": RollbackState.ROLLBACK_FAILED.value,
                        "reason": "Restored file hash does not match original pre-repair hash.",
                    }
                    all_success = False
                else:
                    results["file_outcomes"][clean_rel] = {
                        "state": RollbackState.ROLLBACK_COMPLETED.value,
                        "reason": "Original file content successfully restored and verified.",
                    }
            except Exception as exc:
                results["file_outcomes"][clean_rel] = {
                    "state": RollbackState.ROLLBACK_FAILED.value,
                    "reason": f"Exception restoring file: {str(exc)}",
                }
                all_success = False

        if not all_success:
            # If any file was blocked or failed, set overall state
            any_blocked = any(
                f["state"] == RollbackState.ROLLBACK_BLOCKED_USER_MODIFICATION.value
                for f in results["file_outcomes"].values()
            )
            results["overall_state"] = (
                RollbackState.ROLLBACK_BLOCKED_USER_MODIFICATION.value
                if any_blocked
                else RollbackState.ROLLBACK_FAILED.value
            )

        self.rollback_history.append(results)
        return results

