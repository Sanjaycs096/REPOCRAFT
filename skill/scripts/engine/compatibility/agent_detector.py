"""Detector for agent environments and installed skill markers."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from .compatibility_types import AgentDetectionResult, AgentId


class AgentDetector:
    """Inspects a target project or environment to detect coding agent configurations."""

    @classmethod
    def detect(cls, target_root: Path) -> AgentDetectionResult:
        """Detect agent environment markers within target_root."""
        root = target_root.resolve()
        indicators = []
        env_vars = []

        # Check environment variables
        if os.environ.get("ANTIGRAVITY_WORKSPACE") or os.environ.get("GEMINI_CLI"):
            env_vars.append("ANTIGRAVITY_WORKSPACE")
        if os.environ.get("CLAUDE_CODE_ENTRY"):
            env_vars.append("CLAUDE_CODE_ENTRY")
        if os.environ.get("CURSOR_PROJECT_DIR"):
            env_vars.append("CURSOR_PROJECT_DIR")

        # Check directory markers
        antigravity_marker = root / ".agent"
        claude_marker = root / ".claude"
        cursor_marker = root / ".cursor"
        cursorrules_marker = root / ".cursorrules"
        gemini_marker = root / ".gemini"
        repocraft_marker = root / ".repocraft"

        # Check Antigravity first (primary target)
        if (antigravity_marker / "skills" / "repocraft").is_dir():
            indicators.append(".agent/skills/repocraft")
            return AgentDetectionResult(
                detected_agent=AgentId.ANTIGRAVITY.value,
                confidence=1.0,
                indicator_paths=indicators,
                environment_variables=env_vars,
                notes="Found installed RepoCraft skill under .agent/skills/repocraft.",
            )
        elif antigravity_marker.is_dir():
            indicators.append(".agent/")
            return AgentDetectionResult(
                detected_agent=AgentId.ANTIGRAVITY.value,
                confidence=0.85,
                indicator_paths=indicators,
                environment_variables=env_vars,
                notes="Found .agent/ workspace configuration.",
            )

        # Check Claude Code
        if (claude_marker / "skills" / "repocraft").is_dir():
            indicators.append(".claude/skills/repocraft")
            return AgentDetectionResult(
                detected_agent=AgentId.CLAUDE_CODE.value,
                confidence=0.9,
                indicator_paths=indicators,
                environment_variables=env_vars,
                notes="Found installed RepoCraft skill under .claude/skills/repocraft.",
            )
        elif claude_marker.is_dir():
            indicators.append(".claude/")
            return AgentDetectionResult(
                detected_agent=AgentId.CLAUDE_CODE.value,
                confidence=0.7,
                indicator_paths=indicators,
                environment_variables=env_vars,
                notes="Found .claude/ workspace configuration.",
            )

        # Check Cursor
        if cursor_marker.is_dir() or cursorrules_marker.is_file():
            if cursor_marker.is_dir():
                indicators.append(".cursor/")
            if cursorrules_marker.is_file():
                indicators.append(".cursorrules")
            return AgentDetectionResult(
                detected_agent=AgentId.CURSOR.value,
                confidence=0.75,
                indicator_paths=indicators,
                environment_variables=env_vars,
                notes="Found Cursor workspace configuration.",
            )

        # Check Gemini CLI
        if gemini_marker.is_dir():
            indicators.append(".gemini/")
            return AgentDetectionResult(
                detected_agent=AgentId.GEMINI_CLI.value,
                confidence=0.6,
                indicator_paths=indicators,
                environment_variables=env_vars,
                notes="Found .gemini/ directory.",
            )

        # Check Generic Repocraft installation
        if (repocraft_marker / "skill").is_dir():
            indicators.append(".repocraft/skill")
            return AgentDetectionResult(
                detected_agent=AgentId.GENERIC.value,
                confidence=0.9,
                indicator_paths=indicators,
                environment_variables=env_vars,
                notes="Found generic RepoCraft installation under .repocraft/skill.",
            )

        # No agent detected
        return AgentDetectionResult(
            detected_agent=None,
            confidence=0.0,
            indicator_paths=[],
            environment_variables=env_vars,
            notes="No recognized coding agent directories or markers detected.",
        )

