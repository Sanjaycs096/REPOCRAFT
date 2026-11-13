"""Tests for release notes and public announcement generators."""

from __future__ import annotations

from pathlib import Path
import pytest

from engine.distribution.distribution_types import ReleaseClassification
from engine.distribution.release_notes_generator import ReleaseNotesGenerator
from engine.distribution.announcement_generator import AnnouncementGenerator


REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def test_scenario_11_generate_release_notes_from_phase_metadata():
    """Scenario 11: Release notes draft generation from phase metadata."""
    notes = ReleaseNotesGenerator.generate_release_notes(REPO_ROOT, version="1.0.0-rc1")

    assert notes.version == "1.0.0-rc1"
    assert notes.release_date is not None
    assert ReleaseClassification.ADDED.value in notes.changes
    assert ReleaseClassification.SECURITY.value in notes.changes

    added_entries = notes.changes[ReleaseClassification.ADDED.value]
    # Check that all 8 phases (Phase 0 to Phase 7) are represented
    phases_found = {entry.summary for entry in added_entries}
    for phase_num in range(8):
        assert any(f"Phase {phase_num}" in p for p in phases_found), f"Phase {phase_num} missing from release notes"

    # Format as markdown
    md = ReleaseNotesGenerator.render_markdown(notes)
    assert f"RepoCraft {notes.version} Release Notes" in md
    assert "Gate E Safety Invariant" in md
    assert "Pure Standard Library Runtime" in md
    assert "Phase 7" in md


def test_scenario_12_generate_release_announcement_draft():
    """Scenario 12: Release announcement draft generation."""
    notes = ReleaseNotesGenerator.generate_release_notes(REPO_ROOT, version="1.0.0-rc1")
    announcement_md = AnnouncementGenerator.generate_announcement(notes)

    assert "Announcing RepoCraft 1.0.0-rc1" in announcement_md
    assert "What's in this Release Candidate?" in announcement_md
    assert "Core Safety Guarantees" in announcement_md
    assert "Quick Start" in announcement_md
    assert "install.py" in announcement_md
    assert "Gate E" in announcement_md
