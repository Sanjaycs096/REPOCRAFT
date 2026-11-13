"""Media and visual assets auditor for RepoCraft.

Audits repository screenshots, logos, diagrams, GIFs, and image files for
file size bloat, duplication, and missing visual documentation.
Never fabricates screenshots or claims unverified media.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple


class MediaItem:
    def __init__(self, relative_path: str, size_bytes: int, extension: str, is_referenced: bool):
        self.relative_path = relative_path
        self.size_bytes = size_bytes
        self.extension = extension
        self.is_referenced = is_referenced

    def to_dict(self) -> Dict[str, Any]:
        return {
            "relative_path": self.relative_path,
            "size_bytes": self.size_bytes,
            "extension": self.extension,
            "is_referenced": self.is_referenced,
        }


class MediaAuditResult:
    def __init__(
        self,
        media_files: List[MediaItem],
        total_media_size_bytes: int,
        duplicate_media: List[List[str]],
        oversized_media: List[MediaItem],  # > 2MB
        missing_screenshots_recommended: bool,
        screenshot_capture_spec: str | None,
        diagram_recommendations: List[str],
    ):
        self.media_files = media_files
        self.total_media_size_bytes = total_media_size_bytes
        self.duplicate_media = duplicate_media
        self.oversized_media = oversized_media
        self.missing_screenshots_recommended = missing_screenshots_recommended
        self.screenshot_capture_spec = screenshot_capture_spec
        self.diagram_recommendations = diagram_recommendations

    def to_dict(self) -> Dict[str, Any]:
        return {
            "media_files": [m.to_dict() for m in self.media_files],
            "total_media_size_bytes": self.total_media_size_bytes,
            "duplicate_media": self.duplicate_media,
            "oversized_media": [m.to_dict() for m in self.oversized_media],
            "missing_screenshots_recommended": self.missing_screenshots_recommended,
            "screenshot_capture_spec": self.screenshot_capture_spec,
            "diagram_recommendations": self.diagram_recommendations,
        }


class MediaAuditor:
    """Audits image, media, and visual presentation assets."""

    MEDIA_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".ico"}

    def __init__(self, repo_root: Path, file_paths: List[str], detected_types: List[str]):
        self.repo_root = repo_root
        self.file_paths = file_paths
        self.detected_types = detected_types

    def audit(self, referenced_paths: Set[str]) -> MediaAuditResult:
        media_items: List[MediaItem] = []
        hashes: Dict[str, List[str]] = {}
        oversized: List[MediaItem] = []
        total_bytes = 0

        for p in self.file_paths:
            ext = Path(p).suffix.lower()
            if ext in self.MEDIA_EXTENSIONS:
                full_path = self.repo_root / p
                try:
                    size = full_path.stat().st_size
                    total_bytes += size
                    is_ref = p in referenced_paths

                    item = MediaItem(p, size, ext, is_ref)
                    media_items.append(item)

                    if size > 2 * 1024 * 1024:  # > 2MB
                        oversized.append(item)

                    h = hashlib.sha256(full_path.read_bytes()).hexdigest()
                    hashes.setdefault(h, []).append(p)
                except Exception:
                    continue

        # Duplicate media
        duplicates = [paths for paths in hashes.values() if len(paths) > 1]

        # Check if project should have screenshots
        is_ui = any("Web Application" in t or "Frontend" in t or "Extension" in t for t in self.detected_types)
        has_screenshots = any(
            "screen" in m.relative_path.lower() or "demo" in m.relative_path.lower()
            for m in media_items
        )

        missing_screenshots = is_ui and not has_screenshots
        screenshot_spec = None
        if missing_screenshots:
            screenshot_spec = (
                "Capture high-resolution PNG (1280x720 or 1920x1080) of the main application dashboard "
                "or interface. Save to 'docs/images/screenshot-main.png' and reference in README."
            )

        diagrams = []
        if any("API" in t or "Backend" in t or "Monorepository" in t for t in self.detected_types):
            diagrams.append("Provide a Mermaid sequence or architecture flowchart in README.")

        return MediaAuditResult(
            media_files=media_items,
            total_media_size_bytes=total_bytes,
            duplicate_media=duplicates,
            oversized_media=oversized,
            missing_screenshots_recommended=missing_screenshots,
            screenshot_capture_spec=screenshot_spec,
            diagram_recommendations=diagrams,
        )

