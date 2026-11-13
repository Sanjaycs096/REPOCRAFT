"""Tests 13-18: Phase registry contracts, entry points, and dependency graph."""
from __future__ import annotations

import json
from pathlib import Path
import pytest

from engine.integration import (
    DependencyGraph,
    LifecyclePhase,
    PhaseContract,
    PhaseRegistry,
)


def test_13_register_all_phase_entry_points():
    """Verify all phases 0 through 6 are registered with valid CLI entry points."""
    phases = PhaseRegistry.list_all()
    assert len(phases) >= 7

    expected_phases = [
        ("phase_0_init", "install.py"),
        ("phase_1_intel", "skill/scripts/repocraft_intel.py"),
        ("phase_2_maintenance", "skill/scripts/repocraft_maintenance.py"),
        ("phase_3_security", "skill/scripts/repocraft_security.py"),
        ("phase_4_repair", "skill/scripts/repocraft_repair.py"),
        ("phase_5_git_review", "skill/scripts/repocraft_git.py"),
        ("phase_6_release", "skill/scripts/repocraft_status.py"),
    ]

    for p_id, expected_entry in expected_phases:
        contract = PhaseRegistry.get(p_id)
        assert contract is not None, f"Phase {p_id} not registered"
        assert contract.cli_entry_point == expected_entry
        assert contract.schema_version == "1.0.0"
        assert contract.safety_policy != ""


def test_14_detect_missing_phase():
    """Querying an unknown phase ID returns None."""
    assert PhaseRegistry.get("phase_999_nonexistent") is None
    assert PhaseRegistry.get("") is None


def test_15_get_producing_phase_for_artifact():
    """Verify mapping from artifact filename back to producing phase."""
    p_intel = PhaseRegistry.get_producing_phase_for_artifact("inventory.json")
    assert p_intel is not None
    assert p_intel.phase_id == "phase_1_intel"

    p_repair = PhaseRegistry.get_producing_phase_for_artifact("approval-manifest.json")
    assert p_repair is not None
    assert p_repair.phase_id == "phase_4_repair"

    p_git = PhaseRegistry.get_producing_phase_for_artifact("git-state.json")
    assert p_git is not None
    assert p_git.phase_id == "phase_5_git_review"

    assert PhaseRegistry.get_producing_phase_for_artifact("random_unknown.file") is None


def test_16_phase_registry_serialization():
    """Verify phase registry export to JSON matches schema."""
    data = PhaseRegistry.to_dict()
    assert data["schema_version"] == "1.0.0"
    assert "phase_1_intel" in data["phases"]
    serialized = json.dumps(data)
    loaded = json.loads(serialized)
    assert loaded["phases"]["phase_1_intel"]["safety_policy"] == "repository-intelligence.md"


def test_17_dependency_graph_prerequisites(tmp_path: Path):
    """Verify topological dependencies of phases."""
    # Phase 2 requires Phase 1
    assert "phase_1_intel" in DependencyGraph.get_prerequisites("phase_2_maintenance")

    # In empty reports dir, Phase 2 prerequisites are not satisfied
    reports = tmp_path / "reports"
    reports.mkdir()
    ok, missing = DependencyGraph.check_prerequisites_satisfied("phase_2_maintenance", reports)
    assert ok is False
    assert "inventory.json" in missing

    # After placing inventory.json and repository-overview.md, it is satisfied
    (reports / "inventory.json").write_text("{}", encoding="utf-8")
    (reports / "repository-overview.md").write_text("# Overview", encoding="utf-8")
    ok, missing = DependencyGraph.check_prerequisites_satisfied("phase_2_maintenance", reports)
    assert ok is True
    assert len(missing) == 0


def test_18_canonical_execution_order():
    """Verify canonical ordered lifecycle phase sequence."""
    order = DependencyGraph.get_execution_order()
    assert order[0] == "phase_0_init"
    assert order[1] == "phase_1_intel"
    assert order[2] == "phase_2_maintenance"
    assert order[3] == "phase_3_security"
    assert order[4] == "phase_4_repair"
    assert order[5] == "phase_5_git_review"
    assert order[-1] == "phase_6_release"


def test_18b_all_phases_have_safety_policies():
    """Verify every registered phase specifies a mandatory reference safety policy."""
    for phase in PhaseRegistry.list_all():
        assert phase.safety_policy.endswith(".md")
        assert len(phase.safety_policy) > 3


def test_18c_all_phases_have_supported_modes():
    """Verify every registered phase specifies at least one supported operating mode."""
    for phase in PhaseRegistry.list_all():
        assert len(phase.supported_modes) >= 1
        assert "default" in phase.supported_modes or len(phase.supported_modes) > 0


def test_18d_phase_4_prerequisites_dag():
    """Verify Phase 4 DAG explicitly requires Phase 1, Phase 2, and Phase 3."""
    reqs = DependencyGraph.get_prerequisites("phase_4_repair")
    assert "phase_1_intel" in reqs
    assert "phase_2_maintenance" in reqs
    assert "phase_3_security" in reqs


def test_18e_phase_5_publish_prerequisites():
    """Verify Phase 5 publishing explicitly depends on Phase 5 Git review."""
    reqs = DependencyGraph.get_prerequisites("phase_5_publish")
    assert "phase_5_git_review" in reqs

