"""RepoCraft Phase 4 Bounded Repair, Safe Code Improvements & Regression Validation Engine."""
from __future__ import annotations

from .approval_manager import ApprovalManager
from .attempt_controller import AttemptController
from .backup_manager import BackupManager
from .change_guard import ChangeGuard
from .finding_ingestor import FindingIngestor, ingest_findings
from .patch_generator import PatchGenerator, sha256_of_file, sha256_of_text
from .regression_runner import RegressionRunner
from .repair_classifier import classify_finding
from .repair_executor import RepairExecutor
from .repair_orchestrator import RepairOrchestrator
from .repair_planner import RepairPlanner
from .repair_report_generator import generate_repair_reports
from .repair_types import (
    BackupRecord,
    ExecutionDisposition,
    NormalizedFinding,
    ProposedPatch,
    RegressionComparisonItem,
    RegressionOutcome,
    RepairCategory,
    RepairRiskLevel,
    RepairStatus,
    RepairTask,
    RollbackState,
    ValidationResult,
    ValidationState,
)
from .repair_validator import RepairValidator
from .risk_assessor import RiskAssessor
from .rollback_manager import RollbackManager

__all__ = [
    "RepairRiskLevel",
    "RepairCategory",
    "RepairStatus",
    "ExecutionDisposition",
    "ValidationState",
    "RegressionOutcome",
    "RollbackState",
    "NormalizedFinding",
    "ProposedPatch",
    "RepairTask",
    "BackupRecord",
    "ValidationResult",
    "RegressionComparisonItem",
    "FindingIngestor",
    "ingest_findings",
    "classify_finding",
    "RiskAssessor",
    "PatchGenerator",
    "RepairPlanner",
    "ApprovalManager",
    "ChangeGuard",
    "BackupManager",
    "RepairExecutor",
    "RepairValidator",
    "RegressionRunner",
    "AttemptController",
    "RollbackManager",
    "generate_repair_reports",
    "RepairOrchestrator",
    "sha256_of_file",
    "sha256_of_text",
]

