"""Module M — Repair Orchestrator for RepoCraft Phase 4.

End-to-end pipeline coordinator for bounded repair and regression:
- Coordinates finding ingestion, planning, approval validation, change protection,
  backup creation, patch execution, multi-level validation, regression comparison,
  root-cause attempt tracking, rollback, and reporting.
- Supports modes: 'plan' (default), 'draft', and 'apply-approved'.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

from .approval_manager import ApprovalManager
from .attempt_controller import AttemptController
from .backup_manager import BackupManager
from .change_guard import ChangeGuard
from .finding_ingestor import FindingIngestor
from .patch_generator import sha256_of_text
from .regression_runner import RegressionRunner
from .repair_executor import RepairExecutor
from .repair_planner import RepairPlanner
from .repair_report_generator import generate_repair_reports
from .repair_types import (
    ExecutionDisposition,
    RegressionComparisonItem,
    RegressionOutcome,
    RepairStatus,
    RepairTask,
    ValidationResult,
    ValidationState,
)
from .repair_validator import RepairValidator
from .rollback_manager import RollbackManager


class RepairOrchestrator:
    """Coordinates the complete Phase 4 bounded repair workflow."""

    def __init__(
        self,
        target_dir: str,
        reports_dir: str,
        mode: str = "plan",
        approval_file: Optional[str] = None,
        allow_test_execution: bool = False,
    ):
        self.target_dir = Path(target_dir).resolve()
        self.reports_dir = Path(reports_dir).resolve()
        self.mode = mode
        self.allow_test_execution = allow_test_execution

        self.reports_dir.mkdir(parents=True, exist_ok=True)
        backup_dir = self.reports_dir / "backups"
        history_file = self.reports_dir / "attempt-history.json"

        # Initialize sub-components
        self.ingestor = FindingIngestor(str(self.reports_dir))
        self.planner = RepairPlanner(str(self.target_dir))
        self.approval_mgr = ApprovalManager(approval_file)
        self.change_guard = ChangeGuard(str(self.target_dir))
        self.backup_mgr = BackupManager(str(backup_dir))
        self.executor = RepairExecutor(str(self.target_dir), self.backup_mgr, self.change_guard)
        self.validator = RepairValidator(str(self.target_dir))
        self.regression_runner = RegressionRunner(str(self.target_dir), allow_execution=allow_test_execution)
        self.attempt_controller = AttemptController(history_file)
        self.rollback_mgr = RollbackManager(str(self.target_dir), self.backup_mgr)

    def run(self) -> Dict[str, Any]:
        """Execute Phase 4 pipeline according to selected mode."""
        # 1. Ingest findings from reports directory
        findings, warnings = self.ingestor.ingest_all()

        # 2. Plan repairs and generate proposed patches
        tasks = self.planner.plan_repairs(findings)

        # 3. Always write/update approval manifest template
        manifest_path = self.reports_dir / "approval-manifest.json"
        if not manifest_path.is_file():
            self.approval_mgr.generate_manifest(tasks, manifest_path)

        execution_results: List[Dict[str, Any]] = []
        validation_results: List[ValidationResult] = []
        regression_items: List[RegressionComparisonItem] = []
        rollback_results: List[Dict[str, Any]] = []

        # 4. Mode-specific execution
        if self.mode in ("plan", "draft"):
            # Target project files remain completely untouched
            pass

        elif self.mode == "apply-approved":
            # Baseline test suite execution (if authorized)
            test_commands = self._discover_candidate_commands()
            if self.allow_test_execution and test_commands:
                self.regression_runner.capture_baseline(test_commands)

            # Apply only authorized, safe repairs
            for task in tasks:
                # Check approval
                is_approved, appr_msg = self.approval_mgr.is_repair_approved(task)
                if task.approval_required and not is_approved:
                    execution_results.append({
                        "repair_id": task.repair_id,
                        "success": False,
                        "message": f"Skipped: {appr_msg}",
                        "modified_files": [],
                    })
                    continue

                # Check attempt controller
                combined_patch_hash = sha256_of_text(
                    "::".join(p.new_content_hash or "" for p in task.proposed_changes)
                )
                can_attempt, attempt_reason = self.attempt_controller.can_attempt(
                    task.root_cause_key, combined_patch_hash
                )
                if not can_attempt:
                    task.status = RepairStatus.MAX_ATTEMPTS_REACHED
                    execution_results.append({
                        "repair_id": task.repair_id,
                        "success": False,
                        "message": f"Halted: {attempt_reason}",
                        "modified_files": [],
                    })
                    continue

                # Execute repair
                exec_ok, exec_msg, modified_files = self.executor.execute_task(task, is_approved=is_approved)
                if not exec_ok:
                    self.attempt_controller.record_attempt(
                        task.root_cause_key, combined_patch_hash, False, exec_msg
                    )
                    execution_results.append({
                        "repair_id": task.repair_id,
                        "success": False,
                        "message": exec_msg,
                        "modified_files": [],
                    })
                    continue

                # Level 1 Validation: Patch integrity
                val1 = self.validator.validate_patch_integrity(task)
                validation_results.append(val1)

                # Level 2 Validation: Local syntax
                val2 = self.validator.validate_local_syntax(task)
                validation_results.append(val2)

                # Check if validation passed
                validation_passed = val1.passed and val2.passed

                # If dynamic regression execution is enabled
                if validation_passed and self.allow_test_execution and test_commands:
                    self.regression_runner.run_post_repair_validation(test_commands)
                    reg_comps = self.regression_runner.compare_regression()
                    regression_items.extend(reg_comps)
                    if self.regression_runner.has_new_regressions():
                        validation_passed = False

                if not validation_passed:
                    # Rollback RepoCraft modification!
                    task.status = RepairStatus.VALIDATION_FAILED
                    rb_res = self.rollback_mgr.rollback_repair(
                        task.repair_id, modified_files, reason="Validation checks or regression test failed"
                    )
                    rollback_results.append(rb_res)
                    task.status = RepairStatus.REPAIR_ROLLED_BACK
                    self.attempt_controller.record_attempt(
                        task.root_cause_key, combined_patch_hash, False, "Validation failed; rolled back"
                    )
                    execution_results.append({
                        "repair_id": task.repair_id,
                        "success": False,
                        "message": f"Applied but failed validation; rolled back cleanly. {val1.error_summary or val2.error_summary}",
                        "modified_files": modified_files,
                    })
                else:
                    task.status = RepairStatus.VALIDATION_PASSED
                    self.attempt_controller.record_attempt(
                        task.root_cause_key, combined_patch_hash, True, "Validation passed"
                    )
                    execution_results.append({
                        "repair_id": task.repair_id,
                        "success": True,
                        "message": exec_msg,
                        "modified_files": modified_files,
                    })

        # 5. Generate all 7 Phase 4 artifacts
        generated_files = generate_repair_reports(
            output_dir=str(self.reports_dir),
            target_dir=str(self.target_dir),
            mode=self.mode,
            findings=findings,
            tasks=tasks,
            execution_results=execution_results,
            validation_results=validation_results,
            regression_items=regression_items,
            rollback_results=rollback_results,
            attempt_history=self.attempt_controller.history,
            ingestion_warnings=warnings,
        )

        return {
            "target_dir": str(self.target_dir),
            "reports_dir": str(self.reports_dir),
            "mode": self.mode,
            "total_findings": len(findings),
            "total_tasks": len(tasks),
            "applied_repairs_count": sum(1 for e in execution_results if e.get("success")),
            "blocked_repairs_count": sum(1 for e in execution_results if not e.get("success")),
            "generated_files": generated_files,
            "tasks": [t.to_dict() for t in tasks],
        }

    def _discover_candidate_commands(self) -> List[str]:
        """Read candidate commands from test-analysis.json if present."""
        test_analysis_file = self.reports_dir / "test-analysis.json"
        if test_analysis_file.is_file():
            try:
                import json
                data = json.loads(test_analysis_file.read_text(encoding="utf-8", errors="replace"))
                return data.get("candidate_commands", [])
            except Exception:
                pass
        return []

