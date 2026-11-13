"""Generates verified package inventories and cryptographic manifests."""
from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Set

from .release_types import PackageFileEntry, PackageManifest


def sha256_of_file(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


class ManifestGenerator:
    """Calculates package inventory, file sizes, and cryptographic SHA-256 digests."""

    EXCLUDED_PATTERNS = {
        "__pycache__",
        ".pytest_cache",
        ".git",
        ".backup",
        ".coverage",
        ".DS_Store",
    }

    # Development-only directories and files that MUST NOT be packaged into release distributions
    DEVELOPMENT_EXCLUSIONS = {
        "tests",
        "reports",
        "dist",
        "build",
    }

    @classmethod
    def is_packageable(cls, rel_path: Path) -> bool:
        """Determine if a relative path belongs in the release distribution."""
        parts = rel_path.parts
        if not parts:
            return False

        # Exclude development dirs
        if parts[0] in cls.DEVELOPMENT_EXCLUSIONS:
            return False

        # Exclude cache and backup patterns
        for part in parts:
            for pattern in cls.EXCLUDED_PATTERNS:
                if pattern in part:
                    return False
            if part.endswith(".pyc") or part.endswith(".pyo"):
                return False

        # Exclude dev-only report files at root (e.g. PHASE-5-IMPLEMENTATION-REPORT.md)
        if len(parts) == 1 and parts[0].startswith("PHASE-") and parts[0].endswith(".md"):
            return False
        if len(parts) == 1 and parts[0].startswith("PHASE-") and parts[0].endswith(".txt"):
            return False

        # Only allow recognized top-level categories
        allowed_roots = {"README.md", "LICENSE", "MANIFEST.json", "install.py", "pyproject.toml", "skill", "adapters", "docs"}
        if parts[0] not in allowed_roots:
            return False

        return True

    @classmethod
    def generate_manifest(
        cls,
        source_root: Path,
        version: str = "1.0.0-rc1",
        archive_name: str = "repocraft-1.0.0-rc1.zip",
        archive_sha256: str = "",
    ) -> PackageManifest:
        """Scan source_root and build deterministic PackageManifest."""
        source_resolved = source_root.resolve()
        files_dict: Dict[str, PackageFileEntry] = {}
        total_bytes = 0

        # Collect and sort all valid files deterministically
        candidate_paths: List[Path] = []
        for p in source_resolved.rglob("*"):
            if p.is_file():
                rel = p.relative_to(source_resolved)
                if cls.is_packageable(rel):
                    candidate_paths.append(p)

        candidate_paths.sort(key=lambda p: str(p.relative_to(source_resolved)).replace("\\", "/"))

        for p in candidate_paths:
            rel_str = str(p.relative_to(source_resolved)).replace("\\", "/")
            size = p.stat().st_size
            digest = sha256_of_file(p)
            files_dict[rel_str] = PackageFileEntry(
                archive_path=rel_str,
                size_bytes=size,
                sha256=digest,
            )
            total_bytes += size

        return PackageManifest(
            package_name="RepoCraft",
            version=version,
            archive_name=archive_name,
            archive_sha256=archive_sha256,
            created_at=datetime.now(timezone.utc).isoformat(),
            total_files=len(files_dict),
            total_bytes=total_bytes,
            files=files_dict,
        )

