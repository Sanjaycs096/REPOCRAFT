"""Verifies distribution package integrity, checksums, and safety boundaries."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Dict, List, Optional

from engine.release import IntegrityVerifier
from .distribution_types import DistributionCheckStatus, DistributionVerificationResult


def sha256_of_path(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


class DistributionVerifier:
    """Audits distribution packages for release readiness."""

    def __init__(self, repo_root: Optional[Path] = None, package_path: Optional[Path] = None):
        self.repo_root = repo_root or Path.cwd()
        self.package_path = package_path

    def verify(self, package_path: Optional[Path] = None) -> DistributionVerificationResult:
        pkg = package_path or self.package_path
        if not pkg:
            raise ValueError("package_path must be specified")
        expected_manifest = self.repo_root / "reports" / "release-manifest.json"
        if not expected_manifest.is_file():
            expected_manifest = None
        return self.verify_distribution_package(pkg, expected_manifest)

    @classmethod
    def verify_distribution_package(
        cls,
        package_path: Path,
        expected_manifest_path: Optional[Path] = None,
    ) -> DistributionVerificationResult:
        """Thoroughly audit package integrity, size, checksums, and safety."""
        pkg_resolved = package_path.resolve()
        errors: List[str] = []
        warnings: List[str] = []

        if not pkg_resolved.is_file():
            return DistributionVerificationResult(
                is_valid=False,
                status=DistributionCheckStatus.INVALID,
                package_path=str(pkg_resolved),
                archive_sha256="",
                files_count=0,
                total_bytes=0,
                errors=[f"Distribution package not found: {pkg_resolved}"],
            )

        archive_sha256 = sha256_of_path(pkg_resolved)
        total_bytes = pkg_resolved.stat().st_size

        if total_bytes == 0:
            return DistributionVerificationResult(
                is_valid=False,
                status=DistributionCheckStatus.CORRUPTED,
                package_path=str(pkg_resolved),
                archive_sha256=archive_sha256,
                files_count=0,
                total_bytes=0,
                errors=["Distribution package is 0 bytes (empty file)"],
            )

        # Integrity verification
        pkg_res = IntegrityVerifier.verify_archive(pkg_resolved)
        errors.extend(pkg_res.errors)
        warnings.extend(pkg_res.warnings)

        # If release-manifest.json provided, compare checksums
        files_count = 0
        if expected_manifest_path and expected_manifest_path.is_file():
            try:
                manifest_data = json.loads(expected_manifest_path.read_text(encoding="utf-8"))
                exp_sha = manifest_data.get("archive_sha256")
                if exp_sha and exp_sha != archive_sha256:
                    errors.append(f"Archive SHA-256 mismatch against manifest: expected {exp_sha}, got {archive_sha256}")
                files_count = len(manifest_data.get("files", {}))
            except Exception as e:
                warnings.append(f"Could not parse expected manifest: {e}")

        is_valid = len(errors) == 0 and pkg_res.is_valid
        status = DistributionCheckStatus.VALID if is_valid else DistributionCheckStatus.INVALID

        return DistributionVerificationResult(
            is_valid=is_valid,
            status=status,
            package_path=str(pkg_resolved),
            archive_sha256=archive_sha256,
            files_count=files_count or len(pkg_res.missing_required_files),
            total_bytes=total_bytes,
            path_traversal_safe=not pkg_res.path_traversal_detected,
            integrity_valid=pkg_res.is_valid,
            secret_scan_valid=len(pkg_res.secret_patterns_detected) == 0,
            errors=errors,
            warnings=warnings,
        )
