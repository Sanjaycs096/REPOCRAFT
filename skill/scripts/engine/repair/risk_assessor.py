"""Risk assessor and authorization check helpers for RepoCraft Phase 4."""
from __future__ import annotations

from typing import Dict, List, Optional

from .repair_types import ExecutionDisposition, RepairCategory, RepairRiskLevel, RepairTask


class RiskAssessor:
    """Evaluates repair risks and validates authorization boundaries."""

    @staticmethod
    def is_autonomous_permitted(task: RepairTask) -> bool:
        """Determines whether a task is permitted to execute autonomously without explicit approval."""
        # Policy: CRITICAL, HIGH, and MEDIUM risk tasks are NEVER autonomous
        if task.risk_level in (RepairRiskLevel.CRITICAL, RepairRiskLevel.HIGH, RepairRiskLevel.MEDIUM):
            return False

        # Policy: Tasks flagged approval_required are not autonomous
        if task.approval_required:
            return False

        # Policy: Dead code deletion and license modifications are NEVER autonomous
        if task.category in (RepairCategory.DEAD_CODE_REVIEW, RepairCategory.LICENSE_AND_LEGAL):
            return False

        # Only explicitly marked AUTONOMOUS_CANDIDATE can proceed
        return task.disposition == ExecutionDisposition.AUTONOMOUS_CANDIDATE

    @staticmethod
    def validate_general_permission_scope(task: RepairTask, general_authorization: bool) -> bool:
        """Verifies that general repository permission cannot authorize high/critical risk repairs."""
        if not general_authorization:
            return False
        # General authorization CANNOT authorize CRITICAL or HIGH risk tasks
        if task.risk_level in (RepairRiskLevel.CRITICAL, RepairRiskLevel.HIGH):
            return False
        return True

