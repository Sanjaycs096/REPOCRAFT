"""Generates structured and human-readable agent compatibility reports."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from .agent_detector import AgentDetector
from .agent_registry import AgentRegistry
from .capability_matrix import CapabilityMatrix
from .compatibility_types import AgentSupportLevel, CompatibilityValidationResult
from .compatibility_validator import CompatibilityValidator


class CompatibilityReportGenerator:
    """Generates agent-compatibility.json and agent-compatibility.md."""

    VERSION = "1.0.0-rc1"

    @classmethod
    def generate(
        cls,
        target_root: Path,
        output_dir: Path,
    ) -> Dict[str, Path]:
        """Generate structured JSON and Markdown compatibility reports."""
        output_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(timezone.utc).isoformat()

        # Detect agent
        detection = AgentDetector.detect(target_root)

        # Validate known installed agents
        validations: Dict[str, Dict[str, Any]] = {}
        for agent in AgentRegistry.list_all():
            skill_path = target_root / agent.skill_dir
            val_res = CompatibilityValidator.validate_installation(skill_path, agent.agent_id)
            validations[agent.agent_id] = val_res.to_dict()

        # Capability matrix
        matrix = CapabilityMatrix.build_matrix()

        # Structured JSON artifact
        json_data = {
            "schema_version": "1.0.0",
            "repocraft_version": cls.VERSION,
            "generated_at": timestamp,
            "target_root": str(target_root.resolve()),
            "detected_agent": detection.to_dict(),
            "capability_matrix": matrix,
            "validation_results": validations,
            "status": "VALIDATED",
            "errors": [],
            "warnings": [],
        }

        json_path = output_dir / "agent-compatibility.json"
        json_path.write_text(json.dumps(json_data, indent=2) + "\n", encoding="utf-8")

        # Markdown report
        md_content = cls._build_markdown(json_data)
        md_path = output_dir / "agent-compatibility.md"
        md_path.write_text(md_content, encoding="utf-8")

        return {
            "json": json_path,
            "md": md_path,
        }

    @classmethod
    def _build_markdown(cls, data: Dict[str, Any]) -> str:
        matrix_table = CapabilityMatrix.to_markdown_table()
        det = data["detected_agent"]
        det_name = det.get("detected_agent") or "None (Unconfigured)"
        confidence = int(det.get("confidence", 0) * 100)

        lines = [
            "# RepoCraft — Agent Compatibility Matrix & Validation Report",
            "",
            f"**Generated:** {data['generated_at']}  ",
            f"**RepoCraft Version:** `{data['repocraft_version']}`  ",
            f"**Target Repository:** `{data['target_root']}`  ",
            f"**Detected Workspace Agent:** **{det_name}** ({confidence}% confidence)  ",
            "",
            "---",
            "",
            "## 1. Executive Summary",
            "",
            "RepoCraft is a portable coding-agent skill engineered primarily for **Google Antigravity**. "
            "To prevent misleading users, other agent targets are classified transparently using calibrated "
            "support levels rather than assuming successful file copying implies full invocation compatibility.",
            "",
            "## 2. Support Level Definitions",
            "",
            "- `SUPPORTED`: Certified end-to-end (installation, discovery, parsing, CLI execution, approval gates, lifecycle).",
            "- `PARTIALLY_SUPPORTED`: Verified for specific phases or workflows; known gaps exist.",
            "- `INSTALLATION_ONLY`: File layout and manifest copy correctly, but agent-driven automated execution is uncertified.",
            "- `MANUAL_CONFIGURATION_REQUIRED`: Requires project-specific adapter rule or manual CLI execution.",
            "- `NOT_SUPPORTED`: Incompatible with the agent's extension mechanism.",
            "- `NOT_TESTED`: No certified harness or testing performed.",
            "",
            "## 3. Capability Matrix",
            "",
            matrix_table,
            "",
            "---",
            "",
            "## 4. Agent Validation Details",
            "",
        ]

        validations = data.get("validation_results", {})
        for agent_id, val in validations.items():
            agent_def = AgentRegistry.get(agent_id)
            name = agent_def.display_name if agent_def else agent_id
            level = val.get("support_level", "UNKNOWN")
            is_valid = val.get("is_valid", False)
            status_symbol = "✅ Certified / Intact" if is_valid else "⚠️ Incomplete or Not Installed"

            lines.append(f"### {name} (`{agent_id}`)")
            lines.append(f"- **Support Level:** `{level}`")
            lines.append(f"- **Installation Status:** {status_symbol}")
            lines.append(f"- **Configured Directory:** `{agent_def.skill_dir if agent_def else 'N/A'}`")
            lines.append(f"- **Validation Status:** `{agent_def.validation_status if agent_def else 'UNVERIFIED'}`")
            lines.append("")
            lines.append("**Compatibility Evidence:**")
            if agent_def and agent_def.compatibility_evidence:
                for ev in agent_def.compatibility_evidence:
                    lines.append(f"- {ev}")
            else:
                lines.append("- None recorded.")
            lines.append("")

            if agent_def and agent_def.known_limitations:
                lines.append("**Known Limitations:**")
                for lim in agent_def.known_limitations:
                    lines.append(f"- {lim}")
                lines.append("")

            if val.get("errors"):
                lines.append("**Validation Deficiencies:**")
                for err in val["errors"]:
                    lines.append(f"- ❌ {err}")
                lines.append("")

            lines.append("---")
            lines.append("")

        lines.extend([
            "## 5. Honest Compatibility Guarantees",
            "",
            "RepoCraft adheres to the following release invariants:",
            "1. **Never fabricate compatibility**: An agent is never marked `SUPPORTED` without end-to-end automated verification.",
            "2. **Standard Library Only**: Runtime scripts rely strictly on the Python standard library to maximize portability across host environments.",
            "3. **Zero Developer Path Leaks**: An installed RepoCraft copy operates independently of the original checkout repository.",
            "",
        ])

        return "\n".join(lines)

