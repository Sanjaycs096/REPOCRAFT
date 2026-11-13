"""Installation adapter for agent-specific directory paths and layout checks."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .agent_registry import AgentRegistry
from .compatibility_types import AgentSupportLevel


class InstallationAdapter:
    """Manages agent-specific installation targets, validation, and layout rules."""

    @classmethod
    def get_destination(cls, target_root: Path, agent_id: str) -> Optional[Path]:
        """Compute the destination path for an agent within target_root."""
        agent = AgentRegistry.get(agent_id)
        if not agent:
            return None
        return (target_root / agent.skill_dir).resolve()

    @classmethod
    def validate_destination_safety(
        cls, destination: Path, target_root: Path
    ) -> Tuple[bool, Optional[str]]:
        """Verify destination is strictly within target_root and not unsafe."""
        target_resolved = target_root.resolve()
        dest_resolved = destination.resolve()
        try:
            dest_resolved.relative_to(target_resolved)
        except ValueError:
            return False, f"Destination {dest_resolved} escapes target repository root {target_resolved}"

        # Prevent installing directly to target root or system paths
        if dest_resolved == target_resolved:
            return False, "Destination cannot be the repository root directory itself"
        if dest_resolved == target_resolved / ".git":
            return False, "Destination cannot be inside the .git directory"

        return True, None

    @classmethod
    def inspect_existing_installation(cls, destination: Path) -> Dict[str, Any]:
        """Inspect if RepoCraft is already installed at destination and check its manifest."""
        if not destination.exists():
            return {"installed": False, "version": None, "manifest_present": False, "file_count": 0}

        manifest_file = destination / "INSTALL-MANIFEST.json"
        manifest_data = {}
        if manifest_file.is_file():
            try:
                manifest_data = json.loads(manifest_file.read_text(encoding="utf-8"))
            except Exception:
                manifest_data = {"error": "corrupted_manifest"}

        files = [p for p in destination.rglob("*") if p.is_file()]
        return {
            "installed": True,
            "version": manifest_data.get("version"),
            "agent": manifest_data.get("agent"),
            "manifest_present": manifest_file.is_file(),
            "file_count": len(files),
            "manifest_data": manifest_data,
        }

    @classmethod
    def get_removal_guidance(cls, destination: Path) -> str:
        """Provide safe uninstallation guidance for an installed skill directory."""
        return (
            f"To safely uninstall RepoCraft from this project, remove the skill directory:\n"
            f"  rm -rf \"{destination}\"\n"
            f"Or if using PowerShell:\n"
            f"  Remove-Item -Recurse -Force \"{destination}\"\n"
            f"Note: This removes only RepoCraft's skill instructions and scripts; your project code is untouched."
        )

