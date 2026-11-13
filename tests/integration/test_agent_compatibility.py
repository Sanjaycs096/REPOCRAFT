"""Tests 01-12: Agent compatibility detection, validation, and capability matrix."""
from __future__ import annotations

import json
from pathlib import Path
import pytest

from engine.compatibility import (
    AgentDetector,
    AgentRegistry,
    AgentSupportLevel,
    CapabilityMatrix,
    CompatibilityReportGenerator,
    CompatibilityValidator,
    InstallationAdapter,
    InvocationAdapter,
)


def test_01_detect_antigravity(tmp_path: Path):
    """Detect Antigravity project marker .agent/skills/repocraft."""
    agent_dir = tmp_path / ".agent" / "skills" / "repocraft"
    agent_dir.mkdir(parents=True)
    res = AgentDetector.detect(tmp_path)
    assert res.detected_agent == "antigravity"
    assert res.confidence == 1.0
    assert ".agent/skills/repocraft" in res.indicator_paths


def test_02_validate_antigravity_skill_structure(tmp_path: Path):
    """Validate intact Antigravity skill layout with valid frontmatter, references, and scripts."""
    skill_dir = tmp_path / ".agent" / "skills" / "repocraft"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text("---\nname: repocraft\ndescription: test\n---\n# RepoCraft\n", encoding="utf-8")
    ref_dir = skill_dir / "references"
    ref_dir.mkdir()
    for policy in CompatibilityValidator.REQUIRED_POLICIES:
        (ref_dir / policy).write_text("# Policy\n", encoding="utf-8")
    scripts_dir = skill_dir / "scripts"
    scripts_dir.mkdir()
    for script in CompatibilityValidator.REQUIRED_SCRIPTS:
        (scripts_dir / script).write_text("#!/usr/bin/env python3\n", encoding="utf-8")
    engine_dir = scripts_dir / "engine"
    engine_dir.mkdir()
    (engine_dir / "__init__.py").write_text("", encoding="utf-8")

    val = CompatibilityValidator.validate_installation(skill_dir, "antigravity")
    assert val.is_valid is True
    assert len(val.errors) == 0
    assert val.capability_scores["skill_discovery"] is True
    assert val.capability_scores["full_lifecycle"] is True


def test_03_validate_claude_code_installation_target(tmp_path: Path):
    """Validate Claude Code destination layout."""
    dest = InstallationAdapter.get_destination(tmp_path, "claude-code")
    assert dest == tmp_path / ".claude" / "skills" / "repocraft"
    safe, err = InstallationAdapter.validate_destination_safety(dest, tmp_path)
    assert safe is True
    assert err is None


def test_04_avoid_claiming_unverified_claude_invocation():
    """Verify Claude Code is classified strictly as INSTALLATION_ONLY, not SUPPORTED."""
    claude = AgentRegistry.get("claude-code")
    assert claude is not None
    assert claude.support_level == AgentSupportLevel.INSTALLATION_ONLY
    assert claude.support_level != AgentSupportLevel.SUPPORTED
    matrix = CapabilityMatrix.build_matrix()
    claude_matrix = matrix["agents"]["claude-code"]["capabilities"]
    assert claude_matrix["installation"] is True
    assert claude_matrix["headless_certified"] is False
    assert claude_matrix["full_lifecycle"] is False


def test_05_validate_generic_fallback(tmp_path: Path):
    """Validate generic standalone fallback destination."""
    dest = InstallationAdapter.get_destination(tmp_path, "project")
    assert dest == tmp_path / ".repocraft" / "skill"
    gen_agent = AgentRegistry.get("project")
    assert gen_agent is not None
    assert gen_agent.support_level == AgentSupportLevel.MANUAL_CONFIGURATION_REQUIRED


def test_06_handle_unknown_agents(tmp_path: Path):
    """Clean handling of unknown agent or directory with no markers."""
    res = AgentDetector.detect(tmp_path)
    assert res.detected_agent is None
    assert res.confidence == 0.0
    assert len(res.indicator_paths) == 0
    unknown_def = AgentRegistry.get("non-existent-agent-id")
    assert unknown_def is None


def test_07_detect_missing_skill_metadata(tmp_path: Path):
    """Detect malformed or missing YAML frontmatter in SKILL.md for Antigravity."""
    skill_dir = tmp_path / ".agent" / "skills" / "repocraft"
    skill_dir.mkdir(parents=True)
    # Missing frontmatter
    (skill_dir / "SKILL.md").write_text("# RepoCraft without frontmatter\n", encoding="utf-8")
    ref_dir = skill_dir / "references"
    ref_dir.mkdir()
    for pol in CompatibilityValidator.REQUIRED_POLICIES:
        (ref_dir / pol).write_text("# Policy\n", encoding="utf-8")
    scripts_dir = skill_dir / "scripts"
    scripts_dir.mkdir()
    for s in CompatibilityValidator.REQUIRED_SCRIPTS:
        (scripts_dir / s).write_text("# Script\n", encoding="utf-8")
    (scripts_dir / "engine").mkdir()
    (scripts_dir / "engine" / "__init__.py").write_text("", encoding="utf-8")

    val = CompatibilityValidator.validate_installation(skill_dir, "antigravity")
    assert val.is_valid is False
    assert any("frontmatter" in err.lower() for err in val.errors)


