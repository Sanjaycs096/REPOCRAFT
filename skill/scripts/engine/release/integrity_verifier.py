"""Archive integrity, path traversal safety, and checksum verification."""
from __future__ import annotations

import hashlib
import re
import tempfile
import zipfile
from pathlib import Path
from typing import Dict, List, Optional, Set

from .release_types import PackageManifest, PackageValidationResult


# Suspicious pattern checks for accidental secret leakage
SECRET_PATTERNS = [
    re.compile(r"ghp_[A-Za-z0-9_]{36}"),
    re.compile(r"github_pat_[A-Za-z0-9_]{82}"),
    re.compile(r"-----BEGIN (RSA|OPENSSH|EC|DSA) PRIVATE KEY-----"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
]

REQUIRED_PACKAGE_FILES = [
    "README.md",
    "MANIFEST.json",
    "install.py",
    "pyproject.toml",
    "skill/SKILL.md",
    "skill/scripts/repocraft_intel.py",
    "skill/scripts/repocraft_maintenance.py",
    "skill/scripts/repocraft_security.py",
    "skill/scripts/repocraft_repair.py",
    "skill/scripts/repocraft_git.py",
    "skill/scripts/repocraft_status.py",
]


class IntegrityVerifier:
    """Verifies ZIP archive integrity, security boundaries, and checksum consistency."""

    @classmethod
    def verify_archive(
        cls,
        archive_path: Path,
        expected_manifest: Optional[PackageManifest] = None,
    ) -> PackageValidationResult:
        """Thoroughly audit archive safety, manifest agreement, and file contents."""
        errors: List[str] = []
        warnings: List[str] = []
        missing_files: List[str] = []
        unexpected_files: List[str] = []
        duplicate_entries: List[str] = []
        checksum_mismatches: List[str] = []
        secret_findings: List[str] = []
        path_traversal = False
        extractable = False

        if not archive_path.is_file():
            return PackageValidationResult(
                is_valid=False,
                archive_path=str(archive_path),
                errors=[f"Archive not found: {archive_path}"],
            )

        # 1. Test zip file structure
        try:
            with zipfile.ZipFile(archive_path, "r") as zf:
                # Test CRC on all files
                corrupt_file = zf.testzip()
                if corrupt_file:
                    errors.append(f"Corrupt zip entry detected: {corrupt_file}")

                infolist = zf.infolist()
                seen_names: Set[str] = set()

                for info in infolist:
                    name = info.filename
                    # Normalize slashes
                    norm_name = name.replace("\\", "/")

                    # Check duplicates
                    if norm_name in seen_names:
                        duplicate_entries.append(norm_name)
                        errors.append(f"Duplicate entry in archive: {norm_name}")
                    seen_names.add(norm_name)

                    # Check path traversal
                    if (
                        norm_name.startswith("/")
                        or norm_name.startswith("../")
                        or "/../" in norm_name
                        or ":/" in norm_name
                        or ":\\" in norm_name
                    ):
                        path_traversal = True
                        errors.append(f"Dangerous path traversal detected in entry: {name}")

                    # Check for forbidden development or cache files
                    if (
                        "__pycache__" in norm_name
                        or norm_name.endswith(".pyc")
                        or norm_name.startswith("tests/")
                        or norm_name.startswith(".git/")
                        or norm_name.startswith(".pytest_cache/")
                    ):
                        unexpected_files.append(norm_name)
                        errors.append(f"Development/cache file packaged into release: {norm_name}")

                # Check required files
                for req in REQUIRED_PACKAGE_FILES:
                    if req not in seen_names:
                        missing_files.append(req)
                        errors.append(f"Missing required runtime file in package: {req}")

                # Check against expected manifest if provided
                if expected_manifest:
                    for rel_str, entry in expected_manifest.files.items():
                        if rel_str not in seen_names:
                            missing_files.append(rel_str)
                            errors.append(f"Manifest file missing from archive: {rel_str}")

                # 2. Test actual extraction into temporary directory
                try:
                    with tempfile.TemporaryDirectory() as tmp_dir:
                        zf.extractall(tmp_dir)
                        extractable = True
                        extracted_root = Path(tmp_dir)

                        # Verify checksums and secret checks
                        for info in infolist:
                            extracted_file = extracted_root / info.filename
                            if extracted_file.is_file():
                                content = extracted_file.read_bytes()
                                digest = hashlib.sha256(content).hexdigest()

                                if expected_manifest and info.filename in expected_manifest.files:
                                    expected_hash = expected_manifest.files[info.filename].sha256
                                    if digest != expected_hash:
                                        checksum_mismatches.append(info.filename)
                                        errors.append(
                                            f"Checksum mismatch for {info.filename}: expected {expected_hash}, got {digest}"
                                        )

                                # Check text files for secret patterns
                                try:
                                    text_content = content.decode("utf-8")
                                    for pat in SECRET_PATTERNS:
                                        if pat.search(text_content):
                                            secret_findings.append(info.filename)
                                            errors.append(f"Potential secret pattern found in {info.filename}")
                                            break
                                except UnicodeDecodeError:
                                    pass
                except Exception as ex:
                    extractable = False
                    errors.append(f"Failed to safely extract archive: {ex}")

        except zipfile.BadZipFile as bzf:
            return PackageValidationResult(
                is_valid=False,
                archive_path=str(archive_path),
                errors=[f"Invalid or corrupted ZIP archive: {bzf}"],
            )
        except Exception as e:
            return PackageValidationResult(
                is_valid=False,
                archive_path=str(archive_path),
                errors=[f"Integrity check failed: {e}"],
            )

        is_valid = (
            len(errors) == 0
            and not path_traversal
            and len(duplicate_entries) == 0
            and len(missing_files) == 0
            and len(checksum_mismatches) == 0
            and extractable
        )

        return PackageValidationResult(
            is_valid=is_valid,
            archive_path=str(archive_path),
            errors=errors,
            warnings=warnings,
            missing_required_files=missing_files,
            unexpected_files=unexpected_files,
            path_traversal_detected=path_traversal,
            duplicate_entries=duplicate_entries,
            checksum_mismatches=checksum_mismatches,
            secret_patterns_detected=secret_findings,
            extractable=extractable,
        )

