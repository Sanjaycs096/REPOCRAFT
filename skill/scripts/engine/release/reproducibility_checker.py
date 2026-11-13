"""Checks package build reproducibility across independent builds."""
from __future__ import annotations

import tempfile
from pathlib import Path
from typing import List

from .manifest_generator import sha256_of_file
from .package_builder import PackageBuilder
from .release_types import ReproducibilityResult


class ReproducibilityChecker:
    """Verifies that building the release package produces identical outputs."""

    @classmethod
    def check_reproducibility(
        cls,
        source_root: Path,
        version: str = "1.0.0-rc1",
    ) -> ReproducibilityResult:
        """Build the package twice in separate temp directories and verify reproducibility."""
        differences: List[str] = []

        with tempfile.TemporaryDirectory() as tmp_a, tempfile.TemporaryDirectory() as tmp_b:
            path_a, manifest_a = PackageBuilder.build_zip(
                source_root=source_root,
                output_dir=Path(tmp_a),
                version=version,
                archive_name="repocraft-a.zip",
            )
            path_b, manifest_b = PackageBuilder.build_zip(
                source_root=source_root,
                output_dir=Path(tmp_b),
                version=version,
                archive_name="repocraft-b.zip",
            )

            # Compare file inventories
            files_a = set(manifest_a.files.keys())
            files_b = set(manifest_b.files.keys())
            inventory_identical = files_a == files_b

            if not inventory_identical:
                diff_ab = files_a - files_b
                diff_ba = files_b - files_a
                if diff_ab:
                    differences.append(f"Files present in build A but missing in B: {sorted(diff_ab)}")
                if diff_ba:
                    differences.append(f"Files present in build B but missing in A: {sorted(diff_ba)}")

            # Compare individual file hashes
            file_hashes_identical = True
            for f in sorted(files_a.intersection(files_b)):
                hash_a = manifest_a.files[f].sha256
                hash_b = manifest_b.files[f].sha256
                if hash_a != hash_b:
                    file_hashes_identical = False
                    differences.append(f"Content hash divergence for file '{f}': {hash_a} vs {hash_b}")

            # Compare archive SHA-256
            digest_a = sha256_of_file(path_a)
            digest_b = sha256_of_file(path_b)
            byte_for_byte = digest_a == digest_b

            if not byte_for_byte:
                differences.append(
                    f"Archive byte-for-byte checksum differs: {digest_a} vs {digest_b}"
                )

            is_reproducible = inventory_identical and file_hashes_identical

            return ReproducibilityResult(
                is_reproducible=is_reproducible,
                byte_for_byte=byte_for_byte,
                inventory_identical=inventory_identical,
                file_hashes_identical=file_hashes_identical,
                differences=differences,
            )

