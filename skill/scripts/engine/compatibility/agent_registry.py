"""Central registry of known coding agents and their compatibility contracts."""
from __future__ import annotations

from typing import Dict, List, Optional

from .compatibility_types import AgentDefinition, AgentId, AgentSupportLevel


_REGISTRY: Dict[str, AgentDefinition] = {
    AgentId.ANTIGRAVITY.value: AgentDefinition(
        agent_id=AgentId.ANTIGRAVITY.value,
        display_name="Google Antigravity",
        support_level=AgentSupportLevel.SUPPORTED,
        skill_dir=".agent/skills/repocraft",
        installation_method="local_installer",
        expected_format="yaml_frontmatter_markdown",
        invocation_instructions=(
            "Antigravity automatically discovers skills located in .agent/skills/*/SKILL.md. "
            "Invoke with: 'Run RepoCraft on this repository. Inspect the complete project, establish its Git "
            "and quality baseline, identify improvements, then safely maintain the codebase...'"
        ),
        required_metadata=["name: repocraft", "description:"],
        supported_capabilities=[
            "installation",
            "skill_discovery",
            "frontmatter_parsing",
            "subprocess_execution",
            "human_approval_gates",
            "full_lifecycle_automation",
        ],
        known_limitations=[
            "Requires Python >=3.9 installed in the environment for executing runtime scripts.",
        ],
        validation_status="CERTIFIED",
        compatibility_evidence=[
            "Standard .agent/skills/ directory layout verified by installer contract tests.",
            "YAML frontmatter in skill/SKILL.md conforms to Antigravity skill specification.",
            "Full lifecycle execution verified across Phase 0-5 test suites.",
        ],
    ),
    AgentId.CLAUDE_CODE.value: AgentDefinition(
        agent_id=AgentId.CLAUDE_CODE.value,
        display_name="Claude Code (Anthropic)",
        support_level=AgentSupportLevel.INSTALLATION_ONLY,
        skill_dir=".claude/skills/repocraft",
        installation_method="local_installer",
        expected_format="markdown_instructions",
        invocation_instructions=(
            "Skill files are installed to .claude/skills/repocraft. Prompt Claude Code to read "
            ".claude/skills/repocraft/SKILL.md and execute the required scripts via terminal commands."
        ),
        required_metadata=["name: repocraft"],
        supported_capabilities=[
            "installation",
        ],
        known_limitations=[
            "Claude Code automated skill discovery and headless invocation protocol are unverified.",
            "Requires manual user prompting and terminal execution verification.",
            "Autonomous multi-phase pipeline is not certified for headless invocation.",
        ],
        validation_status="INSTALLATION_VERIFIED_INVOCATION_UNVERIFIED",
        compatibility_evidence=[
            "install.py provides configured target for .claude/skills/repocraft.",
            "File placement and file integrity verified by installer tests.",
            "Invocation protocol not tested in certified headless test harness.",
        ],
    ),
    AgentId.CURSOR.value: AgentDefinition(
        agent_id=AgentId.CURSOR.value,
        display_name="Cursor IDE",
        support_level=AgentSupportLevel.MANUAL_CONFIGURATION_REQUIRED,
        skill_dir=".cursor/rules/repocraft.mdc",
        installation_method="manual_adapter",
        expected_format="mdc_or_cursorrules",
        invocation_instructions=(
            "Copy or reference .repocraft/skill/SKILL.md in .cursorrules or a rule file in .cursor/rules/. "
            "Execute RepoCraft CLI scripts through the Cursor terminal."
        ),
        required_metadata=[],
        supported_capabilities=[
            "terminal_execution",
        ],
        known_limitations=[
            "Cursor uses .cursorrules or .cursor/rules/*.mdc conventions rather than .agent/skills directory tree.",
            "Requires manual adapter file creation.",
        ],
        validation_status="NOT_CERTIFIED",
        compatibility_evidence=[
            "CLI scripts can be executed manually in Cursor built-in terminal.",
        ],
    ),
    AgentId.GEMINI_CLI.value: AgentDefinition(
        agent_id=AgentId.GEMINI_CLI.value,
        display_name="Gemini CLI",
        support_level=AgentSupportLevel.NOT_TESTED,
        skill_dir=".gemini/skills/repocraft",
        installation_method="unsupported",
        expected_format="unknown",
        invocation_instructions="Not tested or certified.",
        required_metadata=[],
        supported_capabilities=[],
        known_limitations=[
            "No official skill discovery convention or test harness available.",
        ],
        validation_status="UNTESTED",
        compatibility_evidence=[],
    ),
    AgentId.GENERIC.value: AgentDefinition(
        agent_id=AgentId.GENERIC.value,
        display_name="Project-Local Standalone (Generic)",
        support_level=AgentSupportLevel.MANUAL_CONFIGURATION_REQUIRED,
        skill_dir=".repocraft/skill",
        installation_method="local_installer",
        expected_format="markdown_instructions",
        invocation_instructions=(
            "Read .repocraft/skill/SKILL.md and run scripts via Python CLI: "
            "`python .repocraft/skill/scripts/repocraft_intel.py --target .`"
        ),
        required_metadata=[],
        supported_capabilities=[
            "installation",
            "script_execution",
        ],
        known_limitations=[
            "Does not integrate with agent-specific skill discovery protocols; requires manual invocation.",
        ],
        validation_status="VERIFIED_STANDALONE",
        compatibility_evidence=[
            "install.py provides configured target for .repocraft/skill.",
            "Installer integrity verified by contract tests.",
        ],
    ),
}


class AgentRegistry:
    """Query interface for registered agents."""

    @classmethod
    def get(cls, agent_id: str) -> Optional[AgentDefinition]:
        return _REGISTRY.get(agent_id.lower().strip())

    @classmethod
    def list_all(cls) -> List[AgentDefinition]:
        return list(_REGISTRY.values())

    @classmethod
    def list_supported(cls) -> List[AgentDefinition]:
        return [
            agent for agent in _REGISTRY.values()
            if agent.support_level == AgentSupportLevel.SUPPORTED
        ]

    @classmethod
    def is_known(cls, agent_id: str) -> bool:
        return agent_id.lower().strip() in _REGISTRY