def test_08_detect_missing_references(tmp_path: Path):
    """Detect missing policy reference files in skill directory."""
    skill_dir = tmp_path / ".agent" / "skills" / "repocraft"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text("---\nname: repocraft\n---\n", encoding="utf-8")
    ref_dir = skill_dir / "references"
    ref_dir.mkdir()
    # Intentionally leave out policies
    scripts_dir = skill_dir / "scripts"
    scripts_dir.mkdir()
    for s in CompatibilityValidator.REQUIRED_SCRIPTS:
        (scripts_dir / s).write_text("# Script\n", encoding="utf-8")
    (scripts_dir / "engine").mkdir()
    (scripts_dir / "engine" / "__init__.py").write_text("", encoding="utf-8")

    val = CompatibilityValidator.validate_installation(skill_dir, "antigravity")
    assert val.is_valid is False
    assert any("missing required policy reference" in err.lower() for err in val.errors)


def test_09_detect_missing_scripts(tmp_path: Path):
    """Detect missing runtime CLI scripts."""
    skill_dir = tmp_path / ".agent" / "skills" / "repocraft"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text("---\nname: repocraft\n---\n", encoding="utf-8")
    ref_dir = skill_dir / "references"
    ref_dir.mkdir()
    for pol in CompatibilityValidator.REQUIRED_POLICIES:
        (ref_dir / pol).write_text("# Policy\n", encoding="utf-8")
    scripts_dir = skill_dir / "scripts"
    scripts_dir.mkdir()
    # Missing required scripts

    val = CompatibilityValidator.validate_installation(skill_dir, "antigravity")
    assert val.is_valid is False
    assert any("missing required runtime script" in err.lower() for err in val.errors)


def test_10_generate_compatibility_matrix(tmp_path: Path):
    """Verify CapabilityMatrix and CompatibilityReportGenerator produce valid artifacts."""
    reports = tmp_path / "reports"
    out = CompatibilityReportGenerator.generate(tmp_path, reports)
    assert out["json"].is_file()
    assert out["md"].is_file()

    data = json.loads(out["json"].read_text(encoding="utf-8"))
    assert data["schema_version"] == "1.0.0"
    assert "antigravity" in data["capability_matrix"]["agents"]
    assert "claude-code" in data["capability_matrix"]["agents"]
    table = CapabilityMatrix.to_markdown_table()
    assert "Google Antigravity" in table
    assert "SUPPORTED" in table


def test_11_detect_cursor_workspace(tmp_path: Path):
    """Detect Cursor IDE workspace marker .cursor/ and .cursorrules."""
    (tmp_path / ".cursor").mkdir()
    res = AgentDetector.detect(tmp_path)
    assert res.detected_agent == "cursor"
    assert res.confidence == 0.75


def test_12_detect_gemini_workspace(tmp_path: Path):
    """Detect Gemini CLI marker .gemini/."""
    (tmp_path / ".gemini").mkdir()
    res = AgentDetector.detect(tmp_path)
    assert res.detected_agent == "gemini-cli"
    assert res.confidence == 0.6


def test_12b_detect_via_environment_variable(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Detect agent environment via environment variables."""
    monkeypatch.setenv("ANTIGRAVITY_WORKSPACE", "1")
    res = AgentDetector.detect(tmp_path)
    assert "ANTIGRAVITY_WORKSPACE" in res.environment_variables


def test_12c_invocation_adapter_prompts():
    """Verify InvocationAdapter generates appropriate prompt text for all agents."""
    p_anti = InvocationAdapter.get_invocation_prompt("antigravity")
    assert "Run RepoCraft on this repository" in p_anti
    p_claude = InvocationAdapter.get_invocation_prompt("claude-code")
    assert ".claude/skills/repocraft/SKILL.md" in p_claude
    p_cursor = InvocationAdapter.get_invocation_prompt("cursor")
    assert ".cursor/rules/repocraft.mdc" in p_cursor


def test_12d_invocation_adapter_cli_commands():
    """Verify InvocationAdapter generates standard CLI command strings."""
    cmd_intel = InvocationAdapter.get_cli_command("intel", target_dir="/repo", reports_dir="/reports")
    assert "repocraft_intel.py" in cmd_intel
    assert "--target /repo" in cmd_intel
    cmd_status = InvocationAdapter.get_cli_command("status", target_dir="/repo")
    assert "repocraft_status.py" in cmd_status


def test_12e_removal_guidance_message(tmp_path: Path):
    """Verify safe removal guidance string output."""
    dest = tmp_path / ".agent" / "skills" / "repocraft"
    msg = InstallationAdapter.get_removal_guidance(dest)
    assert "rm -rf" in msg
    assert "Remove-Item" in msg
    assert str(dest) in msg


def test_12f_inspect_existing_installation(tmp_path: Path):
    """Verify inspection of existing installed skill directory."""
    dest = tmp_path / ".agent" / "skills" / "repocraft"
    # Non-existent
    info_none = InstallationAdapter.inspect_existing_installation(dest)
    assert info_none["installed"] is False

    # Existing with manifest
    dest.mkdir(parents=True)
    (dest / "INSTALL-MANIFEST.json").write_text(
        json.dumps({"name": "RepoCraft", "version": "1.0.0-rc1", "agent": "antigravity"}),
        encoding="utf-8",
    )
    info_exist = InstallationAdapter.inspect_existing_installation(dest)
    assert info_exist["installed"] is True
    assert info_exist["version"] == "1.0.0-rc1"
    assert info_exist["agent"] == "antigravity"

