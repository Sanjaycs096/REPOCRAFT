"""Core data types, enums, and models for RepoCraft Repository Intelligence."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class EvidenceLevel(str, Enum):
    VERIFIED = "VERIFIED"
    LIKELY = "LIKELY"
    UNKNOWN = "UNKNOWN"


class Severity(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"


class FileCategory(str, Enum):
    SOURCE = "source"
    DOCUMENTATION = "documentation"
    TESTING = "testing"
    CONFIGURATION = "configuration"
    ASSETS = "assets"
    GENERATED = "generated"
    VENDOR = "vendor"
    DATA = "data"
    UNKNOWN = "unknown"


@dataclass
class FileInventoryItem:
    relative_path: str
    extension: str
    category: FileCategory
    size_bytes: int
    classification: str
    is_sensitive: bool = False
    warning: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "relative_path": self.relative_path,
            "extension": self.extension,
            "category": self.category.value,
            "size_bytes": self.size_bytes,
            "classification": self.classification,
            "is_sensitive": self.is_sensitive,
            "warning": self.warning,
        }


@dataclass
class GitRemote:
    name: str
    url: str  # credentials redacted


@dataclass
class GitBaseline:
    is_git_repository: bool
    current_branch: Optional[str] = None
    head_commit: Optional[str] = None
    head_commit_short: Optional[str] = None
    head_commit_date: Optional[str] = None
    head_commit_author: Optional[str] = None
    is_detached_head: bool = False
    is_shallow: bool = False
    has_submodules: bool = False
    remotes: List[GitRemote] = field(default_factory=list)
    staged_files: List[str] = field(default_factory=list)
    unstaged_files: List[str] = field(default_factory=list)
    untracked_files: List[str] = field(default_factory=list)
    pre_existing_modifications_count: int = 0
    warning: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_git_repository": self.is_git_repository,
            "current_branch": self.current_branch,
            "head_commit": self.head_commit,
            "head_commit_short": self.head_commit_short,
            "head_commit_date": self.head_commit_date,
            "head_commit_author": self.head_commit_author,
            "is_detached_head": self.is_detached_head,
            "is_shallow": self.is_shallow,
            "has_submodules": self.has_submodules,
            "remotes": [{"name": r.name, "url": r.url} for r in self.remotes],
            "staged_files": self.staged_files,
            "unstaged_files": self.unstaged_files,
            "untracked_files": self.untracked_files,
            "pre_existing_modifications_count": self.pre_existing_modifications_count,
            "warning": self.warning,
        }


@dataclass
class DiscoveredCommand:
    gate_name: str
    command: str
    source_file: str
    verified: bool = False  # Always False in Phase 1 (discovered only)


@dataclass
class GovernanceItem:
    item_type: str
    relative_path: Optional[str] = None
    exists: bool = False
    is_empty: bool = True
    size_bytes: int = 0
    confidence: EvidenceLevel = EvidenceLevel.UNKNOWN
    notes: Optional[str] = None


@dataclass
class ArchitectureObservation:
    dimension: str
    classification: str  # e.g., "Next.js App Router", or "UNKNOWN"
    evidence_level: EvidenceLevel
    evidence_sources: List[str] = field(default_factory=list)
    details: str = ""


@dataclass
class HealthFinding:
    finding_id: str
    category: str
    severity: Severity
    evidence_level: EvidenceLevel
    evidence: str
    explanation: str
    suggested_action: str
    requires_approval: bool
    target_phase: int  # Phase 1, 2, 3, 4, 5


@dataclass
class RepositoryIntelligenceReport:
    repo_root: str
    project_name: str
    detected_types: List[str]
    languages: List[str]
    frameworks: List[str]
    package_managers: List[str]
    manifests: List[str]
    entry_points: List[str]
    source_directories: List[str]
    asset_directories: List[str]
    configuration_files: List[str]
    test_directories: List[str]
    documentation_files: List[str]
    cicd_workflows: List[str]
    is_monorepo: bool
    monorepo_packages: List[str]
    file_inventory_summary: Dict[str, Any]
    git_baseline: GitBaseline
    governance: Dict[str, GovernanceItem]
    discovered_commands: List[DiscoveredCommand]
    architecture: Dict[str, ArchitectureObservation]
    findings: List[HealthFinding]
    unknowns_and_limitations: List[str]
    safe_warnings: List[str]

