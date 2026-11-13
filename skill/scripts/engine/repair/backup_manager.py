"""Module F — Backup and Recovery Manager for RepoCraft Phase 4.

Creates and verifies backups for RepoCraft-owned file modifications:
- External backup storage outside target project
- Verification of backup integrity (SHA256 comparison)
- Non-destructive backup preservation (never silently overwrites backups)
- Records original and post-change file hashes
"""
from __future__ import annotations

import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .patch_generator import sha256_of_file
from .repair_types import BackupRecord


class BackupManager:
    """Manages creation, verification, and retrieval of pre-repair file backups."""

    def __init__(self, backup_dir: str):
        self.backup_dir = Path(backup_dir).resolve()
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.records: Dict[str, BackupRecord] = {}

    def create_backup(self, target_dir: str, repair_id: str, file_rel_path: str) -> Tuple[Optional[BackupRecord], str]:
        """Create a verified backup of an existing target file before repair."""
        root = Path(target_dir).resolve()
        source_path = root / file_rel_path
        clean_rel = file_rel_path.replace("\\", "/").lstrip("./")

        # If file does not exist yet (e.g. file_create patch), no pre-existing content to back up
        if not source_path.is_file():
            record = BackupRecord(
                repair_id=repair_id,
                file_path=clean_rel,
                backup_path="",
                original_sha256="",
                post_change_sha256=None,
                timestamp=datetime.now(timezone.utc).isoformat(),
            )
            self.records[f"{repair_id}::{clean_rel}"] = record
            return record, "File did not pre-exist (creation patch)."

        # Target destination in backup directory
        dest_path = self.backup_dir / repair_id / clean_rel
        if dest_path.exists():
            return None, f"Backup destination '{dest_path}' already exists. Refusing to overwrite existing backup."

        dest_path.parent.mkdir(parents=True, exist_ok=True)

        # Compute original hash
        original_hash = sha256_of_file(source_path)
        if original_hash is None:
            return None, f"Could not read source file '{source_path}' for hashing."

        # Copy file preserving metadata
        try:
            shutil.copy2(source_path, dest_path)
        except Exception as exc:
            return None, f"Failed to copy file to backup location: {str(exc)}"

        # Verify backup integrity
        backup_hash = sha256_of_file(dest_path)
        if backup_hash != original_hash:
            # Corrupted copy
            try:
                dest_path.unlink()
            except Exception:
                pass
            return None, "Backup verification failed: SHA256 checksum mismatch after copy."

        record = BackupRecord(
            repair_id=repair_id,
            file_path=clean_rel,
            backup_path=str(dest_path),
            original_sha256=original_hash,
            post_change_sha256=None,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        self.records[f"{repair_id}::{clean_rel}"] = record
        return record, f"Backup created and verified at {dest_path}"

    def update_post_change_hash(self, repair_id: str, file_rel_path: str, new_hash: str) -> None:
        """Record the post-change hash after RepoCraft modifies the file."""
        clean_rel = file_rel_path.replace("\\", "/").lstrip("./")
        key = f"{repair_id}::{clean_rel}"
        if key in self.records:
            self.records[key].post_change_sha256 = new_hash

    def get_backup_record(self, repair_id: str, file_rel_path: str) -> Optional[BackupRecord]:
        """Retrieve backup record for a repair and file."""
        clean_rel = file_rel_path.replace("\\", "/").lstrip("./")
        return self.records.get(f"{repair_id}::{clean_rel}")

    def verify_backup_integrity(self, record: BackupRecord) -> bool:
        """Verify that the backup file still exists and matches original hash."""
        if not record.backup_path:
            # Creation patch with no previous content
            return True
        p = Path(record.backup_path)
        if not p.is_file():
            return False
        return sha256_of_file(p) == record.original_sha256

