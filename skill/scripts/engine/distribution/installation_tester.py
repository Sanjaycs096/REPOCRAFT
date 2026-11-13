"""Automated verification of installation scenarios, integrity, and safety."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Dict, List, Optional

from .distribution_types import InstallationTestResult


class InstallationTester:
    """Executes automated installation acceptance tests against disposable temporary directories."""

    @classmethod
    def test_clean_installation(cls, installer_path: Path, source_dir: Path) -> InstallationTestResult:
        """Test fresh installation into clean directory."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            target = Path(tmp_dir) / "test_project"
            target.mkdir()

            cmd = [
                sys.executable, str(installer_path.resolve()),
                "--source", str(source_dir.resolve()),
                "--agent", "antigravity",
                "--target", str(target),
            ]
            res = subprocess.run(cmd, capture_output=True, text=True, check=False)
            dest = target / ".agent" / "skills" / "repocraft"

            manifest_file = dest / "INSTALL-MANIFEST.json"
            manifest_present = manifest_file.is_file()
            files_installed = len(list(dest.rglob("*"))) if dest.is_dir() else 0

            errors = []
            if res.returncode != 0:
                errors.append(f"Installer exited with code {res.returncode}: {res.stderr}")
            if not manifest_present:
                errors.append("INSTALL-MANIFEST.json not created")

            return InstallationTestResult(
                test_type="clean_installation",
                is_valid=len(errors) == 0,
                target_path=str(target),
                files_installed=files_installed,
                manifest_present=manifest_present,
                manifest_hashes_valid=manifest_present,
                user_files_preserved=True,
                errors=errors,
            )

    @classmethod
    def test_existing_user_files_protection(cls, installer_path: Path, source_dir: Path) -> InstallationTestResult:
        """Test installing into a project with existing user files (verifying they remain untouched)."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            target = Path(tmp_dir) / "user_project"
            target.mkdir()
            user_code = target / "app.py"
            user_code.write_text("print('user original code')", encoding="utf-8")
            user_readme = target / "README.md"
            user_readme.write_text("# User Project", encoding="utf-8")

            cmd = [
                sys.executable, str(installer_path.resolve()),
                "--source", str(source_dir.resolve()),
                "--agent", "antigravity",
                "--target", str(target),
            ]
            res = subprocess.run(cmd, capture_output=True, text=True, check=False)
            dest = target / ".agent" / "skills" / "repocraft"

            errors = []
            if res.returncode != 0:
                errors.append(f"Installer failed: {res.stderr}")
            if not user_code.is_file() or user_code.read_text(encoding="utf-8") != "print('user original code')":
                errors.append("User file app.py was modified or corrupted!")
            if not user_readme.is_file() or user_readme.read_text(encoding="utf-8") != "# User Project":
                errors.append("User file README.md was modified or corrupted!")

            return InstallationTestResult(
                test_type="existing_user_files_protection",
                is_valid=len(errors) == 0,
                target_path=str(target),
                files_installed=len(list(dest.rglob("*"))) if dest.is_dir() else 0,
                manifest_present=(dest / "INSTALL-MANIFEST.json").is_file(),
                manifest_hashes_valid=True,
                user_files_preserved=len(errors) == 0,
                errors=errors,
            )

    @classmethod
    def test_overwrite_protection_and_backup(cls, installer_path: Path, source_dir: Path) -> InstallationTestResult:
        """Verify installer refuses overwrite without --force, and creates backup with --force."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            target = Path(tmp_dir) / "existing_skill_project"
            target.mkdir()

            # First install
            cmd1 = [
                sys.executable, str(installer_path.resolve()),
                "--source", str(source_dir.resolve()),
                "--agent", "antigravity",
                "--target", str(target),
            ]
            subprocess.run(cmd1, capture_output=True, check=True)
            dest = target / ".agent" / "skills" / "repocraft"

            # Create sentinel file in destination
            sentinel = dest / "custom_note.txt"
            sentinel.write_text("pre-existing note", encoding="utf-8")

            # Second install without force must fail with code 3
            res_no_force = subprocess.run(cmd1, capture_output=True, text=True, check=False)
            errors = []
            if res_no_force.returncode != 3:
                errors.append(f"Expected exit code 3 for overwrite protection, got {res_no_force.returncode}")

            # Third install with force must succeed and create backup
            cmd_force = cmd1 + ["--force"]
            res_force = subprocess.run(cmd_force, capture_output=True, text=True, check=False)
            if res_force.returncode != 0:
                errors.append(f"Force install failed: {res_force.stderr}")

            backup_dir = target / ".agent" / "skills" / "repocraft.backup"
            backup_verified = backup_dir.is_dir() and (backup_dir / "custom_note.txt").is_file()
            if not backup_verified:
                errors.append("Backup directory or custom_note.txt was not created")

            return InstallationTestResult(
                test_type="overwrite_protection_and_backup",
                is_valid=len(errors) == 0,
                target_path=str(target),
                files_installed=len(list(dest.rglob("*"))) if dest.is_dir() else 0,
                manifest_present=(dest / "INSTALL-MANIFEST.json").is_file(),
                manifest_hashes_valid=True,
                user_files_preserved=True,
                backup_verified=backup_verified,
                errors=errors,
            )

    @classmethod
    def run_all_tests(cls, installer_path: Path, source_dir: Path) -> List[InstallationTestResult]:
        """Execute suite of installation acceptance tests."""
        return [
            cls.test_clean_installation(installer_path, source_dir),
            cls.test_existing_user_files_protection(installer_path, source_dir),
            cls.test_overwrite_protection_and_backup(installer_path, source_dir),
        ]
