"""Regression tests for RepoCraft Self-Verification Gate design and overall status calculations.

Verifies:
1. calculate_overall_status strict evaluation logic:
   - Any mandatory gate FAIL -> 'FAIL'
   - Any mandatory gate BLOCKED -> 'BLOCKED'
   - Any mandatory gate NOT_RUN -> 'INCOMPLETE' (prevents full PASS)
   - All mandatory gates PASS -> 'PASS'
2. GATE_12_AUTOMATED_TESTS is mandatory.
3. Without --run-tests, Gate 12 reports NOT_RUN and overall status is INCOMPLETE (exit code 2).
4. Machine-readable JSON output contains exact status values.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SELFCHECK_SCRIPT = REPO_ROOT / "skill" / "scripts" / "repocraft_selfcheck.py"

# Add skill/scripts to sys.path to import calculate_overall_status and CheckStatus directly
SCRIPTS_DIR = REPO_ROOT / "skill" / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from repocraft_selfcheck import CheckStatus, calculate_overall_status


def test_calculate_overall_status_all_pass():
    """All mandatory gates passing yields PASS."""
    gates = {
        "G1": {"status": "PASS", "mandatory": True},
        "G2": {"status": "PASS", "mandatory": True},
        "G3": {"status": "PASS", "mandatory": False},
    }
    assert calculate_overall_status(gates) == "PASS"


def test_calculate_overall_status_mandatory_not_run_prevents_pass():
    """A mandatory NOT_RUN gate must prevent a full PASS result and return INCOMPLETE."""
    gates = {
        "G1": {"status": "PASS", "mandatory": True},
        "G2": {"status": "PASS", "mandatory": True},
        "GATE_12_AUTOMATED_TESTS": {"status": "NOT_RUN", "mandatory": True},
    }
    assert calculate_overall_status(gates) == "INCOMPLETE"


def test_calculate_overall_status_mandatory_fail_precedence():
    """A mandatory FAIL overrides NOT_RUN and returns FAIL."""
    gates = {
        "G1": {"status": "PASS", "mandatory": True},
        "G2": {"status": "FAIL", "mandatory": True},
        "G3": {"status": "NOT_RUN", "mandatory": True},
    }
    assert calculate_overall_status(gates) == "FAIL"


def test_calculate_overall_status_mandatory_blocked_precedence():
    """A mandatory BLOCKED overrides NOT_RUN when no gate has failed."""
    gates = {
        "G1": {"status": "PASS", "mandatory": True},
        "G2": {"status": "BLOCKED", "mandatory": True},
        "G3": {"status": "NOT_RUN", "mandatory": True},
    }
    assert calculate_overall_status(gates) == "BLOCKED"


def test_calculate_overall_status_optional_gate_ignored():
    """Optional non-mandatory gates do not block PASS if all mandatory pass."""
    gates = {
        "G1": {"status": "PASS", "mandatory": True},
        "G2": {"status": "PASS", "mandatory": True},
        "OPTIONAL_GATE": {"status": "NOT_RUN", "mandatory": False},
    }
    assert calculate_overall_status(gates) == "PASS"


def test_selfcheck_cli_without_run_tests_returns_incomplete(tmp_path: Path):
    """Running selfcheck without --run-tests must report NOT_RUN on Gate 12 and exit code 2 (INCOMPLETE)."""
    out_dir = tmp_path / "reports"
    cmd = [
        sys.executable, str(SELFCHECK_SCRIPT),
        "--target", str(REPO_ROOT),
        "--output", str(out_dir),
        "--json",
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, check=False)
    assert res.returncode == 2, f"Expected exit code 2 (INCOMPLETE), got {res.returncode}: {res.stderr}"

    data = json.loads(res.stdout)
    assert data["overall_status"] == "INCOMPLETE"
    assert data["summary"]["not_run"] == 1
    assert data["gates"]["GATE_12_AUTOMATED_TESTS"]["status"] == "NOT_RUN"
    assert data["gates"]["GATE_12_AUTOMATED_TESTS"]["mandatory"] is True


def test_selfcheck_cli_text_mode_incomplete_banner(tmp_path: Path):
    """Text output without --run-tests displays INCOMPLETE banner."""
    out_dir = tmp_path / "reports"
    cmd = [
        sys.executable, str(SELFCHECK_SCRIPT),
        "--target", str(REPO_ROOT),
        "--output", str(out_dir),
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, check=False)
    assert res.returncode == 2
    assert "RepoCraft Self-Verification Gate —" in res.stdout
    assert "INCOMPLETE" in res.stdout
    assert "GATE_12_AUTOMATED_TESTS" in res.stdout
