"""Invocation adapters providing agent-specific instructions and prompt templates."""
from __future__ import annotations

from typing import Dict, Optional

from .agent_registry import AgentRegistry
from .compatibility_types import AgentId


MASTER_INVOCATION_PROMPT = (
    "Run RepoCraft on this repository. Inspect the complete project, establish its Git "
    "and quality baseline, identify improvements, then safely maintain the codebase, "
    "documentation, GitHub presentation, security posture, tests, and CI/CD. Repair "
    "verified issues within policy, rerun relevant checks, review the complete diff, and "
    "publish only if every publishing condition is satisfied. Preserve my existing work. "
    "Produce a terminal summary and a detailed Markdown report."
)


class InvocationAdapter:
    """Generates invocation instructions, prompt templates, and execution guidance."""

    @classmethod
    def get_invocation_prompt(cls, agent_id: str) -> str:
        """Return the recommended prompt to trigger RepoCraft in the target agent."""
        agent = AgentRegistry.get(agent_id)
        if agent and agent.agent_id == AgentId.ANTIGRAVITY.value:
            return MASTER_INVOCATION_PROMPT
        elif agent and agent.agent_id == AgentId.CLAUDE_CODE.value:
            return (
                f"Please read the RepoCraft skill instructions at `{agent.skill_dir}/SKILL.md` "
                f"and execute the RepoCraft analysis pipeline on this repository:\n\n{MASTER_INVOCATION_PROMPT}"
            )
        elif agent and agent.agent_id == AgentId.CURSOR.value:
            return (
                f"Referencing the RepoCraft instructions in `{agent.skill_dir}`, "
                f"execute the RepoCraft analysis:\n\n{MASTER_INVOCATION_PROMPT}"
            )
        else:
            return MASTER_INVOCATION_PROMPT

    @classmethod
    def get_cli_command(cls, phase: str, target_dir: str = ".", reports_dir: str = "../repocraft-reports") -> str:
        """Return the standard CLI command for a given phase."""
        commands: Dict[str, str] = {
            "intel": f"python skill/scripts/repocraft_intel.py --target {target_dir} --output {reports_dir}",
            "maintenance": f"python skill/scripts/repocraft_maintenance.py --target {target_dir} --reports {reports_dir} --mode audit",
            "security": f"python skill/scripts/repocraft_security.py --target {target_dir} --reports {reports_dir} --mode audit",
            "repair": f"python skill/scripts/repocraft_repair.py --target {target_dir} --reports {reports_dir} --mode plan",
            "git": f"python skill/scripts/repocraft_git.py inspect --target {target_dir} --reports {reports_dir}",
            "status": f"python skill/scripts/repocraft_status.py --target {target_dir}",
        }
        return commands.get(phase, f"python skill/scripts/repocraft_{phase}.py --target {target_dir}")

