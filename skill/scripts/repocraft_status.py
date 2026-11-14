#!/usr/bin/env python3
"""RepoCraft Status and Diagnostic CLI.

Read-only inspection of RepoCraft environment, installed skill integrity,
detected agent compatibility, available phases, and package verification.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Reconfigure standard streams to UTF-8 with replacement for Windows / non-UTF-8 consoles
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
if hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


def safe_print(*args, sep: str = " ", end: str = "\n", file=None, flush: bool = False, **kwargs) -> None:
    """Print text safely across platforms without raising UnicodeEncodeError."""
    target_file = file or sys.stdout
    text = sep.join(str(a) for a in args) + end
    try:
        target_file.write(text)
    except UnicodeEncodeError:
        enc = getattr(target_file, "encoding", None) or "ascii"
        safe_text = text.encode(enc, errors="backslashreplace").decode(enc, errors="replace")
        target_file.write(safe_text)
    if flush:
        target_file.flush()

# Add skill/scripts to sys.path so engine packages import cleanly
SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from engine.compatibility import (
    AgentDetector,
    AgentRegistry,
    AgentSupportLevel,
    CompatibilityValidator,
)
from engine.integration import (
    LifecycleOrchestrator,
    PhaseRegistry,
)
from engine.release import (
    IntegrityVerifier,
    ManifestGenerator,
)


VERSION = "1.0.0-rc1"


def inspect_status(
    target_root: Path,
    reports_dir: Optional[Path] = None,
    verify_installation: bool = False,
    package_path: Optional[Path] = None,
) -> Dict[str, Any]:
    """Perform read-only diagnostic inspection of target repository and RepoCraft state."""
    target_resolved = target_root.resolve()

    # 1. Version & environment info
    python_ver = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    python_supported = sys.version_info >= (3, 9)

    # 2. Agent detection
    agent_detection = AgentDetector.detect(target_resolved)
    detected_agent_id = agent_detection.detected_agent

    agent_def = AgentRegistry.get(detected_agent_id) if detected_agent_id else None
    agent_support_level = agent_def.support_level.value if agent_def else AgentSupportLevel.NOT_TESTED.value

    # 3. Available phases & entry points
    phases = PhaseRegistry.list_all()
    phase_summary = [
        {
            "phase_id": p.phase_id,
            "name": p.display_name,
            "entry_point": p.cli_entry_point,
            "modes": p.supported_modes,
        }
        for p in phases
    ]

    # 4. Installation verification (if requested or if detected)
    installation_status: Dict[str, Any] = {"checked": False}
    if verify_installation or detected_agent_id:
        skill_dir = (
            target_resolved / agent_def.skill_dir
            if agent_def
            else target_resolved / ".agent" / "skills" / "repocraft"
        )
        val_result = CompatibilityValidator.validate_installation(
            skill_dir, detected_agent_id or "antigravity"
        )
        installation_status = {
            "checked": True,
            "skill_dir": str(skill_dir),
            "is_valid": val_result.is_valid,
            "errors": val_result.errors,
            "warnings": val_result.warnings,
            "evidence": val_result.evidence,
        }

    # 5. Package verification (if requested)
    package_status: Dict[str, Any] = {"checked": False}
    if package_path:
        pkg_res = IntegrityVerifier.verify_archive(package_path.resolve())
        package_status = {
            "checked": True,
            "package_path": str(package_path),
            "is_valid": pkg_res.is_valid,
            "errors": pkg_res.errors,
            "warnings": pkg_res.warnings,
            "extractable": pkg_res.extractable,
            "path_traversal_safe": not pkg_res.path_traversal_detected,
        }

    # 6. Artifact & lifecycle check if reports_dir exists
    lifecycle_status: Dict[str, Any] = {"checked": False}
    if reports_dir and reports_dir.is_dir():
        lifecycle_res = LifecycleOrchestrator.evaluate_lifecycle(target_resolved, reports_dir.resolve())
        lifecycle_status = {
            "checked": True,
            "is_valid": lifecycle_res.is_valid,
            "executed_phases": lifecycle_res.executed_phases,
            "missing_phases": lifecycle_res.missing_phases,
            "approval_boundaries_preserved": lifecycle_res.approval_boundaries_preserved,
            "errors": lifecycle_res.errors,
            "warnings": lifecycle_res.warnings,
        }

    # 7. Determine overall diagnostic status
    overall_status = "READY"
    if not python_supported:
        overall_status = "INCOMPLETE"
    elif verify_installation and not installation_status.get("is_valid", False):
        overall_status = "INVALID_INSTALLATION"
    elif package_path and not package_status.get("is_valid", False):
        overall_status = "INCOMPLETE"
    elif detected_agent_id and agent_support_level == AgentSupportLevel.NOT_SUPPORTED.value:
        overall_status = "UNSUPPORTED_AGENT"
    elif detected_agent_id and agent_support_level in (
        AgentSupportLevel.INSTALLATION_ONLY.value,
        AgentSupportLevel.MANUAL_CONFIGURATION_REQUIRED.value,
    ):
        overall_status = "READY_WITH_LIMITATIONS"
    elif not detected_agent_id:
        overall_status = "READY_WITH_LIMITATIONS"

    return {
        "schema_version": "1.0.0",
        "repocraft_version": VERSION,
        "overall_status": overall_status,
        "python_environment": {
            "version": python_ver,
            "supported": python_supported,
            "executable": sys.executable,
        },
        "target_repository": str(target_resolved),
        "detected_agent": agent_detection.to_dict(),
        "agent_support_level": agent_support_level,
        "available_phases": phase_summary,
        "installation_verification": installation_status,
        "package_verification": package_status,
        "lifecycle_verification": lifecycle_status,
        "known_limitations": [
            "Full multi-phase autonomous execution is certified only on Google Antigravity.",
            "Requires Python >=3.9 in the execution environment.",
            "Remote push requires non-conflicting fast-forward state on target remote.",
        ],
    }


def format_text_output(status_data: Dict[str, Any]) -> str:
    """Format status report for console display."""
    enc = getattr(sys.stdout, "encoding", None) or "utf-8"

    def _can(s: str) -> bool:
        try:
            s.encode(enc)
            return True
        except Exception:
            return False

    can_unicode = _can("🟢") and _can("❌")
    status = status_data["overall_status"]
    if can_unicode:
        status_icon = "🟢" if status == "READY" else ("🟡" if "LIMITATIONS" in status else "🔴")
        icon_err = "❌"
        icon_warn = "⚠️"
        icon_info = "ℹ️"
        icon_bullet = "•"
    else:
        status_icon = "[READY]" if status == "READY" else ("[LIMITATIONS]" if "LIMITATIONS" in status else "[NOT_READY]")
        icon_err = "[FAIL]"
        icon_warn = "[WARN]"
        icon_info = "[INFO]"
        icon_bullet = "*"

    lines = [
        "==================================================================",
        f"  RepoCraft Status & Diagnostic Report — {status_icon} {status}",
        "==================================================================",
        f"RepoCraft Version:   {status_data['repocraft_version']}",
        f"Target Repository:   {status_data['target_repository']}",
        f"Python Runtime:      {status_data['python_environment']['version']} (Supported: {status_data['python_environment']['supported']})",
        "",
        "--- Coding Agent Diagnostics ---",
    ]

    det = status_data["detected_agent"]
    agent_name = det.get("detected_agent") or "None detected"
    confidence = int(det.get("confidence", 0) * 100)
    lines.append(f"Detected Agent:      {agent_name} ({confidence}% confidence)")
    lines.append(f"Support Level:       {status_data['agent_support_level']}")
    if det.get("indicator_paths"):
        lines.append(f"Indicators:          {', '.join(det['indicator_paths'])}")

    if status_data["installation_verification"].get("checked"):
        lines.append("")
        lines.append("--- Installation Verification ---")
        inst = status_data["installation_verification"]
        valid_str = "VALID" if inst.get("is_valid") else "INVALID"
        lines.append(f"Skill Directory:     {inst.get('skill_dir')}")
        lines.append(f"Integrity Status:    {valid_str}")
        if inst.get("errors"):
            for err in inst["errors"]:
                lines.append(f"  {icon_err} {err}")
        if inst.get("warnings"):
            for w in inst["warnings"]:
                lines.append(f"  {icon_warn} {w}")

    if status_data["package_verification"].get("checked"):
        lines.append("")
        lines.append("--- Package Verification ---")
        pkg = status_data["package_verification"]
        valid_str = "VALID" if pkg.get("is_valid") else "CORRUPT / INVALID"
        lines.append(f"Archive:             {pkg.get('package_path')}")
        lines.append(f"Integrity:           {valid_str}")
        lines.append(f"Extractable:         {pkg.get('extractable')}")
        lines.append(f"Path Traversal Safe: {pkg.get('path_traversal_safe')}")
        if pkg.get("errors"):
            for err in pkg["errors"]:
                lines.append(f"  {icon_err} {err}")

    lines.extend([
        "",
        "--- Registered Lifecycle Phases ---",
    ])
    for p in status_data["available_phases"]:
        lines.append(f"  {icon_bullet} {p['name']} ({p['entry_point']})")

    lines.extend([
        "",
        "--- Known Limitations ---",
    ])
    for lim in status_data["known_limitations"]:
        lines.append(f"  {icon_info} {lim}")

    lines.append("==================================================================")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="RepoCraft diagnostic and environment inspector.")
    parser.add_argument("--target", type=Path, default=Path.cwd(),
                        help="Target repository root (default: current directory).")
    parser.add_argument("--reports", type=Path, default=None,
                        help="Reports directory for lifecycle inspection.")
    parser.add_argument("--json", action="store_true",
                        help="Emit machine-readable JSON status.")
    parser.add_argument("--verify-installation", action="store_true",
                        help="Verify integrity of installed skill files.")
    parser.add_argument("--verify-package", type=Path, default=None,
                        help="Path to a release ZIP package to verify.")
    args = parser.parse_args()

    status_data = inspect_status(
        target_root=args.target,
        reports_dir=args.reports,
        verify_installation=args.verify_installation,
        package_path=args.verify_package,
    )

    if args.json:
        safe_print(json.dumps(status_data, indent=2))
    else:
        safe_print(format_text_output(status_data))

    overall = status_data["overall_status"]
    if overall in ("READY", "READY_WITH_LIMITATIONS"):
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

