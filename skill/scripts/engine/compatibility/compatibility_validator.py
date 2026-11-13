"""Validator that checks installed skill directory integrity against agent expectations."""
from __future__ import annotations

import re
from pathlib import Path
from typing import List, Optional

from .agent_registry import AgentRegistry
from .compatibility_types import AgentSupportLevel, CompatibilityValidationResult


class CompatibilityValidator:
    """Validates an installed skill directory against an agent's contract."""

    REQUIRED_POLICIES = [
        "safety-and-git-baseline.md",
        "quality-gates.md",
        "repository-intelligence.md",
        "maintenance-policy.md",
        "documentation-policy.md",
        "github-presentation-policy.md",
        "security-testing-policy.md",
        "repair-and-regression-policy.md",
        "git-workflow-policy.md",
    ]

    REQUIRED_SCRIPTS = [
        "repocraft_intel.py",
        "repocraft_maintenance.py",
        "repocraft_security.py",
        "repocraft_repair.py",
        "repocraft_git.py",
    ]

    @classmethod
    def validate_installation(
        cls, skill_dir: Path, agent_id: str = "antigravity"
    ) -> CompatibilityValidationResult:
        """Validate that skill_dir contains a complete, functional skill for agent_id."""
        agent = AgentRegistry.get(agent_id)
        support_level = agent.support_level if agent else AgentSupportLevel.NOT_TESTED
        errors: List[str] = []
        warnings: List[str] = []
        evidence: List[str] = []
        checked_paths: List[str] = []

        if not skill_dir.is_dir():
            return CompatibilityValidationResult(
                agent_id=agent_id,
                support_level=support_level,
                is_valid=False,
                errors=[f"Skill directory does not exist: {skill_dir}"],
                warnings=[],
                evidence=[],
                checked_paths=[str(skill_dir)],
                capability_scores={"installation": False},
            )

        checked_paths.append(str(skill_dir))

        # Check SKILL.md
        skill_md = skill_dir / "SKILL.md"
        if not skill_md.is_file():
            errors.append(f"Missing canonical SKILL.md in {skill_dir}")
        else:
            checked_paths.append(str(skill_md))
            content = skill_md.read_text(encoding="utf-8", errors="replace")
            # Check frontmatter
            if content.startswith("---"):
                frontmatter_match = re.search(r"^---\s*\n(.*?)\n---", content, re.DOTALL)
                if frontmatter_match:
                    frontmatter = frontmatter_match.group(1)
                    if "name: repocraft" in frontmatter:
                        evidence.append("Valid YAML frontmatter with name 'repocraft' found in SKILL.md")
                    else:
                        warnings.append("SKILL.md frontmatter does not define 'name: repocraft'")
                else:
                    warnings.append("SKILL.md starts with '---' but has malformed frontmatter block")
            else:
                if agent_id == "antigravity":
                    errors.append("Antigravity requires YAML frontmatter at start of SKILL.md")
                else:
                    warnings.append("SKILL.md does not contain YAML frontmatter")

        # Check references
        ref_dir = skill_dir / "references"
        if not ref_dir.is_dir():
            errors.append(f"Missing references directory in {skill_dir}")
        else:
            checked_paths.append(str(ref_dir))
            for policy in cls.REQUIRED_POLICIES:
                p_file = ref_dir / policy
                if not p_file.is_file():
                    errors.append(f"Missing required policy reference: references/{policy}")
                elif p_file.stat().st_size == 0:
                    errors.append(f"Empty policy reference file: references/{policy}")
                else:
                    checked_paths.append(str(p_file))

        # Check runtime scripts
        scripts_dir = skill_dir / "scripts"
        if not scripts_dir.is_dir():
            errors.append(f"Missing scripts directory in {skill_dir}")
        else:
            checked_paths.append(str(scripts_dir))
            for script in cls.REQUIRED_SCRIPTS:
                s_file = scripts_dir / script
                if not s_file.is_file():
                    errors.append(f"Missing required runtime script: scripts/{script}")
                else:
                    checked_paths.append(str(s_file))

            # Check engine package
            engine_dir = scripts_dir / "engine"
            if not engine_dir.is_dir():
                errors.append(f"Missing engine package directory: scripts/engine")
            elif not (engine_dir / "__init__.py").is_file():
                errors.append("Missing engine/__init__.py in scripts/engine")

        # Check INSTALL-MANIFEST.json
        manifest_file = skill_dir / "INSTALL-MANIFEST.json"
        if manifest_file.is_file():
            evidence.append(f"Found installation manifest: {manifest_file.name}")
            checked_paths.append(str(manifest_file))
        else:
            warnings.append("INSTALL-MANIFEST.json not present in skill directory")

        is_valid = len(errors) == 0
        if is_valid:
            evidence.append(f"All {len(cls.REQUIRED_POLICIES)} policies and {len(cls.REQUIRED_SCRIPTS)} runtime scripts verified present.")

        capability_scores = {
            "installation": is_valid,
            "skill_discovery": is_valid and (agent_id == "antigravity"),
            "frontmatter_parsing": is_valid and (agent_id == "antigravity"),
            "cli_execution": is_valid,
            "approval_handling": True,
            "full_lifecycle": is_valid and (agent_id == "antigravity"),
        }

        return CompatibilityValidationResult(
            agent_id=agent_id,
            support_level=support_level,
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            evidence=evidence,
            checked_paths=checked_paths,
            capability_scores=capability_scores,
        )

