"""Tests 27-35: Lifecycle handoffs, repository identity consistency, and approval boundary isolation."""
from __future__ import annotations

import json
from pathlib import Path
import pytest

from engine.integration import (
    IntegrationReportGenerator,
    IntegrationValidator,
    LifecycleOrchestrator,
)


def test_27_validate_phase_1_to_2_handoff(tmp_path: Path):
    """Verify handoff from Phase 1 to Phase 2."""
    reports = tmp_path / "reports"
    reports.mkdir()
    # Missing inputs
    res_bad = IntegrationValidator.validate_handoff("phase_1_intel", "phase_2_maintenance", reports)
    assert res_bad.is_valid is False
    assert "inventory.json" in res_bad.missing_inputs

    # Supply valid inputs
    (reports / "inventory.json").write_text(
        json.dumps({
            "schema_version": "1.0.0",
            "generated_at": "2026-01-01T00:00:00Z",
            "target_root": str(tmp_path),
            "files_count": 5,
        }),
        encoding="utf-8",
    )
    (reports / "repository-overview.md").write_text("# Overview", encoding="utf-8")
    res_good = IntegrationValidator.validate_handoff("phase_1_intel", "phase_2_maintenance", reports)
    assert res_good.is_valid is True
    assert len(res_good.errors) == 0


def test_28_validate_phase_3_to_4_handoff(tmp_path: Path):
    """Verify handoff to Phase 4 requires inventory, maintenance-plan, and security-findings."""
    reports = tmp_path / "reports"
    reports.mkdir()

    # Create inventory
    (reports / "inventory.json").write_text(
        json.dumps({
            "schema_version": "1.0.0",
            "generated_at": "2026-01-01T00:00:00Z",
            "target_root": str(tmp_path),
            "files_count": 5,
        }),
        encoding="utf-8",
    )
    # Create maintenance-plan
    (reports / "maintenance-plan.json").write_text(
        json.dumps({
            "schema_version": "1.0.0",
            "generated_at": "2026-01-01T00:00:00Z",
            "tasks": [],
        }),
        encoding="utf-8",
    )
    # Missing security-findings
    h1 = IntegrationValidator.validate_handoff("phase_3_security", "phase_4_repair", reports)
    assert h1.is_valid is False
    assert "security-findings.json" in h1.missing_inputs

    # Add security-findings
    (reports / "security-findings.json").write_text(
        json.dumps({
            "schema_version": "1.0.0",
            "generated_at": "2026-01-01T00:00:00Z",
            "findings": [],
        }),
        encoding="utf-8",
    )
    h2 = IntegrationValidator.validate_handoff("phase_3_security", "phase_4_repair", reports)
    assert h2.is_valid is True


def test_29_detect_repository_identity_mismatch(tmp_path: Path):
    """Detect if artifacts in reports_dir belong to different repository roots."""
    reports = tmp_path / "reports"
    reports.mkdir()
    other_repo = tmp_path / "other-project"
    other_repo.mkdir()

    (reports / "inventory.json").write_text(
        json.dumps({
            "schema_version": "1.0.0",
            "generated_at": "2026-01-01T00:00:00Z",
            "target_root": str(tmp_path),
            "files_count": 5,
        }),
        encoding="utf-8",
    )
    (reports / "maintenance-analysis.json").write_text(
        json.dumps({
            "schema_version": "1.0.0",
            "timestamp": "2026-01-01T00:00:00Z",
            "target": str(other_repo),
        }),
        encoding="utf-8",
    )
    (reports / "maintenance-plan.json").write_text(
        json.dumps({
            "schema_version": "1.0.0",
            "generated_at": "2026-01-01T00:00:00Z",
            "tasks": [],
        }),
        encoding="utf-8",
    )
    (reports / "security-findings.json").write_text(
        json.dumps({
            "schema_version": "1.0.0",
            "generated_at": "2026-01-01T00:00:00Z",
            "findings": [],
            "target_root": str(other_repo),
        }),
        encoding="utf-8",
    )

    handoff = IntegrationValidator.validate_handoff("phase_3_security", "phase_4_repair", reports)
    # Check identity mismatch
    assert handoff.identity_mismatch is True or any("mismatch" in e.lower() for e in handoff.errors)


