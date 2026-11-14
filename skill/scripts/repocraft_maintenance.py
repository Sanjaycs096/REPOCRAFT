#!/usr/bin/env python3
"""RepoCraft Phase 2: Maintenance, Documentation & GitHub Presentation CLI.

Audits codebase organization, analyzes and generates evidence-backed READMEs,
reviews governance and licensing, evaluates GitHub presentation, and produces
prioritized maintenance plans.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Add scripts directory to sys.path
SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

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

from engine.maintenance.maintenance_orchestrator import MaintenanceOrchestrator


def main() -> int:
    parser = argparse.ArgumentParser(
        description="RepoCraft Phase 2: Maintenance, Documentation & GitHub Presentation Engine"
    )
    parser.add_argument(
        "--target",
        type=Path,
        default=Path.cwd(),
        help="Target project directory (default: current directory).",
    )
    parser.add_argument(
        "--reports",
        type=Path,
        default=None,
        help="Directory to read/write reports (default: ../repocraft-reports).",
    )
    parser.add_argument(
        "--mode",
        choices=["audit", "draft", "apply"],
        default="audit",
        help="Execution mode: audit (default: read-only analysis), draft (generate draft improvements), apply (apply approved changes).",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output JSON summary to stdout.",
    )
    args = parser.parse_args()

    target = args.target.resolve()
    if not target.is_dir():
        print(f"ERROR: target directory does not exist: {target}", file=sys.stderr)
        return 2

    orchestrator = MaintenanceOrchestrator(
        target_dir=target,
        reports_dir=args.reports,
        mode=args.mode,
    )
    summary, artifacts = orchestrator.run()

    # Terminal summary output
    print("=" * 68)
    print(f"RepoCraft Phase 2 Maintenance & Presentation: {target.name}")
    print("=" * 68)
    print(f"Target Directory:        {target}")
    print(f"Execution Mode:          {args.mode.upper()}")
    print(f"Reports Directory:       {summary['reports_dir']}")
    print(f"Codebase Org Findings:   {summary['total_organization_findings']}")
    print(f"Unused File Candidates:  {summary['unused_file_candidates']}")
    print(f"README Quality Score:    {summary['readme_score']}/100")
    print(f"Branding Score:          {summary['branding_score']}/100")
    print(f"Broken Doc Links/Images: {summary['broken_doc_links']} link(s), {summary['missing_doc_images']} image(s)")
    print(f"License Present:         {'Yes' if summary['has_license'] else 'No (Action Required)'}")
    print(f"Total Maintenance Tasks: {summary['total_maintenance_tasks']}")
    print(f"Changes Applied:         {summary['applied_changes_count']} file(s)")

    print("\nGenerated Phase 2 Artifacts:")
    for name, p in artifacts.items():
        print(f"  * {name}: {p}")

    print("=" * 68)
    if args.mode in ("audit", "draft"):
        print("Inspection complete. No target project files were altered.")
    else:
        print("Maintenance execution complete. All changes applied under safety policies.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

