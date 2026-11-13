"""Capability matrix evaluator across supported and candidate agents."""
from __future__ import annotations

from typing import Any, Dict, List

from .agent_registry import AgentRegistry
from .compatibility_types import AgentSupportLevel


CAPABILITIES = [
    ("installation", "Clean installation via install.py"),
    ("skill_discovery", "Automatic agent skill discovery"),
    ("frontmatter_parsing", "YAML frontmatter parsing"),
    ("cli_execution", "Subprocess / CLI script execution"),
    ("approval_handling", "Human-in-the-loop approval gate support"),
    ("full_lifecycle", "Certified full multi-phase lifecycle"),
    ("headless_certified", "Headless automated execution certification"),
]


class CapabilityMatrix:
    """Builds and analyzes cross-agent capability matrices."""

    @classmethod
    def build_matrix(cls) -> Dict[str, Any]:
        """Generate structured capability matrix across all registered agents."""
        agents = AgentRegistry.list_all()
        matrix = {}
        for agent in agents:
            caps = {}
            if agent.support_level == AgentSupportLevel.SUPPORTED:
                # Fully certified (Antigravity)
                caps = {
                    "installation": True,
                    "skill_discovery": True,
                    "frontmatter_parsing": True,
                    "cli_execution": True,
                    "approval_handling": True,
                    "full_lifecycle": True,
                    "headless_certified": True,
                }
            elif agent.support_level == AgentSupportLevel.INSTALLATION_ONLY:
                # Claude Code
                caps = {
                    "installation": True,
                    "skill_discovery": False,  # Not verified headless
                    "frontmatter_parsing": False,
                    "cli_execution": True,  # Via Claude bash tool if prompted
                    "approval_handling": True,
                    "full_lifecycle": False,  # Not certified
                    "headless_certified": False,
                }
            elif agent.support_level == AgentSupportLevel.MANUAL_CONFIGURATION_REQUIRED:
                caps = {
                    "installation": True if agent.agent_id == "project" else False,
                    "skill_discovery": False,
                    "frontmatter_parsing": False,
                    "cli_execution": True,
                    "approval_handling": True,
                    "full_lifecycle": False,
                    "headless_certified": False,
                }
            else:  # NOT_TESTED / NOT_SUPPORTED
                caps = {
                    "installation": False,
                    "skill_discovery": False,
                    "frontmatter_parsing": False,
                    "cli_execution": False,
                    "approval_handling": False,
                    "full_lifecycle": False,
                    "headless_certified": False,
                }

            matrix[agent.agent_id] = {
                "display_name": agent.display_name,
                "support_level": agent.support_level.value,
                "skill_dir": agent.skill_dir,
                "validation_status": agent.validation_status,
                "capabilities": caps,
                "limitations": list(agent.known_limitations),
                "evidence": list(agent.compatibility_evidence),
            }

        return {
            "schema_version": "1.0.0",
            "capabilities_defined": [c[0] for c in CAPABILITIES],
            "capability_descriptions": dict(CAPABILITIES),
            "agents": matrix,
        }

    @classmethod
    def to_markdown_table(cls) -> str:
        """Render markdown table summarizing agent compatibility and capabilities."""
        matrix = cls.build_matrix()["agents"]
        headers = ["Agent", "Support Level", "Install", "Discovery", "CLI Exec", "Full Lifecycle", "Status"]
        rows = []
        for agent_id, data in matrix.items():
            caps = data["capabilities"]
            inst = "✅ Yes" if caps.get("installation") else "❌ No"
            disc = "✅ Yes" if caps.get("skill_discovery") else "❌ No"
            cli = "✅ Yes" if caps.get("cli_execution") else "❌ No"
            life = "✅ Yes" if caps.get("full_lifecycle") else "❌ No"
            rows.append(f"| {data['display_name']} | `{data['support_level']}` | {inst} | {disc} | {cli} | {life} | {data['validation_status']} |")

        table = (
            f"| {' | '.join(headers)} |\n"
            f"| {' | '.join(['---'] * len(headers))} |\n" +
            "\n".join(rows)
        )
        return table

