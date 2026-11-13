#!/usr/bin/env python3
"""RepoCraft Repository Intelligence CLI.

Safe, read-only inspection engine for repositories. Discovers architecture,
technologies, testing setups, governance, and Git baselines, producing
structured evidence-backed reports.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Add script directory to sys.path to allow running standalone or as module
SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from engine.orchestrator import IntelligenceEngine
from engine.types import Severity


def main() -> int:
    parser = argparse.ArgumentParser(
        description="RepoCraft Phase 1: Repository Intelligence Engine"
    )
    parser.add_argument(
        "--target",
        type=Path,
        default=Path.cwd(),
        help="Target project directory (default: current directory).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Directory to write reports (default: ../repocraft-reports).",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output brief JSON summary to stdout.",
    )
    args = parser.parse_args()

    target = args.target.resolve()
    if not target.is_dir():
        print(f"ERROR: target directory does not exist: {target}", file=sys.stderr)
        return 2

    engine = IntelligenceEngine(target_dir=target, output_dir=args.output)
    report, output_files = engine.run()

    # Terminal summary output
    print("=" * 64)
    print(f"RepoCraft Repository Intelligence Report: {report.project_name}")
    print("=" * 64)
    print(f"Target Directory: {report.repo_root}")
    print(f"Project Type(s):  {', '.join(report.detected_types)}")
    print(f"Languages:        {', '.join(report.languages) if report.languages else 'None detected'}")
    print(f"Frameworks:       {', '.join(report.frameworks) if report.frameworks else 'None detected'}")
    print(f"Package Managers: {', '.join(report.package_managers) if report.package_managers else 'None'}")
    print(f"Total Files:      {report.file_inventory_summary.get('total_files', 0)}")

    git_info = "Git Repository" if report.git_baseline.is_git_repository else "Non-Git Directory"
    if report.git_baseline.is_git_repository:
        git_info += f" ({report.git_baseline.current_branch})"
        if report.git_baseline.pre_existing_modifications_count > 0:
            git_info += f" — {report.git_baseline.pre_existing_modifications_count} pre-existing user modification(s)"
    print(f"Git Baseline:     {git_info}")

    # Findings summary
    sev_counts = {sev: 0 for sev in Severity}
    for f in report.findings:
        sev_counts[f.severity] += 1

    print("\nHealth & Risk Findings:")
    print(f"  CRITICAL: {sev_counts[Severity.CRITICAL]}")
    print(f"  HIGH:     {sev_counts[Severity.HIGH]}")
    print(f"  MEDIUM:   {sev_counts[Severity.MEDIUM]}")
    print(f"  LOW:      {sev_counts[Severity.LOW]}")
    print(f"  INFO:     {sev_counts[Severity.INFO]}")

    if report.safe_warnings:
        print("\nSafety Notices:")
        for w in report.safe_warnings:
            print(f"  * {w}")

    print("\nGenerated Artifacts:")
    for name, p in output_files.items():
        print(f"  * {name}: {p}")
    print("=" * 64)
    print("Static inspection complete. No target project files were altered.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