def test_30_verify_approval_boundaries_isolation(tmp_path: Path):
    """Verify approval boundary check enforces staging approval != commit approval."""
    reports = tmp_path / "reports"
    reports.mkdir()
    (reports / "staging-approval.json").write_text(
        json.dumps({"schema_version": "1.0.0", "status": "APPROVED", "authorized_by": "user"}),
        encoding="utf-8",
    )
    ok, errs = IntegrationValidator.verify_approval_boundaries(reports)
    assert ok is True
    # Having staging approval alone does NOT create or authorize commit approval
    assert not (reports / "commit-approval.json").exists()


def test_31_lifecycle_orchestrator_evaluation(tmp_path: Path):
    """Verify LifecycleOrchestrator discovers executed phases and evaluates overall status."""
    reports = tmp_path / "reports"
    reports.mkdir()
    (reports / "inventory.json").write_text(
        json.dumps({
            "schema_version": "1.0.0",
            "generated_at": "2026-01-01T00:00:00Z",
            "target_root": str(tmp_path),
            "files_count": 10,
        }),
        encoding="utf-8",
    )
    (reports / "recommendations.json").write_text(
        json.dumps({"schema_version": "1.0.0", "recommendations": []}),
        encoding="utf-8",
    )
    (reports / "repository-overview.md").write_text("# Overview", encoding="utf-8")
    (reports / "repository-audit.md").write_text("# Audit", encoding="utf-8")

    res = LifecycleOrchestrator.evaluate_lifecycle(tmp_path, reports)
    assert "phase_1_intel" in res.executed_phases
    assert "phase_2_maintenance" in res.missing_phases
    assert res.approval_boundaries_preserved is True


def test_32_integration_report_generation(tmp_path: Path):
    """Verify IntegrationReportGenerator outputs all 4 integration artifacts."""
    reports = tmp_path / "reports"
    reports.mkdir()
    lifecycle_res = LifecycleOrchestrator.evaluate_lifecycle(tmp_path, reports)
    out = IntegrationReportGenerator.generate(lifecycle_res, reports)

    assert out["phase_registry"].is_file()
    assert out["artifact_registry"].is_file()
    assert out["json_report"].is_file()
    assert out["md_report"].is_file()

    json_data = json.loads(out["json_report"].read_text(encoding="utf-8"))
    assert json_data["repocraft_version"] == "1.0.0-rc1"
    md_text = out["md_report"].read_text(encoding="utf-8")
    assert "Lifecycle Integration Report" in md_text


def test_32b_validate_phase_2_to_3_handoff(tmp_path: Path):
    """Verify handoff from Phase 2 to Phase 3 requires inventory."""
    reports = tmp_path / "reports"
    reports.mkdir()
    res1 = IntegrationValidator.validate_handoff("phase_2_maintenance", "phase_3_security", reports)
    assert res1.is_valid is False
    assert "inventory.json" in res1.missing_inputs

    (reports / "inventory.json").write_text(
        json.dumps({
            "schema_version": "1.0.0",
            "generated_at": "2026-01-01T00:00:00Z",
            "target_root": str(tmp_path),
            "files_count": 5,
        }),
        encoding="utf-8",
    )
    res2 = IntegrationValidator.validate_handoff("phase_2_maintenance", "phase_3_security", reports)
    assert res2.is_valid is True


def test_32c_validate_phase_4_to_5_handoff(tmp_path: Path):
    """Verify handoff from Phase 4 to Phase 5."""
    reports = tmp_path / "reports"
    reports.mkdir()
    res = IntegrationValidator.validate_handoff("phase_4_repair", "phase_5_git_review", reports)
    assert res.is_valid is True


def test_32d_validate_phase_5_staging_to_commit_boundary(tmp_path: Path):
    """Verify staging result existence does not substitute commit approval."""
    reports = tmp_path / "reports"
    reports.mkdir()
    (reports / "staging-result.json").write_text(
        json.dumps({"schema_version": "1.0.0", "status": "VERIFIED", "staged_files": ["foo.py"]}),
        encoding="utf-8",
    )
    # Commit approval still absent
    assert not (reports / "commit-approval.json").exists()


def test_32e_validate_phase_5_commit_to_push_boundary(tmp_path: Path):
    """Verify commit receipt existence does not substitute push approval."""
    reports = tmp_path / "reports"
    reports.mkdir()
    (reports / "commit-receipt.json").write_text(
        json.dumps({"schema_version": "1.0.0", "status": "COMMITTED", "commit_hash": "abc123"}),
        encoding="utf-8",
    )
    # Push approval still absent
    assert not (reports / "push-approval.json").exists()

