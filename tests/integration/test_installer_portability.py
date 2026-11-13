"""Tests 47-58: Installer portability, clean install, backup recovery, and path safety."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def test_47_clean_installation(tmp_path: Path):
    """Test clean install via install.py."""
    target = tmp_path / "project"
    target.mkdir()

    cmd = [
        sys.executable, str(REPO_ROOT / "install.py"),
        "--source", str(REPO_ROOT),
        "--agent", "antigravity",
        "--target", str(target),
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, check=False)
    assert res.returncode == 0
    dest = target / ".agent" / "skills" / "repocraft"
    assert (dest / "SKILL.md").is_file()
    assert (dest / "INSTALL-MANIFEST.json").is_file()
    manifest = json.loads((dest / "INSTALL-MANIFEST.json").read_text(encoding="utf-8"))
    assert manifest["version"] == "1.0.0-rc1"


def test_48_existing_directory_protection(tmp_path: Path):
    """Verify existing installation is not overwritten without --force."""
    target = tmp_path / "project"
    dest = target / ".agent" / "skills" / "repocraft"
    dest.mkdir(parents=True)
    user_file = dest / "custom_user_file.txt"
    user_file.write_text("pre-existing content", encoding="utf-8")

    cmd = [
        sys.executable, str(REPO_ROOT / "install.py"),
        "--source", str(REPO_ROOT),
        "--agent", "antigravity",
        "--target", str(target),
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, check=False)
    assert res.returncode == 3
    assert user_file.read_text(encoding="utf-8") == "pre-existing content"


def test_49_force_installation_backup(tmp_path: Path):
    """Verify --force creates backup directory before replacing."""
    target = tmp_path / "project"
    dest = target / ".agent" / "skills" / "repocraft"
    dest.mkdir(parents=True)
    (dest / "keep.txt").write_text("important user backup data", encoding="utf-8")

    cmd = [
        sys.executable, str(REPO_ROOT / "install.py"),
        "--source", str(REPO_ROOT),
        "--agent", "antigravity",
        "--target", str(target),
        "--force",
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, check=False)
    assert res.returncode == 0

    backup_dir = target / ".agent" / "skills" / "repocraft.backup"
    assert backup_dir.is_dir()
    assert (backup_dir / "keep.txt").read_text(encoding="utf-8") == "important user backup data"


def test_50_install_path_with_spaces(tmp_path: Path):
    """Verify installation works into directories with spaces in path name."""
    target = tmp_path / "project with spaces"
    target.mkdir()

    cmd = [
        sys.executable, str(REPO_ROOT / "install.py"),
        "--source", str(REPO_ROOT),
        "--agent", "antigravity",
        "--target", str(target),
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, check=False)
    assert res.returncode == 0
    assert (target / ".agent" / "skills" / "repocraft" / "SKILL.md").is_file()


def test_51_install_path_with_unicode(tmp_path: Path):
    """Verify installation works into unicode path directories."""
    target = tmp_path / "proyecto_ñ_🚀"
    target.mkdir()

    cmd = [
        sys.executable, str(REPO_ROOT / "install.py"),
        "--source", str(REPO_ROOT),
        "--agent", "antigravity",
        "--target", str(target),
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, check=False)
    assert res.returncode == 0
    assert (target / ".agent" / "skills" / "repocraft" / "SKILL.md").is_file()


def test_52_missing_source_files_error(tmp_path: Path):
    """Verify error exit code 2 when required files are missing in source."""
    empty_src = tmp_path / "empty_src"
    empty_src.mkdir()
    (empty_src / "skill").mkdir()

    cmd = [
        sys.executable, str(REPO_ROOT / "install.py"),
        "--source", str(empty_src),
        "--agent", "antigravity",
        "--target", str(tmp_path),
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, check=False)
    assert res.returncode == 2
    assert "missing" in res.stderr.lower()


def test_53_installed_cli_help(tmp_path: Path):
    """Verify all CLI scripts in installed skill run --help without error."""
    target = tmp_path / "project"
    target.mkdir()

    subprocess.run(
        [sys.executable, str(REPO_ROOT / "install.py"), "--source", str(REPO_ROOT), "--target", str(target)],
        check=True,
    )
    installed_scripts = target / ".agent" / "skills" / "repocraft" / "scripts"

    scripts_to_test = [
        "repocraft_intel.py",
        "repocraft_maintenance.py",
        "repocraft_security.py",
        "repocraft_repair.py",
        "repocraft_git.py",
        "repocraft_status.py",
    ]
    for s in scripts_to_test:
        s_path = installed_scripts / s
        res = subprocess.run([sys.executable, str(s_path), "--help"], capture_output=True, text=True)
        assert res.returncode == 0, f"Script {s} --help failed: {res.stderr}"


def test_53b_reinstall_same_files_with_force(tmp_path: Path):
    """Verify reinstallation succeeds when --force is supplied."""
    target = tmp_path / "project"
    target.mkdir()

    cmd = [sys.executable, str(REPO_ROOT / "install.py"), "--source", str(REPO_ROOT), "--target", str(target)]
    subprocess.run(cmd, check=True)

    # Reinstall with force
    cmd_force = cmd + ["--force"]
    res = subprocess.run(cmd_force, capture_output=True, text=True, check=False)
    assert res.returncode == 0
    assert (target / ".agent" / "skills" / "repocraft" / "SKILL.md").is_file()


def test_53c_installer_excludes_tests(tmp_path: Path):
    """Verify install.py copies only skill/ and not tests/ or .git/ into target."""
    target = tmp_path / "project"
    target.mkdir()

    subprocess.run([sys.executable, str(REPO_ROOT / "install.py"), "--source", str(REPO_ROOT), "--target", str(target)], check=True)
    dest = target / ".agent" / "skills" / "repocraft"
    assert not (dest / "tests").exists()
    assert not (dest / ".git").exists()


def test_53d_installed_files_sha256_match_manifest(tmp_path: Path):
    """Verify SHA-256 hashes recorded in INSTALL-MANIFEST.json match actual files."""
    import hashlib
    target = tmp_path / "project"
    target.mkdir()

    subprocess.run([sys.executable, str(REPO_ROOT / "install.py"), "--source", str(REPO_ROOT), "--target", str(target)], check=True)
    dest = target / ".agent" / "skills" / "repocraft"
    manifest = json.loads((dest / "INSTALL-MANIFEST.json").read_text(encoding="utf-8"))

    for rel_path, expected_hash in manifest["files"].items():
        if rel_path == "INSTALL-MANIFEST.json":
            continue
        file_path = dest / rel_path
        assert file_path.is_file()
        actual_hash = hashlib.sha256(file_path.read_bytes()).hexdigest()
        assert actual_hash == expected_hash, f"Hash mismatch for {rel_path}"

