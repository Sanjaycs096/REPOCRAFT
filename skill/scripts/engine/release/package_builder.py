"""Deterministic builder for release distribution archives."""
from __future__ import annotations

import hashlib
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Tuple

from .manifest_generator import ManifestGenerator, sha256_of_file
from .release_types import PackageManifest


# Deterministic zip timestamp: 2026-01-01 00:00:00
DETERMINISTIC_ZIP_TIME = (2026, 1, 1, 0, 0, 0)


class PackageBuilder:
    """Builds deterministic, reproducible ZIP distribution archives."""

    @classmethod
    def build_zip(
        cls,
        source_root: Path,
        output_dir: Path,
        version: str = "1.0.0-rc1",
        archive_name: Optional[str] = None,
    ) -> Tuple[Path, PackageManifest]:
        """Build a deterministic distribution ZIP package.
        
        Returns (archive_path, package_manifest).
        """
        source_resolved = source_root.resolve()
        output_dir.mkdir(parents=True, exist_ok=True)

        if not archive_name:
            archive_name = f"repocraft-{version}.zip"

        archive_path = output_dir / archive_name

        # 1. Generate preliminary manifest to identify files
        manifest = ManifestGenerator.generate_manifest(
            source_root=source_resolved,
            version=version,
            archive_name=archive_name,
        )

        # 2. Write zip file deterministically
        with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            for rel_path_str in sorted(manifest.files.keys()):
                file_path = source_resolved / rel_path_str
                # Create ZipInfo with fixed timestamp
                zinfo = zipfile.ZipInfo(filename=rel_path_str, date_time=DETERMINISTIC_ZIP_TIME)
                # Ensure readable file permissions
                zinfo.external_attr = 0o644 << 16
                if rel_path_str.endswith(".py") or rel_path_str.endswith(".sh"):
                    zinfo.external_attr = 0o755 << 16

                file_data = file_path.read_bytes()
                zf.writestr(zinfo, file_data)

        # 3. Calculate archive SHA-256
        archive_digest = sha256_of_file(archive_path)
        manifest.archive_sha256 = archive_digest

        return archive_path, manifest

