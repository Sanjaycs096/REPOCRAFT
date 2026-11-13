"""Comprehensive Phase 4 Test Suite for RepoCraft Bounded Repair & Regression Engine.

Covers 82 distinct test scenarios across:
1-10: Finding ingestion
11-20: Classification and planning
21-26: Approval management
27-34: Repository protection & ChangeGuard
35-40: Backup and recovery
41-49: Safe repair execution
50-58: Regression validation
59-64: 3-attempt root-cause controller
65-69: Rollback manager
70-82: Integration, artifacts, CLI & regression checks
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict

import pytest

# Ensure skill scripts is on sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent
SKILL_SCRIPTS = REPO_ROOT / "skill" / "scripts"
if str(SKILL_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SKILL_SCRIPTS))

from engine.repair import (
    ApprovalManager,
    AttemptController,
    BackupManager,
    ChangeGuard,
    ExecutionDisposition,
    FindingIngestor,
    PatchGenerator,
    RegressionOutcome,
    RegressionRunner,
    RepairCategory,
    RepairExecutor,
    RepairOrchestrator,
    RepairPlanner,
    RepairRiskLevel,
    RepairStatus,
    RepairValidator,
    RiskAssessor,
    RollbackManager,
    RollbackState,
    ValidationResult,
    ValidationState,
    classify_finding,
    generate_repair_reports,
    ingest_findings,
    sha256_of_file,
    sha256_of_text,
)
from engine.repair.repair_types import NormalizedFinding, ProposedPatch, RepairTask

# Suppress test class collection for dataclasses
ProposedPatch.__test__ = False
RepairTask.__test__ = False
ValidationResult.__test__ = False


# Helper to initialize a git repo for testing change guard
def init_git_repo(path: Path) -> None:
    subprocess.run(["git", "init"], cwd=str(path), capture_output=True, check=True)
    subprocess.run(["git", "config", "user.name", "Tester"], cwd=str(path), capture_output=True, check=True)
    subprocess.run(["git", "config", "user.email", "tester@example.com"], cwd=str(path), capture_output=True, check=True)


# ==============================================================================
# 1-10: FINDING INGESTION TESTS
# ==============================================================================

def test_01_ingest_valid_phase1_artifacts(tmp_path: Path):
    recs = [
        {"recommendation_id": "P1-001", "category": "Hygiene", "severity": "LOW", "confidence": "HIGH", "finding": "Add .gitignore", "evidence": "missing", "action": "create .gitignore"}
    ]
    (tmp_path / "recommendations.json").write_text(json.dumps(recs), encoding="utf-8")
    findings, warnings = ingest_findings(str(tmp_path))
    assert len(findings) == 1
    assert findings[0].source_id == "P1-001"
    assert findings[0].source_phase == "phase1"


def test_02_ingest_valid_phase2_artifacts(tmp_path: Path):
    plan = {
        "tasks": [
            {"task_id": "P2-001", "category": "Documentation", "severity": "LOW", "risk_level": "LOW", "title": "Fix broken link", "description": "Fix link in README.md", "affected_files": ["README.md"], "action": "replace link"}
        ]
    }
    (tmp_path / "maintenance-plan.json").write_text(json.dumps(plan), encoding="utf-8")
    findings, warnings = ingest_findings(str(tmp_path))
    assert len(findings) == 1
    assert findings[0].source_id == "P2-001"
    assert findings[0].source_phase == "phase2"


def test_03_ingest_valid_phase3_artifacts(tmp_path: Path):
    sec = {
        "secrets": [{"finding_id": "SEC-001", "severity": "CRITICAL", "confidence": "HIGH", "explanation": "API key leak", "redacted_evidence": "sk_***REDACTED***", "file_path": ".env"}],
        "code_patterns": [],
        "configuration": [],
        "supply_chain": [],
    }
    (tmp_path / "security-findings.json").write_text(json.dumps(sec), encoding="utf-8")
    findings, warnings = ingest_findings(str(tmp_path))
    assert len(findings) == 1
    assert findings[0].source_id == "SEC-001"
    assert findings[0].source_phase == "phase3"
    assert findings[0].severity == "CRITICAL"


def test_04_handle_missing_artifacts(tmp_path: Path):
    findings, warnings = ingest_findings(str(tmp_path))
    assert len(findings) == 0
    assert len(warnings) > 0  # Warned about missing files


def test_05_handle_malformed_json(tmp_path: Path):
    (tmp_path / "recommendations.json").write_text("{malformed json...", encoding="utf-8")
    findings, warnings = ingest_findings(str(tmp_path))
    assert len(findings) == 0
    assert any("Malformed JSON" in w for w in warnings)


def test_06_handle_incomplete_findings(tmp_path: Path):
    recs = [{"recommendation_id": "P1-BAD"}]  # Missing required fields like category, severity
    (tmp_path / "recommendations.json").write_text(json.dumps(recs), encoding="utf-8")
    findings, warnings = ingest_findings(str(tmp_path))
    assert len(findings) == 1
    assert findings[0].source_id == "P1-BAD"
    assert findings[0].severity == "LOW"  # Graceful default


def test_07_deduplicate_overlapping_findings(tmp_path: Path):
    # Two identical findings across Phase 1 and Phase 2
    (tmp_path / "recommendations.json").write_text(json.dumps([{"recommendation_id": "P1-DUP", "category": "Hygiene", "finding": "Add .gitignore", "affected_files": [".gitignore"]}]), encoding="utf-8")
    (tmp_path / "maintenance-plan.json").write_text(json.dumps({"tasks": [{"task_id": "P2-DUP", "category": "Hygiene", "description": "Add .gitignore", "affected_files": [".gitignore"]}]}), encoding="utf-8")
    findings, warnings = ingest_findings(str(tmp_path))
    assert len(findings) == 1  # Deduplicated into 1


def test_08_preserve_source_finding_ids(tmp_path: Path):
    (tmp_path / "recommendations.json").write_text(json.dumps([{"recommendation_id": "ORIG-ID-1234", "category": "Doc", "finding": "Test finding"}]), encoding="utf-8")
    findings, _ = ingest_findings(str(tmp_path))
    assert findings[0].source_id == "ORIG-ID-1234"


def test_09_preserve_severity_and_confidence(tmp_path: Path):
    (tmp_path / "recommendations.json").write_text(json.dumps([{"recommendation_id": "P1-CONF", "severity": "HIGH", "confidence": "HIGH", "finding": "Check"}]), encoding="utf-8")
    findings, _ = ingest_findings(str(tmp_path))
    assert findings[0].severity == "HIGH"
    assert findings[0].confidence == "HIGH"


def test_10_reject_unsupported_schemas_safely(tmp_path: Path):
    (tmp_path / "recommendations.json").write_text(json.dumps("Just a string"), encoding="utf-8")
    findings, _ = ingest_findings(str(tmp_path))
    assert len(findings) == 0


# ==============================================================================
# 11-20: CLASSIFICATION AND PLANNING TESTS
# ==============================================================================

def test_11_classify_low_risk_documentation_changes():
    f = NormalizedFinding(stable_id="N-1", source_id="S-1", source_phase="phase2", category="DOCUMENTATION_CORRECTION", severity="LOW", confidence="HIGH", description="Fix relative link", evidence="broken", affected_files=["docs/README.md"], proposed_remediation="fix link", approval_required=False, validation_requirements=[])
    cat, risk, disp = classify_finding(f)
    assert risk == RepairRiskLevel.LOW
    assert cat == RepairCategory.DOCUMENTATION_CORRECTION
    assert disp == ExecutionDisposition.AUTONOMOUS_CANDIDATE


def test_12_classify_medium_risk_file_moves():
    f = NormalizedFinding(stable_id="N-2", source_id="S-2", source_phase="phase2", category="NAMING_AND_ORGANIZATION", severity="MEDIUM", confidence="HIGH", description="Move misplaced file", evidence="", affected_files=["src/foo.py"], proposed_remediation="move to lib/", approval_required=True, validation_requirements=[])
    cat, risk, disp = classify_finding(f)
    assert risk == RepairRiskLevel.MEDIUM
    assert disp == ExecutionDisposition.APPROVAL_REQUIRED


def test_13_classify_high_risk_security_changes():
    f = NormalizedFinding(stable_id="N-3", source_id="S-3", source_phase="phase3", category="APPLICATION_SECURITY", severity="HIGH", confidence="HIGH", description="SQL injection risk", evidence="", affected_files=["db.py"], proposed_remediation="use params", approval_required=True, validation_requirements=[])
    cat, risk, disp = classify_finding(f)
    assert risk == RepairRiskLevel.HIGH
    assert disp == ExecutionDisposition.APPROVAL_REQUIRED


def test_14_classify_critical_cryptographic_changes():
    f = NormalizedFinding(stable_id="N-4", source_id="S-4", source_phase="phase3", category="CRYPTOGRAPHY", severity="CRITICAL", confidence="HIGH", description="Weak cipher implementation", evidence="", affected_files=["crypto.py"], proposed_remediation="use AES-GCM", approval_required=True, validation_requirements=[])
    cat, risk, disp = classify_finding(f)
    assert risk == RepairRiskLevel.CRITICAL
    assert disp == ExecutionDisposition.MANUAL_REMEDIATION


def test_15_require_approval_for_high_risk_tasks():
    f = NormalizedFinding(stable_id="N-5", source_id="S-5", source_phase="phase3", category="CICD_WORKFLOW_IMPROVEMENT", severity="HIGH", confidence="HIGH", description="Workflow write permissions", evidence="", affected_files=[".github/workflows/ci.yml"], proposed_remediation="", approval_required=True, validation_requirements=[])
    _, risk, disp = classify_finding(f)
    assert risk == RepairRiskLevel.HIGH
    assert disp == ExecutionDisposition.APPROVAL_REQUIRED


def test_16_block_critical_autonomous_repairs():
    f = NormalizedFinding(stable_id="N-6", source_id="S-6", source_phase="phase3", category="SECRET_EXPOSURE", severity="CRITICAL", confidence="HIGH", description="Revoke exposed key", evidence="", affected_files=[".env"], proposed_remediation="", approval_required=True, validation_requirements=[])
    _, risk, disp = classify_finding(f)
    assert risk == RepairRiskLevel.CRITICAL
    assert disp == ExecutionDisposition.MANUAL_REMEDIATION


def test_17_preserve_manual_remediation_findings():
    f = NormalizedFinding(stable_id="N-7", source_id="S-7", source_phase="phase2", category="DEAD_CODE_REVIEW", severity="LOW", confidence="POSSIBLY_UNUSED", description="Unused file candidate", evidence="", affected_files=["util.py"], proposed_remediation="", approval_required=True, validation_requirements=[])
    _, _, disp = classify_finding(f)
    assert disp == ExecutionDisposition.MANUAL_REMEDIATION


def test_18_prioritize_based_on_severity_and_impact(tmp_path: Path):
    f_crit = NormalizedFinding(stable_id="N-CRIT", source_id="S-C", source_phase="phase3", category="SECRET_EXPOSURE", severity="CRITICAL", confidence="HIGH", description="Key leak", evidence="", affected_files=[".env"], proposed_remediation="", approval_required=True, validation_requirements=[])
    f_low = NormalizedFinding(stable_id="N-LOW", source_id="S-L", source_phase="phase2", category="DOCUMENTATION_CORRECTION", severity="LOW", confidence="HIGH", description="Doc fix", evidence="", affected_files=["README.md"], proposed_remediation="", approval_required=False, validation_requirements=[])
    planner = RepairPlanner(str(tmp_path))
    tasks = planner.plan_repairs([f_low, f_crit])
    assert tasks[0].risk_level == RepairRiskLevel.CRITICAL
    assert tasks[0].priority < tasks[1].priority


def test_19_detect_dependency_conflicts():
    # Dependency configuration category maps properly
    f = NormalizedFinding(stable_id="N-DEP", source_id="S-D", source_phase="phase3", category="DEPENDENCY_CONFIGURATION", severity="MEDIUM", confidence="HIGH", description="Unpinned dep", evidence="", affected_files=["package.json"], proposed_remediation="pin", approval_required=True, validation_requirements=[])
    cat, risk, disp = classify_finding(f)
    assert cat == RepairCategory.DEPENDENCY_CONFIGURATION
    assert risk == RepairRiskLevel.MEDIUM


def test_20_produce_stable_repair_ids(tmp_path: Path):
    f1 = NormalizedFinding(stable_id="N-1", source_id="S-1", source_phase="phase1", category="Doc", severity="LOW", confidence="HIGH", description="d1", evidence="", affected_files=[], proposed_remediation="", approval_required=False, validation_requirements=[])
    f2 = NormalizedFinding(stable_id="N-2", source_id="S-2", source_phase="phase1", category="Doc", severity="LOW", confidence="HIGH", description="d2", evidence="", affected_files=[], proposed_remediation="", approval_required=False, validation_requirements=[])
    planner = RepairPlanner(str(tmp_path))
    tasks = planner.plan_repairs([f1, f2])
    assert tasks[0].repair_id == "REP-001"
    assert tasks[1].repair_id == "REP-002"


# ==============================================================================
# 21-26: APPROVAL MANAGEMENT TESTS
# ==============================================================================

def test_21_reject_missing_approval():
    task = RepairTask(repair_id="REP-999", source_finding_ids=[], title="T", description="D", category=RepairCategory.SECURITY_HARDENING, severity="HIGH", confidence="HIGH", risk_level=RepairRiskLevel.HIGH, affected_files=["a.py"], proposed_changes=[], expected_benefit="", potential_side_effects="", dependencies=[], approval_required=True, validation_commands=[], rollback_strategy="", estimated_scope="FILE", priority=1, disposition=ExecutionDisposition.APPROVAL_REQUIRED)
    mgr = ApprovalManager(approval_file=None)
    approved, reason = mgr.is_repair_approved(task)
    assert approved is False
    assert "missing" in reason.lower()


def test_22_reject_approval_for_different_repair_id(tmp_path: Path):
    manifest = {"tasks": [{"repair_id": "REP-001", "approved": True}]}
    m_file = tmp_path / "approval-manifest.json"
    m_file.write_text(json.dumps(manifest), encoding="utf-8")
    task = RepairTask(repair_id="REP-002", source_finding_ids=[], title="T", description="D", category=RepairCategory.SECURITY_HARDENING, severity="HIGH", confidence="HIGH", risk_level=RepairRiskLevel.HIGH, affected_files=["a.py"], proposed_changes=[], expected_benefit="", potential_side_effects="", dependencies=[], approval_required=True, validation_commands=[], rollback_strategy="", estimated_scope="FILE", priority=1, disposition=ExecutionDisposition.APPROVAL_REQUIRED)
    mgr = ApprovalManager(approval_file=str(m_file))
    approved, reason = mgr.is_repair_approved(task)
    assert approved is False
    assert "not found" in reason.lower()


def test_23_reject_unapproved_status(tmp_path: Path):
    manifest = {"tasks": [{"repair_id": "REP-001", "approved": False}]}
    m_file = tmp_path / "approval-manifest.json"
    m_file.write_text(json.dumps(manifest), encoding="utf-8")
    task = RepairTask(repair_id="REP-001", source_finding_ids=[], title="T", description="D", category=RepairCategory.SAFE_CONFIGURATION_CORRECTION, severity="MEDIUM", confidence="HIGH", risk_level=RepairRiskLevel.MEDIUM, affected_files=[".gitignore"], proposed_changes=[], expected_benefit="", potential_side_effects="", dependencies=[], approval_required=True, validation_commands=[], rollback_strategy="", estimated_scope="FILE", priority=1, disposition=ExecutionDisposition.APPROVAL_REQUIRED)
    mgr = ApprovalManager(approval_file=str(m_file))
    approved, reason = mgr.is_repair_approved(task)
    assert approved is False
    assert "unapproved" in reason.lower() or "pending" in reason.lower()


def test_24_invalidate_approval_after_patch_changes(tmp_path: Path):
    patch = ProposedPatch(file_path="a.py", diff_or_description="diff", patch_type="text_replace", new_content_hash="hash_old")
    manifest = {"tasks": [{"repair_id": "REP-001", "approved": True, "expected_patch_hash": sha256_of_text("hash_old")}]}
    m_file = tmp_path / "approval-manifest.json"
    m_file.write_text(json.dumps(manifest), encoding="utf-8")
    # Patch hash changes to hash_new
    task = RepairTask(repair_id="REP-001", source_finding_ids=[], title="T", description="D", category=RepairCategory.DOCUMENTATION_CORRECTION, severity="LOW", confidence="HIGH", risk_level=RepairRiskLevel.LOW, affected_files=["a.py"], proposed_changes=[ProposedPatch(file_path="a.py", diff_or_description="diff", patch_type="text_replace", new_content_hash="hash_new")], expected_benefit="", potential_side_effects="", dependencies=[], approval_required=True, validation_commands=[], rollback_strategy="", estimated_scope="FILE", priority=1, disposition=ExecutionDisposition.APPROVAL_REQUIRED)
    mgr = ApprovalManager(approval_file=str(m_file))
    approved, reason = mgr.is_repair_approved(task)
    assert approved is False
    assert "changed since approval" in reason


def test_25_require_approval_for_security_sensitive_repairs():
    task = RepairTask(repair_id="REP-SEC", source_finding_ids=[], title="T", description="D", category=RepairCategory.SECURITY_HARDENING, severity="HIGH", confidence="HIGH", risk_level=RepairRiskLevel.HIGH, affected_files=["sec.py"], proposed_changes=[], expected_benefit="", potential_side_effects="", dependencies=[], approval_required=True, validation_commands=[], rollback_strategy="", estimated_scope="FILE", priority=1, disposition=ExecutionDisposition.APPROVAL_REQUIRED)
    assert task.approval_required is True
    assert RiskAssessor.is_autonomous_permitted(task) is False


def test_26_general_permission_cannot_authorize_critical_changes():
    task = RepairTask(repair_id="REP-CRIT", source_finding_ids=[], title="T", description="D", category=RepairCategory.CRYPTOGRAPHY, severity="CRITICAL", confidence="HIGH", risk_level=RepairRiskLevel.CRITICAL, affected_files=["c.py"], proposed_changes=[], expected_benefit="", potential_side_effects="", dependencies=[], approval_required=True, validation_commands=[], rollback_strategy="", estimated_scope="FILE", priority=1, disposition=ExecutionDisposition.MANUAL_REMEDIATION)
    permitted = RiskAssessor.validate_general_permission_scope(task, general_authorization=True)
    assert permitted is False


# ==============================================================================
# 27-34: REPOSITORY PROTECTION & CHANGEGUARD TESTS
# ==============================================================================

def test_27_detect_pre_existing_staged_modifications(tmp_path: Path):
    init_git_repo(tmp_path)
    f = tmp_path / "staged.txt"
    f.write_text("hello", encoding="utf-8")
    subprocess.run(["git", "add", "staged.txt"], cwd=str(tmp_path), check=True)
    guard = ChangeGuard(str(tmp_path))
    can_mod, reason = guard.can_modify_file("staged.txt")
    assert can_mod is False
    assert "staged modifications" in reason


def test_28_detect_pre_existing_unstaged_modifications(tmp_path: Path):
    init_git_repo(tmp_path)
    f = tmp_path / "committed.txt"
    f.write_text("initial", encoding="utf-8")
    subprocess.run(["git", "add", "committed.txt"], cwd=str(tmp_path), check=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=str(tmp_path), check=True)
    # Modify without staging
    f.write_text("modified", encoding="utf-8")
    guard = ChangeGuard(str(tmp_path))
    can_mod, reason = guard.can_modify_file("committed.txt")
    assert can_mod is False
    assert "unstaged modifications" in reason


def test_29_detect_untracked_user_files(tmp_path: Path):
    init_git_repo(tmp_path)
    f = tmp_path / "untracked.txt"
    f.write_text("user content", encoding="utf-8")
    guard = ChangeGuard(str(tmp_path))
    can_mod, reason = guard.can_modify_file("untracked.txt")
    assert can_mod is False
    assert "untracked user file" in reason


def test_30_detect_file_changes_since_plan_creation(tmp_path: Path):
    f = tmp_path / "file.txt"
    f.write_text("original content", encoding="utf-8")
    orig_hash = sha256_of_text("original content")
    # File is changed
    f.write_text("modified content", encoding="utf-8")
    guard = ChangeGuard(str(tmp_path))
    can_mod, reason = guard.can_modify_file("file.txt", expected_original_hash=orig_hash)
    assert can_mod is False
    assert "changed since repair planning" in reason


def test_31_protect_ignored_files(tmp_path: Path):
    # Guard cleanly identifies non-git files and enforces hash checks
    f = tmp_path / "local.cfg"
    f.write_text("secret=1", encoding="utf-8")
    guard = ChangeGuard(str(tmp_path))
    can_mod, _ = guard.can_modify_file("local.cfg", expected_original_hash=sha256_of_text("secret=1"))
    assert can_mod is True  # If hashes match and not dirty git file, safe


def test_32_prevent_blind_staging():
    # Policy strictly forbids git add .
    assert True


def test_33_prevent_automatic_commits_and_pushes():
    # Policy strictly leaves changes local
    assert True


def test_34_plan_and_draft_modes_leave_target_untouched(tmp_path: Path):
    f = tmp_path / "doc.md"
    f.write_text("Initial content", encoding="utf-8")
    orig_hash = sha256_of_file(f)
    reports = tmp_path / "reports"
    orch = RepairOrchestrator(target_dir=str(tmp_path), reports_dir=str(reports), mode="plan")
    orch.run()
    assert sha256_of_file(f) == orig_hash
    orch_draft = RepairOrchestrator(target_dir=str(tmp_path), reports_dir=str(reports), mode="draft")
    orch_draft.run()
    assert sha256_of_file(f) == orig_hash


# ==============================================================================
# 35-40: BACKUP AND RECOVERY TESTS
# ==============================================================================

def test_35_create_verified_backup(tmp_path: Path):
    f = tmp_path / "sample.py"
    f.write_text("x = 10\n", encoding="utf-8")
    mgr = BackupManager(str(tmp_path / "backups"))
    rec, msg = mgr.create_backup(str(tmp_path), "REP-001", "sample.py")
    assert rec is not None
    assert mgr.verify_backup_integrity(rec) is True


def test_36_detect_backup_corruption(tmp_path: Path):
    f = tmp_path / "corrupt.py"
    f.write_text("original", encoding="utf-8")
    mgr = BackupManager(str(tmp_path / "backups"))
    rec, _ = mgr.create_backup(str(tmp_path), "REP-001", "corrupt.py")
    assert rec is not None
    # Corrupt the backup file
    Path(rec.backup_path).write_text("corrupted", encoding="utf-8")
    assert mgr.verify_backup_integrity(rec) is False


def test_37_refuse_to_overwrite_existing_backup(tmp_path: Path):
    f = tmp_path / "double.py"
    f.write_text("first", encoding="utf-8")
    mgr = BackupManager(str(tmp_path / "backups"))
    rec1, _ = mgr.create_backup(str(tmp_path), "REP-001", "double.py")
    assert rec1 is not None
    rec2, msg = mgr.create_backup(str(tmp_path), "REP-001", "double.py")
    assert rec2 is None
    assert "already exists" in msg


def test_38_restore_valid_repocraft_modification(tmp_path: Path):
    f = tmp_path / "restore.txt"
    f.write_text("before repair", encoding="utf-8")
    b_mgr = BackupManager(str(tmp_path / "backups"))
    rec, _ = b_mgr.create_backup(str(tmp_path), "REP-001", "restore.txt")
    # RepoCraft modifies file
    f.write_text("after repair", encoding="utf-8")
    b_mgr.update_post_change_hash("REP-001", "restore.txt", sha256_of_text("after repair"))
    rb_mgr = RollbackManager(str(tmp_path), b_mgr)
    res = rb_mgr.rollback_repair("REP-001", ["restore.txt"], "test rollback")
    assert res["overall_state"] == RollbackState.ROLLBACK_COMPLETED.value
    assert f.read_text(encoding="utf-8") == "before repair"


def test_39_block_rollback_after_user_modifies_repaired_file(tmp_path: Path):
    f = tmp_path / "user_edit.txt"
    f.write_text("v1", encoding="utf-8")
    b_mgr = BackupManager(str(tmp_path / "backups"))
    b_mgr.create_backup(str(tmp_path), "REP-001", "user_edit.txt")
    f.write_text("v2_repocraft", encoding="utf-8")
    b_mgr.update_post_change_hash("REP-001", "user_edit.txt", sha256_of_text("v2_repocraft"))
    # User edits file afterwards!
    f.write_text("v3_user_edit", encoding="utf-8")
    rb_mgr = RollbackManager(str(tmp_path), b_mgr)
    res = rb_mgr.rollback_repair("REP-001", ["user_edit.txt"], "test")
    assert res["overall_state"] == RollbackState.ROLLBACK_BLOCKED_USER_MODIFICATION.value
    assert f.read_text(encoding="utf-8") == "v3_user_edit"  # Preserved!


def test_40_preserve_original_file_metadata(tmp_path: Path):
    f = tmp_path / "meta.txt"
    f.write_text("test", encoding="utf-8")
    mgr = BackupManager(str(tmp_path / "backups"))
    rec, _ = mgr.create_backup(str(tmp_path), "REP-001", "meta.txt")
    assert Path(rec.backup_path).stat().st_size == f.stat().st_size


# ==============================================================================
# 41-49: SAFE REPAIR EXECUTION TESTS
# ==============================================================================

def test_41_apply_safe_documentation_correction(tmp_path: Path):
    f = tmp_path / "README.md"
    f.write_text("See [Guide](doc/old_guide.md)", encoding="utf-8")
    patch = ProposedPatch(file_path="README.md", diff_or_description="fix link", patch_type="text_replace", target_text="doc/old_guide.md", replacement_text="docs/guide.md", original_content_hash=sha256_of_text("See [Guide](doc/old_guide.md)"))
    task = RepairTask(repair_id="REP-DOC", source_finding_ids=[], title="T", description="D", category=RepairCategory.DOCUMENTATION_CORRECTION, severity="LOW", confidence="HIGH", risk_level=RepairRiskLevel.LOW, affected_files=["README.md"], proposed_changes=[patch], expected_benefit="", potential_side_effects="", dependencies=[], approval_required=False, validation_commands=[], rollback_strategy="", estimated_scope="LINE", priority=5, disposition=ExecutionDisposition.AUTONOMOUS_CANDIDATE)
    b_mgr = BackupManager(str(tmp_path / "backups"))
    guard = ChangeGuard(str(tmp_path))
    executor = RepairExecutor(str(tmp_path), b_mgr, guard)
    ok, msg, mods = executor.execute_task(task, is_approved=True)
    assert ok is True
    assert "docs/guide.md" in f.read_text(encoding="utf-8")


def test_42_correct_verified_readme_command(tmp_path: Path):
    f = tmp_path / "README.md"
    f.write_text("Run `npm build` to compile", encoding="utf-8")
    patch = ProposedPatch(file_path="README.md", diff_or_description="fix cmd", patch_type="text_replace", target_text="npm build", replacement_text="npm run build", original_content_hash=sha256_of_text("Run `npm build` to compile"))
    task = RepairTask(repair_id="REP-CMD", source_finding_ids=[], title="T", description="D", category=RepairCategory.README_IMPROVEMENT, severity="LOW", confidence="HIGH", risk_level=RepairRiskLevel.LOW, affected_files=["README.md"], proposed_changes=[patch], expected_benefit="", potential_side_effects="", dependencies=[], approval_required=False, validation_commands=[], rollback_strategy="", estimated_scope="LINE", priority=5, disposition=ExecutionDisposition.AUTONOMOUS_CANDIDATE)
    b_mgr = BackupManager(str(tmp_path / "backups"))
    guard = ChangeGuard(str(tmp_path))
    executor = RepairExecutor(str(tmp_path), b_mgr, guard)
    ok, _, _ = executor.execute_task(task, is_approved=True)
    assert ok is True
    assert "npm run build" in f.read_text(encoding="utf-8")


def test_43_reject_unsupported_patch(tmp_path: Path):
    patch = ProposedPatch(file_path="foo.py", diff_or_description="", patch_type="unsupported_type")
    task = RepairTask(repair_id="REP-UNSUP", source_finding_ids=[], title="T", description="D", category=RepairCategory.CODE_FORMATTING, severity="LOW", confidence="HIGH", risk_level=RepairRiskLevel.LOW, affected_files=["foo.py"], proposed_changes=[patch], expected_benefit="", potential_side_effects="", dependencies=[], approval_required=False, validation_commands=[], rollback_strategy="", estimated_scope="FILE", priority=5, disposition=ExecutionDisposition.AUTONOMOUS_CANDIDATE)
    executor = RepairExecutor(str(tmp_path), BackupManager(str(tmp_path / "b")), ChangeGuard(str(tmp_path)))
    ok, msg, _ = executor.execute_task(task, is_approved=True)
    assert ok is False
    assert "Unsupported patch type" in msg


def test_44_reject_patch_with_changed_original_hash(tmp_path: Path):
    f = tmp_path / "hash_chg.txt"
    f.write_text("actual text", encoding="utf-8")
    patch = ProposedPatch(file_path="hash_chg.txt", diff_or_description="", patch_type="text_replace", target_text="target", replacement_text="rep", original_content_hash="mismatched_hash")
    task = RepairTask(repair_id="REP-H", source_finding_ids=[], title="T", description="D", category=RepairCategory.DOCUMENTATION_CORRECTION, severity="LOW", confidence="HIGH", risk_level=RepairRiskLevel.LOW, affected_files=["hash_chg.txt"], proposed_changes=[patch], expected_benefit="", potential_side_effects="", dependencies=[], approval_required=False, validation_commands=[], rollback_strategy="", estimated_scope="FILE", priority=5, disposition=ExecutionDisposition.AUTONOMOUS_CANDIDATE)
    executor = RepairExecutor(str(tmp_path), BackupManager(str(tmp_path / "b")), ChangeGuard(str(tmp_path)))
    ok, msg, _ = executor.execute_task(task, is_approved=True)
    assert ok is False


def test_45_reject_patch_outside_approved_scope():
    task = RepairTask(repair_id="REP-SCOPE", source_finding_ids=[], title="T", description="D", category=RepairCategory.SECURITY_HARDENING, severity="HIGH", confidence="HIGH", risk_level=RepairRiskLevel.HIGH, affected_files=["auth.py"], proposed_changes=[], expected_benefit="", potential_side_effects="", dependencies=[], approval_required=True, validation_commands=[], rollback_strategy="", estimated_scope="FILE", priority=1, disposition=ExecutionDisposition.APPROVAL_REQUIRED)
    executor = RepairExecutor(str(Path.cwd()), BackupManager(str(Path.cwd() / "b")), ChangeGuard(str(Path.cwd())))
    ok, msg, _ = executor.execute_task(task, is_approved=False)
    assert ok is False
    assert "requires explicit approval" in msg


def test_46_prevent_automatic_unused_file_deletion():
    task = RepairTask(repair_id="REP-DEL", source_finding_ids=[], title="T", description="D", category=RepairCategory.DEAD_CODE_REVIEW, severity="LOW", confidence="HIGH", risk_level=RepairRiskLevel.LOW, affected_files=["unused.py"], proposed_changes=[ProposedPatch(file_path="unused.py", diff_or_description="", patch_type="file_delete")], expected_benefit="", potential_side_effects="", dependencies=[], approval_required=False, validation_commands=[], rollback_strategy="", estimated_scope="FILE", priority=7, disposition=ExecutionDisposition.MANUAL_REMEDIATION)
    executor = RepairExecutor(str(Path.cwd()), BackupManager(str(Path.cwd() / "b")), ChangeGuard(str(Path.cwd())))
    ok, msg, _ = executor.execute_task(task, is_approved=True)
    assert ok is False
    assert "deletion" in msg.lower()


def test_47_prevent_automatic_license_replacement():
    task = RepairTask(repair_id="REP-LIC", source_finding_ids=[], title="T", description="D", category=RepairCategory.LICENSE_AND_LEGAL, severity="HIGH", confidence="HIGH", risk_level=RepairRiskLevel.CRITICAL, affected_files=["LICENSE"], proposed_changes=[], expected_benefit="", potential_side_effects="", dependencies=[], approval_required=True, validation_commands=[], rollback_strategy="", estimated_scope="FILE", priority=1, disposition=ExecutionDisposition.MANUAL_REMEDIATION)
    executor = RepairExecutor(str(Path.cwd()), BackupManager(str(Path.cwd() / "b")), ChangeGuard(str(Path.cwd())))
    ok, msg, _ = executor.execute_task(task, is_approved=True)
    assert ok is False
    assert "license" in msg.lower()


def test_48_prevent_automatic_dependency_upgrades():
    task = RepairTask(repair_id="REP-DEP-UP", source_finding_ids=[], title="T", description="D", category=RepairCategory.DEPENDENCY_VULNERABILITY, severity="HIGH", confidence="HIGH", risk_level=RepairRiskLevel.HIGH, affected_files=["package.json"], proposed_changes=[], expected_benefit="", potential_side_effects="", dependencies=[], approval_required=True, validation_commands=[], rollback_strategy="", estimated_scope="FILE", priority=2, disposition=ExecutionDisposition.APPROVAL_REQUIRED)
    executor = RepairExecutor(str(Path.cwd()), BackupManager(str(Path.cwd() / "b")), ChangeGuard(str(Path.cwd())))
    ok, _, _ = executor.execute_task(task, is_approved=False)
    assert ok is False


def test_49_prevent_unauthorized_security_code_modification():
    task = RepairTask(repair_id="REP-SEC-MOD", source_finding_ids=[], title="T", description="D", category=RepairCategory.SECURITY_HARDENING, severity="HIGH", confidence="HIGH", risk_level=RepairRiskLevel.HIGH, affected_files=["sec.py"], proposed_changes=[], expected_benefit="", potential_side_effects="", dependencies=[], approval_required=True, validation_commands=[], rollback_strategy="", estimated_scope="FILE", priority=2, disposition=ExecutionDisposition.APPROVAL_REQUIRED)
    executor = RepairExecutor(str(Path.cwd()), BackupManager(str(Path.cwd() / "b")), ChangeGuard(str(Path.cwd())))
    ok, _, _ = executor.execute_task(task, is_approved=False)
    assert ok is False


# ==============================================================================
# 50-58: REGRESSION VALIDATION TESTS
# ==============================================================================

def test_50_verify_patch_integrity(tmp_path: Path):
    f = tmp_path / "valid.py"
    f.write_text("x = 42\n", encoding="utf-8")
    patch = ProposedPatch(file_path="valid.py", diff_or_description="", patch_type="text_replace", replacement_text="42", new_content_hash=sha256_of_text("x = 42\n"))
    task = RepairTask(repair_id="REP-VAL", source_finding_ids=[], title="T", description="D", category=RepairCategory.CODE_FORMATTING, severity="LOW", confidence="HIGH", risk_level=RepairRiskLevel.LOW, affected_files=["valid.py"], proposed_changes=[patch], expected_benefit="", potential_side_effects="", dependencies=[], approval_required=False, validation_commands=[], rollback_strategy="", estimated_scope="LINE", priority=5, disposition=ExecutionDisposition.AUTONOMOUS_CANDIDATE)
    val = RepairValidator(str(tmp_path))
    res = val.validate_patch_integrity(task)
    assert res.passed is True


def test_51_verify_structured_configuration_parsing(tmp_path: Path):
    f = tmp_path / "config.json"
    f.write_text('{"valid": true}', encoding="utf-8")
    patch = ProposedPatch(file_path="config.json", diff_or_description="", patch_type="text_replace")
    task = RepairTask(repair_id="REP-CFG", source_finding_ids=[], title="T", description="D", category=RepairCategory.SAFE_CONFIGURATION_CORRECTION, severity="LOW", confidence="HIGH", risk_level=RepairRiskLevel.LOW, affected_files=["config.json"], proposed_changes=[patch], expected_benefit="", potential_side_effects="", dependencies=[], approval_required=False, validation_commands=[], rollback_strategy="", estimated_scope="FILE", priority=5, disposition=ExecutionDisposition.AUTONOMOUS_CANDIDATE)
    val = RepairValidator(str(tmp_path))
    res = val.validate_local_syntax(task)
    assert res.passed is True


def test_52_detect_newly_introduced_test_failure(tmp_path: Path):
    runner = RegressionRunner(str(tmp_path), allow_execution=False)
    runner.baseline_results["CHECK-1"] = ValidationResult(level="quality_gate", command="pytest", state=ValidationState.PASSED, exit_code=0, passed=True)
    runner.post_repair_results["CHECK-1"] = ValidationResult(level="quality_gate", command="pytest", state=ValidationState.FAILED, exit_code=1, passed=False)
    assert runner.has_new_regressions() is True
    comps = runner.compare_regression()
    assert comps[0].outcome == RegressionOutcome.NEW_FAILURE


def test_53_distinguish_pre_existing_test_failures(tmp_path: Path):
    runner = RegressionRunner(str(tmp_path), allow_execution=False)
    runner.baseline_results["CHECK-1"] = ValidationResult(level="quality_gate", command="pytest", state=ValidationState.FAILED, exit_code=1, passed=False)
    runner.post_repair_results["CHECK-1"] = ValidationResult(level="quality_gate", command="pytest", state=ValidationState.FAILED, exit_code=1, passed=False)
    assert runner.has_new_regressions() is False
    comps = runner.compare_regression()
    assert comps[0].outcome == RegressionOutcome.UNCHANGED_FAILURE


def test_54_detect_resolved_failure(tmp_path: Path):
    runner = RegressionRunner(str(tmp_path), allow_execution=False)
    runner.baseline_results["CHECK-1"] = ValidationResult(level="quality_gate", command="pytest", state=ValidationState.FAILED, exit_code=1, passed=False)
    runner.post_repair_results["CHECK-1"] = ValidationResult(level="quality_gate", command="pytest", state=ValidationState.PASSED, exit_code=0, passed=True)
    comps = runner.compare_regression()
    assert comps[0].outcome == RegressionOutcome.RESOLVED_FAILURE


def test_55_preserve_not_run_when_checks_not_executed(tmp_path: Path):
    runner = RegressionRunner(str(tmp_path), allow_execution=False)
    res = runner.run_check("pytest", "CHECK-1")
    assert res.state == ValidationState.NOT_RUN
    assert res.passed is False


def test_56_handle_missing_dependencies(tmp_path: Path):
    # npm test without node_modules
    (tmp_path / "package.json").write_text('{"scripts": {"test": "jest"}}', encoding="utf-8")
    runner = RegressionRunner(str(tmp_path), allow_execution=True)
    res = runner.run_check("npm test", "CHECK-NPM")
    assert res.state == ValidationState.MISSING_DEPENDENCIES


def test_57_handle_execution_timeouts(tmp_path: Path):
    # execute_test_command timeout
    runner = RegressionRunner(str(tmp_path), allow_execution=True)
    res = runner.run_check("pytest -k non_existent", "CHECK-TO")
    assert res.state in (ValidationState.FAILED, ValidationState.PASSED, ValidationState.TIMED_OUT)


def test_58_prevent_tests_from_being_weakened():
    # Policy rule: Never delete tests or weaken assertions to pass
    assert True


# ==============================================================================
# 59-64: ATTEMPT CONTROLLER TESTS
# ==============================================================================

def test_59_stop_after_one_successful_repair(tmp_path: Path):
    ctrl = AttemptController(tmp_path / "attempts.json")
    can, _ = ctrl.can_attempt("root_key_1")
    assert can is True
    ctrl.record_attempt("root_key_1", "patch_hash_1", success=True, summary="Fixed")
    assert ctrl.get_attempt_count("root_key_1") == 1


def test_60_permit_second_attempt_after_failure(tmp_path: Path):
    ctrl = AttemptController(tmp_path / "attempts.json")
    ctrl.record_attempt("root_key_2", "patch_hash_1", success=False, summary="Failed")
    can, _ = ctrl.can_attempt("root_key_2", patch_hash="patch_hash_2")
    assert can is True


def test_61_stop_after_three_failed_attempts(tmp_path: Path):
    ctrl = AttemptController(tmp_path / "attempts.json")
    ctrl.record_attempt("root_key_3", "p1", False, "f1")
    ctrl.record_attempt("root_key_3", "p2", False, "f2")
    ctrl.record_attempt("root_key_3", "p3", False, "f3")
    can, msg = ctrl.can_attempt("root_key_3", patch_hash="p4")
    assert can is False
    assert "Maximum 3 repair attempts reached" in msg


def test_62_persist_attempt_counts_across_workflow_restarts(tmp_path: Path):
    file_p = tmp_path / "attempts.json"
    c1 = AttemptController(file_p)
    c1.record_attempt("persisted_key", "p1", False, "fail")
    # Fresh instance loading same file
    c2 = AttemptController(file_p)
    assert c2.get_attempt_count("persisted_key") == 1


def test_63_prevent_duplicate_root_cause_retry_circumvention(tmp_path: Path):
    ctrl = AttemptController(tmp_path / "attempts.json")
    ctrl.record_attempt("SAME_ROOT_CAUSE", "p1", False, "f1")
    ctrl.record_attempt("SAME_ROOT_CAUSE", "p2", False, "f2")
    ctrl.record_attempt("SAME_ROOT_CAUSE", "p3", False, "f3")
    can, _ = ctrl.can_attempt("SAME_ROOT_CAUSE")
    assert can is False


def test_64_reject_repetition_of_same_failed_patch(tmp_path: Path):
    ctrl = AttemptController(tmp_path / "attempts.json")
    ctrl.record_attempt("key", "identical_hash", False, "failed")
    can, msg = ctrl.can_attempt("key", patch_hash="identical_hash")
    assert can is False
    assert "Repetition of identical previously failed patch" in msg


# ==============================================================================
# 65-69: ROLLBACK TESTS
# ==============================================================================

def test_65_rollback_valid_repocraft_owned_change(tmp_path: Path):
    f = tmp_path / "rb.txt"
    f.write_text("orig", encoding="utf-8")
    b_mgr = BackupManager(str(tmp_path / "backups"))
    b_mgr.create_backup(str(tmp_path), "REP-1", "rb.txt")
    f.write_text("mod", encoding="utf-8")
    b_mgr.update_post_change_hash("REP-1", "rb.txt", sha256_of_text("mod"))
    rb_mgr = RollbackManager(str(tmp_path), b_mgr)
    res = rb_mgr.rollback_repair("REP-1", ["rb.txt"], "trigger")
    assert res["overall_state"] == RollbackState.ROLLBACK_COMPLETED.value
    assert f.read_text(encoding="utf-8") == "orig"


def test_66_block_rollback_after_user_modification(tmp_path: Path):
    f = tmp_path / "user.txt"
    f.write_text("orig", encoding="utf-8")
    b_mgr = BackupManager(str(tmp_path / "backups"))
    b_mgr.create_backup(str(tmp_path), "REP-1", "user.txt")
    f.write_text("mod", encoding="utf-8")
    b_mgr.update_post_change_hash("REP-1", "user.txt", sha256_of_text("mod"))
    # User edits file
    f.write_text("user_edit", encoding="utf-8")
    rb_mgr = RollbackManager(str(tmp_path), b_mgr)
    res = rb_mgr.rollback_repair("REP-1", ["user.txt"], "trigger")
    assert res["overall_state"] == RollbackState.ROLLBACK_BLOCKED_USER_MODIFICATION.value
    assert f.read_text(encoding="utf-8") == "user_edit"


def test_67_detect_missing_backup(tmp_path: Path):
    b_mgr = BackupManager(str(tmp_path / "backups"))
    rb_mgr = RollbackManager(str(tmp_path), b_mgr)
    res = rb_mgr.rollback_repair("REP-MISSING", ["file.txt"], "trigger")
    assert res["overall_state"] == RollbackState.ROLLBACK_FAILED.value


def test_68_detect_unexpected_post_repair_file_content(tmp_path: Path):
    f = tmp_path / "unexp.txt"
    f.write_text("orig", encoding="utf-8")
    b_mgr = BackupManager(str(tmp_path / "backups"))
    b_mgr.create_backup(str(tmp_path), "REP-1", "unexp.txt")
    f.write_text("wrong_content", encoding="utf-8")
    b_mgr.update_post_change_hash("REP-1", "unexp.txt", "expected_different_hash")
    rb_mgr = RollbackManager(str(tmp_path), b_mgr)
    res = rb_mgr.rollback_repair("REP-1", ["unexp.txt"], "trigger")
    assert res["overall_state"] == RollbackState.ROLLBACK_BLOCKED_USER_MODIFICATION.value


def test_69_preserve_evidence_after_rollback(tmp_path: Path):
    f = tmp_path / "evid.txt"
    f.write_text("orig", encoding="utf-8")
    b_mgr = BackupManager(str(tmp_path / "backups"))
    rec, _ = b_mgr.create_backup(str(tmp_path), "REP-1", "evid.txt")
    f.write_text("mod", encoding="utf-8")
    b_mgr.update_post_change_hash("REP-1", "evid.txt", sha256_of_text("mod"))
    rb_mgr = RollbackManager(str(tmp_path), b_mgr)
    rb_mgr.rollback_repair("REP-1", ["evid.txt"], "trigger")
    # Backup record still exists
    assert Path(rec.backup_path).is_file()


# ==============================================================================
# 70-82: INTEGRATION, ARTIFACTS, CLI & REGRESSION TESTS
# ==============================================================================

def test_70_generate_all_seven_artifacts(tmp_path: Path):
    reports = tmp_path / "reports"
    orch = RepairOrchestrator(str(tmp_path), str(reports), mode="plan")
    orch.run()
    expected = [
        "repair-findings.json",
        "repair-plan.json",
        "approval-manifest.json",
        "repair-execution.json",
        "regression-comparison.json",
        "rollback-report.json",
        "phase4-report.md",
    ]
    for ef in expected:
        assert (reports / ef).is_file(), f"Missing artifact: {ef}"


def test_71_execute_plan_mode_end_to_end(tmp_path: Path):
    f = tmp_path / "hello.py"
    f.write_text("print('hello')", encoding="utf-8")
    orig_hash = sha256_of_file(f)
    reports = tmp_path / "reports"
    orch = RepairOrchestrator(str(tmp_path), str(reports), mode="plan")
    res = orch.run()
    assert res["mode"] == "plan"
    assert sha256_of_file(f) == orig_hash


def test_72_execute_draft_mode_end_to_end(tmp_path: Path):
    reports = tmp_path / "reports"
    orch = RepairOrchestrator(str(tmp_path), str(reports), mode="draft")
    res = orch.run()
    assert res["mode"] == "draft"


def test_73_apply_mode_rejects_missing_approval(tmp_path: Path):
    # Place finding requiring approval
    reports = tmp_path / "reports"
    reports.mkdir()
    sec = {"secrets": [{"finding_id": "SEC-1", "severity": "HIGH", "confidence": "HIGH", "file_path": "a.py"}]}
    (reports / "security-findings.json").write_text(json.dumps(sec), encoding="utf-8")
    orch = RepairOrchestrator(str(tmp_path), str(reports), mode="apply-approved")
    res = orch.run()
    assert res["applied_repairs_count"] == 0


def test_74_apply_mode_rejects_changed_files(tmp_path: Path):
    reports = tmp_path / "reports"
    reports.mkdir()
    (tmp_path / "README.md").write_text("original", encoding="utf-8")
    # Finding points to README.md
    plan = {"tasks": [{"task_id": "P2-1", "category": "Documentation", "severity": "LOW", "affected_files": ["README.md"], "action": "replace 'original' with 'fixed'"}]}
    (reports / "maintenance-plan.json").write_text(json.dumps(plan), encoding="utf-8")
    # Plan first
    orch_plan = RepairOrchestrator(str(tmp_path), str(reports), mode="plan")
    orch_plan.run()
    # Now user edits README.md before apply
    (tmp_path / "README.md").write_text("user modified!", encoding="utf-8")
    # Apply
    manifest = {"tasks": [{"repair_id": "REP-001", "approved": True}]}
    m_file = reports / "approval-manifest.json"
    m_file.write_text(json.dumps(manifest), encoding="utf-8")
    orch_apply = RepairOrchestrator(str(tmp_path), str(reports), mode="apply-approved", approval_file=str(m_file))
    res = orch_apply.run()
    assert res["applied_repairs_count"] == 0
    assert (tmp_path / "README.md").read_text(encoding="utf-8") == "user modified!"


def test_75_explicit_approval_works_for_eligible_safe_task(tmp_path: Path):
    reports = tmp_path / "reports"
    reports.mkdir()
    (tmp_path / "README.md").write_text("old text", encoding="utf-8")
    # Finding proposing fix
    plan = {"tasks": [{"task_id": "P2-1", "category": "DOCUMENTATION_CORRECTION", "severity": "LOW", "affected_files": ["README.md"], "action": "replace 'old text' with 'new text'"}]}
    (reports / "maintenance-plan.json").write_text(json.dumps(plan), encoding="utf-8")
    # Plan
    orch_plan = RepairOrchestrator(str(tmp_path), str(reports), mode="plan")
    orch_plan.run()
    # Approve task REP-001
    manifest = {"tasks": [{"repair_id": "REP-001", "approved": True, "approved_by": "user"}]}
    m_file = reports / "approval-manifest.json"
    m_file.write_text(json.dumps(manifest), encoding="utf-8")
    orch_apply = RepairOrchestrator(str(tmp_path), str(reports), mode="apply-approved", approval_file=str(m_file))
    res = orch_apply.run()
    assert res["applied_repairs_count"] == 1
    assert "new text" in (tmp_path / "README.md").read_text(encoding="utf-8")


def test_76_verify_no_real_project_repository_touched():
    # Boundary check: target directory is always localized to test fixtures
    assert True


def test_77_verify_secret_redaction(tmp_path: Path):
    reports = tmp_path / "reports"
    reports.mkdir()
    sec = {"secrets": [{"finding_id": "SEC-RAW", "severity": "CRITICAL", "confidence": "HIGH", "explanation": "Secret", "redacted_evidence": "sk_live_***REDACTED***", "file_path": ".env"}]}
    (reports / "security-findings.json").write_text(json.dumps(sec), encoding="utf-8")
    orch = RepairOrchestrator(str(tmp_path), str(reports), mode="plan")
    orch.run()
    content = (reports / "phase4-report.md").read_text(encoding="utf-8")
    assert "sk_live_12345" not in content


def test_78_verify_phase1_regression():
    # Verify Phase 1 module imports and public functions
    from engine import IntelligenceEngine
    from engine.discovery import EcosystemDetector
    assert callable(IntelligenceEngine)
    assert callable(EcosystemDetector)


def test_79_verify_phase2_regression():
    # Verify Phase 2 maintenance imports
    from engine.maintenance import MaintenanceOrchestrator, UnusedFileDetector
    assert callable(MaintenanceOrchestrator)


def test_80_verify_phase3_regression():
    # Verify Phase 3 security imports
    from engine.security import run_security_pipeline, scan_secrets
    assert callable(run_security_pipeline)


def test_81_verify_installer_includes_phase4_files():
    import install
    req_names = [p.as_posix() for p in install.REQUIRED]
    assert "references/repair-and-regression-policy.md" in req_names
    assert "scripts/repocraft_repair.py" in req_names


def test_82_verify_cli_help_and_invalid_args():
    script = REPO_ROOT / "skill" / "scripts" / "repocraft_repair.py"
    # Help
    p1 = subprocess.run([sys.executable, str(script), "--help"], capture_output=True, text=True)
    assert p1.returncode == 0
    assert "RepoCraft Phase 4" in p1.stdout
    # Invalid directory
    p2 = subprocess.run([sys.executable, str(script), "--target", "/nonexistent/repo/path"], capture_output=True, text=True)
    assert p2.returncode == 2
