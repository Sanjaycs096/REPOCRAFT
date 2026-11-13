"""Tests 33-40: Release packaging, manifest generation, and reproducibility."""
from __future__ import annotations

import zipfile
from pathlib import Path
import pytest

from engine.release import (
    ManifestGenerator,
    PackageBuilder,
    ReproducibilityChecker,
    sha256_of_file,
)


def test_33_package_inclusion_exclusion_rules():
    """Verify ManifestGenerator includes runtime files and excludes tests/cache."""
    assert ManifestGenerator.is_packageable(Path("README.md")) is True
    assert ManifestGenerator.is_packageable(Path("MANIFEST.json")) is True
    assert ManifestGenerator.is_packageable(Path("install.py")) is True
    assert ManifestGenerator.is_packageable(Path("skill/SKILL.md")) is True
    assert ManifestGenerator.is_packageable(Path("skill/scripts/repocraft_intel.py")) is True

    # Exclusions
    assert ManifestGenerator.is_packageable(Path("tests/test_git_engine.py")) is False
    assert ManifestGenerator.is_packageable(Path(".git/config")) is False
    assert ManifestGenerator.is_packageable(Path("skill/scripts/__pycache__/something.pyc")) is False
    assert ManifestGenerator.is_packageable(Path(".pytest_cache/v/cache/nodeids")) is False
    assert ManifestGenerator.is_packageable(Path("skill.backup-1/SKILL.md")) is False
    assert ManifestGenerator.is_packageable(Path("PHASE-5-IMPLEMENTATION-REPORT.md")) is False


def test_34_generate_manifest(tmp_path: Path):
    """Verify manifest generation produces valid entries and digests."""
    src = tmp_path / "src"
    src.mkdir()
    (src / "README.md").write_text("# RepoCraft", encoding="utf-8")
    (src / "MANIFEST.json").write_text("{}", encoding="utf-8")
    (src / "install.py").write_text("# installer", encoding="utf-8")
    skill_dir = src / "skill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text("# Skill", encoding="utf-8")

    manifest = ManifestGenerator.generate_manifest(src, version="1.0.0-rc1")
    assert manifest.total_files == 4
    assert "README.md" in manifest.files
    assert "skill/SKILL.md" in manifest.files
    assert manifest.files["README.md"].sha256 != ""
    assert manifest.total_bytes > 0


def test_35_build_zip_archive(tmp_path: Path):
    """Verify PackageBuilder creates valid ZIP archive."""
    src = tmp_path / "src"
    src.mkdir()
    (src / "README.md").write_text("# RepoCraft", encoding="utf-8")
    (src / "install.py").write_text("# installer", encoding="utf-8")
    (src / "pyproject.toml").write_text("[project]\nname='test'", encoding="utf-8")
    (src / "MANIFEST.json").write_text("{}", encoding="utf-8")
    skill_dir = src / "skill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text("# Skill", encoding="utf-8")
    scripts_dir = skill_dir / "scripts"
    scripts_dir.mkdir()
    for s in ["repocraft_intel.py", "repocraft_maintenance.py", "repocraft_security.py", "repocraft_repair.py", "repocraft_git.py", "repocraft_status.py"]:
        (scripts_dir / s).write_text("#!/usr/bin/env python3\n", encoding="utf-8")

    dist = tmp_path / "dist"
    zip_path, manifest = PackageBuilder.build_zip(src, dist, version="1.0.0-rc1")

    assert zip_path.is_file()
    assert zip_path.suffix == ".zip"
    assert manifest.archive_sha256 == sha256_of_file(zip_path)

    with zipfile.ZipFile(zip_path, "r") as zf:
        namelist = zf.namelist()
        assert "README.md" in namelist
        assert "install.py" in namelist
        assert "skill/SKILL.md" in namelist


def test_36_reproducible_package_builds(tmp_path: Path):
    """Verify two independent package builds from the same state are byte-for-byte identical."""
    src = tmp_path / "src"
    src.mkdir()
    (src / "README.md").write_text("# Title\nDeterministic", encoding="utf-8")
    (src / "install.py").write_text("# Code\nprint('hello')", encoding="utf-8")
    (src / "MANIFEST.json").write_text("{}", encoding="utf-8")
    (src / "pyproject.toml").write_text("[project]\nversion='1.0'", encoding="utf-8")
    skill = src / "skill"
    skill.mkdir()
    (skill / "SKILL.md").write_text("# Instructions", encoding="utf-8")

    res = ReproducibilityChecker.check_reproducibility(src, version="1.0.0-rc1")
    assert res.is_reproducible is True
    assert res.inventory_identical is True
    assert res.file_hashes_identical is True
    assert res.byte_for_byte is True
    assert len(res.differences) == 0


def test_36b_package_builder_custom_archive_name(tmp_path: Path):
    """Verify PackageBuilder respects custom archive name."""
    src = tmp_path / "src"
    src.mkdir()
    (src / "README.md").write_text("# Test", encoding="utf-8")
    (src / "install.py").write_text("# installer", encoding="utf-8")
    (src / "MANIFEST.json").write_text("{}", encoding="utf-8")
    (src / "pyproject.toml").write_text("[project]\nname='test'", encoding="utf-8")
    (src / "skill").mkdir()
    (src / "skill" / "SKILL.md").write_text("# Skill", encoding="utf-8")

    dist = tmp_path / "dist"
    custom_name = "custom-dist-candidate.zip"
    zip_path, manifest = PackageBuilder.build_zip(src, dist, version="1.0.0-rc1", archive_name=custom_name)
    assert zip_path.name == custom_name
    assert manifest.archive_name == custom_name


def test_36c_manifest_generator_excludes_coverage_and_ds_store():
    """Verify exclusion of .coverage and .DS_Store."""
    assert ManifestGenerator.is_packageable(Path(".DS_Store")) is False
    assert ManifestGenerator.is_packageable(Path(".coverage")) is False


def test_36d_package_builder_executable_permissions(tmp_path: Path):
    """Verify zip entries for Python scripts have executable bit set."""
    src = tmp_path / "src"
    src.mkdir()
    (src / "README.md").write_text("# Readme", encoding="utf-8")
    (src / "install.py").write_text("# installer", encoding="utf-8")
    (src / "MANIFEST.json").write_text("{}", encoding="utf-8")
    (src / "pyproject.toml").write_text("[project]\nname='test'", encoding="utf-8")
    (src / "skill").mkdir()
    (src / "skill" / "SKILL.md").write_text("# Skill", encoding="utf-8")

    dist = tmp_path / "dist"
    zip_path, _ = PackageBuilder.build_zip(src, dist)
    with zipfile.ZipFile(zip_path, "r") as zf:
        install_info = zf.getinfo("install.py")
        mode = install_info.external_attr >> 16
        assert mode & 0o111 != 0, "install.py should be executable"


def test_36e_package_manifest_total_bytes_and_files(tmp_path: Path):
    """Verify package manifest counts total bytes and total files correctly."""
    src = tmp_path / "src"
    src.mkdir()
    (src / "README.md").write_text("12345", encoding="utf-8")
    (src / "install.py").write_text("67890", encoding="utf-8")
    (src / "MANIFEST.json").write_text("{}", encoding="utf-8")
    (src / "pyproject.toml").write_text("[project]\nname='test'", encoding="utf-8")
    (src / "skill").mkdir()
    (src / "skill" / "SKILL.md").write_text("abc", encoding="utf-8")

    manifest = ManifestGenerator.generate_manifest(src)
    assert manifest.total_files == 5
    assert manifest.total_bytes == sum(f.size_bytes for f in manifest.files.values())

