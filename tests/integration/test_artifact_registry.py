"""Tests 19-27: Artifact registry contracts, schema validation, and sensitivity models."""
from __future__ import annotations

import json
from pathlib import Path
import pytest

from engine.integration import (
    ArtifactContract,
    ArtifactRegistry,
    ArtifactSensitivity,
    SchemaValidator,
)


def test_19_validate_artifact_registry_entries():
    """Verify registry contains all expected artifacts across phases."""
    all_artifacts = ArtifactRegistry.list_all()
    assert len(all_artifacts) >= 25

    expected_samples = [
        "inventory.json",
        "maintenance-plan.json",
        "security-findings.json",
        "repair-plan.json",
        "git-state.json",
        "staging-approval.json",
        "commit-receipt.json",
        "agent-compatibility.json",
        "release-manifest.json",
    ]
    for sample in expected_samples:
        art = ArtifactRegistry.get(sample)
        assert art is not None, f"Artifact {sample} not in registry"
        assert art.schema_version == "1.0.0"
        assert len(art.required_fields) > 0


def test_20_detect_malformed_artifact(tmp_path: Path):
    """Detect malformed JSON syntax in artifact."""
    bad_json = tmp_path / "inventory.json"
    bad_json.write_text("{ unclosed json: ", encoding="utf-8")
    is_valid, errors, warnings = SchemaValidator.validate_file(bad_json)
    assert is_valid is False
    assert any("corrupted" in err.lower() or "unparseable" in err.lower() for err in errors)


def test_21_detect_missing_required_fields(tmp_path: Path):
    """Detect JSON artifact that lacks required fields."""
    incomplete = tmp_path / "inventory.json"
    # inventory.json requires schema_version, generated_at, target_root, files_count
    incomplete.write_text(json.dumps({"schema_version": "1.0.0"}), encoding="utf-8")
    is_valid, errors, warnings = SchemaValidator.validate_file(incomplete)
    assert is_valid is False
    assert any("files_count" in err for err in errors)


def test_22_validate_intact_artifact(tmp_path: Path):
    """Validate correctly formed artifact passes schema checks."""
    valid_file = tmp_path / "inventory.json"
    valid_file.write_text(
        json.dumps({
            "schema_version": "1.0.0",
            "generated_at": "2026-01-01T00:00:00Z",
            "target_root": str(tmp_path),
            "files_count": 10,
        }),
        encoding="utf-8",
    )
    is_valid, errors, warnings = SchemaValidator.validate_file(valid_file)
    assert is_valid is True
    assert len(errors) == 0


def test_23_non_json_markdown_artifacts(tmp_path: Path):
    """Validate non-empty markdown artifacts pass while empty ones fail."""
    empty_md = tmp_path / "repository-overview.md"
    empty_md.write_text("", encoding="utf-8")
    ok, errs, _ = SchemaValidator.validate_file(empty_md)
    assert ok is False

    valid_md = tmp_path / "git-change-review.md"
    valid_md.write_text("# Review\nSome content", encoding="utf-8")
    ok, errs, _ = SchemaValidator.validate_file(valid_md)
    assert ok is True


def test_24_artifact_sensitivity_classification():
    """Verify security findings are classified SENSITIVE_REDACTED."""
    sec_findings = ArtifactRegistry.get("security-findings.json")
    assert sec_findings is not None
    assert sec_findings.data_sensitivity == ArtifactSensitivity.SENSITIVE_REDACTED

    inv = ArtifactRegistry.get("inventory.json")
    assert inv is not None
    assert inv.data_sensitivity == ArtifactSensitivity.INTERNAL

    rec = ArtifactRegistry.get("recommendations.json")
    assert rec is not None
    assert rec.data_sensitivity == ArtifactSensitivity.PUBLIC


def test_25_list_artifacts_by_phase():
    """Verify filtering artifacts by producing phase."""
    p3_artifacts = ArtifactRegistry.list_by_phase("phase_3_security")
    p3_filenames = [a.filename for a in p3_artifacts]
    assert "security-findings.json" in p3_filenames
    assert "dependency-audit.json" in p3_filenames
    assert "test-analysis.json" in p3_filenames
    assert "inventory.json" not in p3_filenames


def test_26_directory_validation(tmp_path: Path):
    """Validate all artifacts in a directory at once."""
    reports = tmp_path / "reports"
    reports.mkdir()
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

    res = SchemaValidator.validate_directory(reports)
    assert "inventory.json" in res
    assert res["inventory.json"]["is_valid"] is True
    assert "repository-overview.md" in res
    assert res["repository-overview.md"]["is_valid"] is True


def test_26b_missing_schema_version_warning(tmp_path: Path):
    """Verify warning is emitted if schema_version is omitted in JSON artifact."""
    art = tmp_path / "recommendations.json"
    art.write_text(json.dumps({"recommendations": []}), encoding="utf-8")
    is_valid, errors, warnings = SchemaValidator.validate_file(art)
    assert any("schema_version" in w.lower() for w in warnings)


def test_26c_non_dict_root_rejected(tmp_path: Path):
    """Verify JSON array at root of artifact is rejected."""
    art = tmp_path / "inventory.json"
    art.write_text(json.dumps(["item1", "item2"]), encoding="utf-8")
    is_valid, errors, warnings = SchemaValidator.validate_file(art)
    assert is_valid is False
    assert any("object" in err.lower() for err in errors)


def test_26d_non_existent_file_rejected(tmp_path: Path):
    """Verify non-existent file returns error."""
    missing = tmp_path / "does_not_exist.json"
    is_valid, errors, warnings = SchemaValidator.validate_file(missing)
    assert is_valid is False
    assert any("not found" in err.lower() for err in errors)


def test_26e_all_artifacts_have_descriptions():
    """Verify every registered artifact defines a descriptive purpose."""
    for art in ArtifactRegistry.list_all():
        assert len(art.description) > 5

