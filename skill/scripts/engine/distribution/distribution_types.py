"""Data types and contracts for Release Publication, Distribution & Maintenance."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class ReleaseClassification(str, Enum):
    """Categorization for release notes entries."""
    ADDED = "Added"
    CHANGED = "Changed"
    FIXED = "Fixed"
    SECURITY = "Security"
    BREAKING = "Breaking Changes"
    DOCUMENTATION = "Documentation"


class UpgradeStatus(str, Enum):
    """Status of an installation upgrade check or execution."""
    UPGRADE_AVAILABLE = "UPGRADE_AVAILABLE"
    UP_TO_DATE = "UP_TO_DATE"
    UNKNOWN_SOURCE = "UNKNOWN_SOURCE"
    UPGRADE_BLOCKED = "UPGRADE_BLOCKED"
    BACKUP_CREATED = "BACKUP_CREATED"
    UPGRADED = "UPGRADED"
    ROLLBACK_COMPLETED = "ROLLBACK_COMPLETED"
    ROLLBACK_FAILED = "ROLLBACK_FAILED"


class DistributionCheckStatus(str, Enum):
    """Status of package distribution checks."""
    VALID = "VALID"
    INVALID = "INVALID"
    CORRUPTED = "CORRUPTED"
    UNVERIFIED = "UNVERIFIED"


@dataclass
class ReleaseNoteEntry:
    """Individual item in release notes."""
    category: ReleaseClassification
    summary: str
    details: str = ""
    evidence_reference: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "category": self.category.value,
            "summary": self.summary,
            "details": self.details,
            "evidence_reference": self.evidence_reference,
        }


@dataclass
class ReleaseNotes:
    """Structured release notes for a release candidate or version."""
    version: str
    release_date: str
    summary: str
    highlights: List[str] = field(default_factory=list)
    changes: Dict[str, List[ReleaseNoteEntry]] = field(default_factory=dict)
    breaking_changes: List[str] = field(default_factory=list)
    migration_notes: List[str] = field(default_factory=list)
    known_limitations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "version": self.version,
            "release_date": self.release_date,
            "summary": self.summary,
            "highlights": list(self.highlights),
            "changes": {
                k: [entry.to_dict() for entry in v]
                for k, v in self.changes.items()
            },
            "breaking_changes": list(self.breaking_changes),
            "migration_notes": list(self.migration_notes),
            "known_limitations": list(self.known_limitations),
        }


@dataclass
class DistributionVerificationResult:
    """Result of auditing distribution archive integrity and security."""
    is_valid: bool
    status: DistributionCheckStatus
    package_path: str
    archive_sha256: str
    files_count: int
    total_bytes: int
    path_traversal_safe: bool = True
    integrity_valid: bool = True
    secret_scan_valid: bool = True
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": "1.0.0",
            "is_valid": self.is_valid,
            "status": self.status.value,
            "package_path": self.package_path,
            "archive_sha256": self.archive_sha256,
            "files_count": self.files_count,
            "total_bytes": self.total_bytes,
            "path_traversal_safe": self.path_traversal_safe,
            "integrity_valid": self.integrity_valid,
            "secret_scan_valid": self.secret_scan_valid,
            "errors": list(self.errors),
            "warnings": list(self.warnings),
        }


@dataclass
class InstallationTestResult:
    """Result of validating an installation scenario."""
    test_type: str
    is_valid: bool
    target_path: str
    files_installed: int
    manifest_present: bool
    manifest_hashes_valid: bool
    user_files_preserved: bool
    backup_verified: bool = False
    rollback_verified: bool = False
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "test_type": self.test_type,
            "is_valid": self.is_valid,
            "target_path": self.target_path,
            "files_installed": self.files_installed,
            "manifest_present": self.manifest_present,
            "manifest_hashes_valid": self.manifest_hashes_valid,
            "user_files_preserved": self.user_files_preserved,
            "backup_verified": self.backup_verified,
            "rollback_verified": self.rollback_verified,
            "errors": list(self.errors),
            "warnings": list(self.warnings),
        }


@dataclass
class UpgradePlan:
    """Plan for upgrading an installed RepoCraft copy."""
    target_directory: str
    current_version: Optional[str]
    candidate_version: str
    upgrade_status: UpgradeStatus
    backup_path: Optional[str]
    files_to_add: List[str] = field(default_factory=list)
    files_to_update: List[str] = field(default_factory=list)
    files_to_remove: List[str] = field(default_factory=list)
    can_proceed: bool = True
    blockers: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "target_directory": self.target_directory,
            "current_version": self.current_version,
            "candidate_version": self.candidate_version,
            "upgrade_status": self.upgrade_status.value,
            "backup_path": self.backup_path,
            "files_to_add": list(self.files_to_add),
            "files_to_update": list(self.files_to_update),
            "files_to_remove": list(self.files_to_remove),
            "can_proceed": self.can_proceed,
            "blockers": list(self.blockers),
        }


@dataclass
class UpgradeReceipt:
    """Receipt after executing an upgrade or rollback."""
    timestamp: str
    from_version: Optional[str]
    to_version: str
    status: UpgradeStatus
    backup_path: Optional[str]
    updated_files_count: int
    verification_passed: bool
    errors: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "from_version": self.from_version,
            "to_version": self.to_version,
            "status": self.status.value,
            "backup_path": self.backup_path,
            "updated_files_count": self.updated_files_count,
            "verification_passed": self.verification_passed,
            "errors": list(self.errors),
        }


@dataclass
class MaintenanceAuditReport:
    """Health audit of RepoCraft installation, manifests, and documentation."""
    timestamp: str
    version: str
    installation_healthy: bool
    manifests_consistent: bool
    policy_files_intact: bool
    cli_drivers_intact: bool
    schemas_compatible: bool
    zero_telemetry_guarantee: bool = True
    known_limitations: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": "1.0.0",
            "timestamp": self.timestamp,
            "version": self.version,
            "installation_healthy": self.installation_healthy,
            "manifests_consistent": self.manifests_consistent,
            "policy_files_intact": self.policy_files_intact,
            "cli_drivers_intact": self.cli_drivers_intact,
            "schemas_compatible": self.schemas_compatible,
            "zero_telemetry_guarantee": self.zero_telemetry_guarantee,
            "known_limitations": list(self.known_limitations),
            "recommendations": list(self.recommendations),
            "errors": list(self.errors),
            "warnings": list(self.warnings),
        }

