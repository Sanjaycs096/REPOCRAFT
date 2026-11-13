"""Tests for installation acceptance, user file preservation, upgrades, and rollbacks."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from engine.distribution.distribution_types import UpgradeStatus
from engine.distribution.installation_tester import InstallationTester
from engine.distribution.upgrade_manager import UpgradeManager


REPO_ROOT = Path(__file__).resolve().parent.parent.parent
INSTALLER = REPO_ROOT / "install.py"
SKILL_DIR = REPO_ROOT / "skill"


def test_scenario_04_clean_installation_acceptance(tmp_path: Path):
    """Scenario 4: Clean installation acceptance test (clean target, all files verified)."""
    result = InstallationTester.test_clean_installation(INSTALLER, REPO_ROOT)

    assert result.is_valid is True
    assert result.manifest_present is True
    assert result.files_installed > 10
    assert len(result.errors) == 0


def test_scenario_05_preserved_user_files(tmp_path: Path):
    """Scenario 5: Preserved user files during installation (non-destructive)."""
    result = InstallationTester.test_existing_user_files_protection(INSTALLER, REPO_ROOT)

    assert result.is_valid is True
    assert result.user_files_preserved is True
    assert len(result.errors) == 0


def test_scenario_06_backup_creation_on_force_install(tmp_path: Path):
    """Scenario 6: Backup creation before overwrite / upgrade."""
    result = InstallationTester.test_overwrite_protection_and_backup(INSTALLER, REPO_ROOT)

    assert result.is_valid is True
    assert len(result.errors) == 0


def test_scenario_07_upgrade_from_previous_version(tmp_path: Path):
    """Scenario 7: Upgrade from previous version (e.g. v0.5.0 fixture to v1.0.0-rc1)."""
    target = tmp_path / "project"
    skill_dest = target / ".agent" / "skills" / "repocraft"
    skill_dest.mkdir(parents=True)

    # Simulate installed v0.5.0
    (skill_dest / "SKILL.md").write_text("# RepoCraft v0.5.0\n", encoding="utf-8")
    (skill_dest / "INSTALL-MANIFEST.json").write_text(
        json.dumps({"name": "RepoCraft", "version": "0.5.0", "files": {"SKILL.md": "abc"}}),
        encoding="utf-8",
    )

    plan = UpgradeManager.plan_upgrade(target, SKILL_DIR, candidate_version="1.0.0-rc1")
    assert plan.current_version == "0.5.0"
    assert plan.candidate_version == "1.0.0-rc1"
    assert plan.upgrade_status == UpgradeStatus.UPGRADE_AVAILABLE
    assert plan.can_proceed is True

    receipt = UpgradeManager.execute_upgrade(target, SKILL_DIR, candidate_version="1.0.0-rc1")
    assert receipt.status == UpgradeStatus.UPGRADED
    assert receipt.from_version == "0.5.0"
    assert receipt.to_version == "1.0.0-rc1"
    assert receipt.backup_path is not None
    assert Path(receipt.backup_path).is_dir()
    assert (Path(receipt.backup_path) / "SKILL.md").read_text(encoding="utf-8") == "# RepoCraft v0.5.0\n"


def test_scenario_08_upgrade_verification_against_manifest(tmp_path: Path):
    """Scenario 8: Upgrade verification against manifest."""
    target = tmp_path / "project"
    skill_dest = target / ".agent" / "skills" / "repocraft"
    skill_dest.mkdir(parents=True)

    # Initial install
    receipt = UpgradeManager.execute_upgrade(target, SKILL_DIR, candidate_version="1.0.0-rc1")
    assert receipt.status == UpgradeStatus.UPGRADED

    # Verify via install.py --verify
    res = subprocess.run(
        [sys.executable, str(INSTALLER), "--target", str(target), "--verify"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert res.returncode == 0
    assert "verification passed" in res.stdout.lower()


def test_scenario_09_rollback_to_backup_after_failed_upgrade(tmp_path: Path):
    """Scenario 9: Rollback to backup restores original files."""
    target = tmp_path / "project"
    skill_dest = target / ".agent" / "skills" / "repocraft"
    skill_dest.mkdir(parents=True)

    # Old version
    (skill_dest / "SKILL.md").write_text("# RepoCraft Original\n", encoding="utf-8")
    (skill_dest / "INSTALL-MANIFEST.json").write_text(
        json.dumps({"name": "RepoCraft", "version": "0.1.0", "files": {}}),
        encoding="utf-8",
    )

    # Perform upgrade
    receipt = UpgradeManager.execute_upgrade(target, SKILL_DIR, candidate_version="1.0.0-rc1")
    assert (skill_dest / "SKILL.md").read_text(encoding="utf-8") != "# RepoCraft Original\n"

    # Roll back
    rollback_receipt = UpgradeManager.rollback_upgrade(target)
    assert rollback_receipt.status == UpgradeStatus.ROLLBACK_COMPLETED
    assert rollback_receipt.to_version == "0.1.0"
    assert (skill_dest / "SKILL.md").read_text(encoding="utf-8") == "# RepoCraft Original\n"


def test_scenario_10_rollback_rejection_when_no_backup(tmp_path: Path):
    """Scenario 10: Rollback rejection when no backup exists."""
    target = tmp_path / "empty_project"
    target.mkdir()

    receipt = UpgradeManager.rollback_upgrade(target)
    assert receipt.status == UpgradeStatus.ROLLBACK_FAILED
    assert receipt.verification_passed is False
    assert any("no backup directory found" in err.lower() for err in receipt.errors)


def test_installer_cli_upgrade_and_rollback(tmp_path: Path):
    """Test install.py CLI commands: --upgrade, --verify, and --rollback."""
    target = tmp_path / "cli_project"
    target.mkdir()

    # Step 1: Initial install
    cmd_install = [
        sys.executable, str(INSTALLER),
        "--source", str(REPO_ROOT),
        "--agent", "antigravity",
        "--target", str(target),
    ]
    res_inst = subprocess.run(cmd_install, capture_output=True, text=True, check=False)
    assert res_inst.returncode == 0

    # Step 2: Verify installation
    cmd_verify = [sys.executable, str(INSTALLER), "--target", str(target), "--verify"]
    res_ver = subprocess.run(cmd_verify, capture_output=True, text=True, check=False)
    assert res_ver.returncode == 0
    assert "verification passed" in res_ver.stdout.lower()

    # Step 3: Upgrade
    cmd_upgrade = [
        sys.executable, str(INSTALLER),
        "--source", str(REPO_ROOT),
        "--target", str(target),
        "--upgrade",
    ]
    res_upg = subprocess.run(cmd_upgrade, capture_output=True, text=True, check=False)
    assert res_upg.returncode == 0
    assert "repocraft skill upgraded" in res_upg.stdout.lower()

    # Step 4: Rollback
    cmd_rollback = [sys.executable, str(INSTALLER), "--target", str(target), "--rollback"]
    res_roll = subprocess.run(cmd_rollback, capture_output=True, text=True, check=False)
    assert res_roll.returncode == 0
    assert "rollback successful" in res_roll.stdout.lower()
