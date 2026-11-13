"""Data types and models for Release Packaging and Readiness Engine."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class ReleaseStatus(str, Enum):
    """Overall release candidate status."""
    READY_FOR_RELEASE = "READY_FOR_RELEASE"
    READY_WITH_LIMITATIONS = "READY_WITH_LIMITATIONS"
    NOT_READY = "NOT_READY"
    BLOCKED = "BLOCKED"


class GateStatus(str, Enum):
    """Individual release gate status."""
    PASS = "PASS"
    FAIL = "FAIL"
    NOT_RUN = "NOT_RUN"
    BLOCKED = "BLOCKED"
    WAIVED = "WAIVED"


@dataclass
class ReleaseGate:
    """Evaluation of a mandatory release completion gate."""
    gate_id: str
    name: str
    status: GateStatus
    summary: str
    evidence: List[str] = field(default_factory=list)
    blockers: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "gate_id": self.gate_id,
            "name": self.name,
            "status": self.status.value,
            "summary": self.summary,
            "evidence": list(self.evidence),
            "blockers": list(self.blockers),
        }


@dataclass
class PackageFileEntry:
    """Metadata for a single file included in a release package."""
    archive_path: str
    size_bytes: int
    sha256: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "archive_path": self.archive_path,
            "size_bytes": self.size_bytes,
            "sha256": self.sha256,
        }


@dataclass
class PackageManifest:
    """Manifest of files and cryptographic hashes in a release package."""
    package_name: str
    version: str
    archive_name: str
    archive_sha256: str
    created_at: str
    total_files: int
    total_bytes: int
    files: Dict[str, PackageFileEntry] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": "1.0.0",
            "package_name": self.package_name,
            "version": self.version,
            "archive_name": self.archive_name,
            "archive_sha256": self.archive_sha256,
            "created_at": self.created_at,
            "total_files": self.total_files,
            "total_bytes": self.total_bytes,
            "files": {k: v.to_dict() for k, v in self.files.items()},
        }


@dataclass
class PackageValidationResult:
    """Result of validating archive integrity, paths, and security."""
    is_valid: bool
    archive_path: str
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    missing_required_files: List[str] = field(default_factory=list)
    unexpected_files: List[str] = field(default_factory=list)
    path_traversal_detected: bool = False
    duplicate_entries: List[str] = field(default_factory=list)
    checksum_mismatches: List[str] = field(default_factory=list)
    secret_patterns_detected: List[str] = field(default_factory=list)
    extractable: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_valid": self.is_valid,
            "archive_path": self.archive_path,
            "errors": list(self.errors),
            "warnings": list(self.warnings),
            "missing_required_files": list(self.missing_required_files),
            "unexpected_files": list(self.unexpected_files),
            "path_traversal_detected": self.path_traversal_detected,
            "duplicate_entries": list(self.duplicate_entries),
            "checksum_mismatches": list(self.checksum_mismatches),
            "secret_patterns_detected": list(self.secret_patterns_detected),
            "extractable": self.extractable,
        }


@dataclass
class ReproducibilityResult:
    """Comparison of two independent package builds from the same state."""
    is_reproducible: bool
    byte_for_byte: bool
    inventory_identical: bool
    file_hashes_identical: bool
    differences: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_reproducible": self.is_reproducible,
            "byte_for_byte": self.byte_for_byte,
            "inventory_identical": self.inventory_identical,
            "file_hashes_identical": self.file_hashes_identical,
            "differences": list(self.differences),
        }

