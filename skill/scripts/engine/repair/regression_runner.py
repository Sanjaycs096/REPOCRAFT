"""Module H2 & J — Regression Runner and Comparator for RepoCraft Phase 4.

Runs authorized project test suites and compares post-repair results against baseline:
- Distinguishes NEW_FAILURE vs PRE_EXISTING_FAILURE vs RESOLVED_FAILURE
- Strictly returns NOT_RUN when test execution is unauthorized
- Detects regressions that trigger automated rollback
"""
from __future__ import annotations

import os
import shlex
import subprocess
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from ..security.secret_scanner import redact_string
from ..security.test_result_analyzer import analyze_test_output
from ..security.test_runner import execute_test_command, is_command_safe
from .repair_types import (
    RegressionComparisonItem,
    RegressionOutcome,
    ValidationResult,
    ValidationState,
)


class RegressionRunner:
    """Manages baseline capture, regression check execution, and outcome comparison."""

    def __init__(self, target_dir: str, allow_execution: bool = False):
        self.target_dir = Path(target_dir).resolve()
        self.allow_execution = allow_execution
        self.baseline_results: Dict[str, ValidationResult] = {}
        self.post_repair_results: Dict[str, ValidationResult] = {}

    def run_check(self, command: str, check_id: str, level: str = "project_quality_gates") -> ValidationResult:
        """Execute a single test or lint command safely under policy."""
        if not self.allow_execution:
            return ValidationResult(
                level=level,
                command=command,
                state=ValidationState.NOT_RUN,
                exit_code=None,
                duration_seconds=0.0,
                output_redacted="Test execution was not authorized. Flagged as NOT_RUN by policy.",
                error_summary=None,
                passed=False,
            )

        # Use safe whitelisted test command execution from security engine
        res = execute_test_command(
            command=command,
            target_dir=str(self.target_dir),
            allow_execution=True,
            timeout_seconds=30,
        )

        state_mapping = {
            "PASSED": ValidationState.PASSED,
            "FAILED": ValidationState.FAILED,
            "TIMED_OUT": ValidationState.TIMED_OUT,
            "BLOCKED_BY_POLICY": ValidationState.BLOCKED_BY_POLICY,
            "MISSING_DEPENDENCIES": ValidationState.MISSING_DEPENDENCIES,
            "EXECUTION_ERROR": ValidationState.EXECUTION_ERROR,
            "NOT_RUN": ValidationState.NOT_RUN,
        }

        val_state = state_mapping.get(res.state.value, ValidationState.EXECUTION_ERROR)
        passed = (val_state == ValidationState.PASSED)

        return ValidationResult(
            level=level,
            command=command,
            state=val_state,
            exit_code=res.exit_code,
            duration_seconds=res.duration_seconds,
            output_redacted=res.raw_output_redacted,
            error_summary=res.error_summary,
            passed=passed,
        )

    def capture_baseline(self, commands: List[str]) -> Dict[str, ValidationResult]:
        """Run and record baseline validation results for candidate commands before repairs."""
        self.baseline_results.clear()
        for idx, cmd in enumerate(commands, start=1):
            cid = f"CHECK-{idx:03d}"
            res = self.run_check(cmd, cid, level="project_quality_gates")
            self.baseline_results[cid] = res
        return self.baseline_results

    def run_post_repair_validation(self, commands: List[str]) -> Dict[str, ValidationResult]:
        """Run validation commands after repairs have been applied."""
        self.post_repair_results.clear()
        for idx, cmd in enumerate(commands, start=1):
            cid = f"CHECK-{idx:03d}"
            res = self.run_check(cmd, cid, level="project_quality_gates")
            self.post_repair_results[cid] = res
        return self.post_repair_results

    def compare_regression(self) -> List[RegressionComparisonItem]:
        """Module J: Compare baseline vs post-repair to detect regressions and resolutions."""
        comparisons: List[RegressionComparisonItem] = []

        all_keys = set(self.baseline_results.keys()) | set(self.post_repair_results.keys())
        for cid in sorted(all_keys):
            base = self.baseline_results.get(cid)
            post = self.post_repair_results.get(cid)

            b_state = base.state if base else ValidationState.NOT_RUN
            p_state = post.state if post else ValidationState.NOT_RUN
            cmd_desc = (post.command if post else (base.command if base else cid))

            if b_state == ValidationState.NOT_RUN or p_state == ValidationState.NOT_RUN:
                outcome = RegressionOutcome.UNVERIFIED
            elif b_state == ValidationState.PASSED and p_state != ValidationState.PASSED:
                outcome = RegressionOutcome.NEW_FAILURE
            elif b_state != ValidationState.PASSED and p_state == ValidationState.PASSED:
                outcome = RegressionOutcome.RESOLVED_FAILURE
            elif b_state != ValidationState.PASSED and p_state != ValidationState.PASSED:
                outcome = RegressionOutcome.UNCHANGED_FAILURE
            else:
                outcome = RegressionOutcome.RESOLVED_WARNING if p_state == ValidationState.PASSED else RegressionOutcome.UNCHANGED_FAILURE

            comparisons.append(
                RegressionComparisonItem(
                    check_id=cid,
                    description=cmd_desc,
                    baseline_state=b_state,
                    post_repair_state=p_state,
                    outcome=outcome,
                )
            )

        return comparisons

    def has_new_regressions(self) -> bool:
        """Check if any new failure was introduced by applied repairs."""
        comparisons = self.compare_regression()
        return any(c.outcome == RegressionOutcome.NEW_FAILURE for c in comparisons)

