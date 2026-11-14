#!/usr/bin/env python3
"""RepoCraft Phase 4: Bounded Repair, Safe Code Improvements & Regression Validation CLI.

Inspects findings from Phase 1, Phase 2, and Phase 3, constructs structured repair plans,
enforces explicit approval and repository change protection, applies verified patches,
validates results against regressions, and manages root-cause attempt limits.
"""
from __future__ import annotations

import argparse
import json
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

from engine.repair.repair_orchestrator import RepairOrchestrator


def main() -> int:
    parser = argparse.ArgumentParser(
        description="RepoCraft Phase 4: Bounded Repair, Safe Code Improvements & Regression Validation Engine"
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
        help="Directory containing Phase 1-3 reports and output for Phase 4 (default: ../repocraft-reports).",
    )
    parser.add_argument(
        "--mode",
        choices=["plan", "draft", "apply-approved"],
        default="plan",
        help="Execution mode: plan (default: analyze and generate plan without modifying files), draft (generate draft patches and approval manifest), apply-approved (apply authorized repairs under safeguards).",
    )
    parser.add_argument(
        "--approval-file",
        type=Path,
        default=None,
        help="Path to approval manifest JSON containing human authorizations.",
    )
    parser.add_argument(
        "--execute-tests",
        action="store_true",
        help="Explicit authorization to execute dynamic regression test suites.",
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

    reports_dir = args.reports.resolve() if args.reports else (target.parent / "repocraft-reports").resolve()
    approval_path = str(args.approval_file.resolve()) if args.approval_file else None

    orchestrator = RepairOrchestrator(
        target_dir=str(target),
        reports_dir=str(reports_dir),
        mode=args.mode,
        approval_file=approval_path,
        allow_test_execution=args.execute_tests,
    )

    result = orchestrator.run()

    if args.json:
        print(json.dumps(result, indent=2))
        return 0

    print("=" * 72)
    print(f"RepoCraft Phase 4 Bounded Repair & Regression: {target.name}")
    print("=" * 72)
    print(f"Target Directory:        {target}")
    print(f"Reports Directory:       {reports_dir}")
    print(f"Execution Mode:          {args.mode.upper()}")
    print(f"Test Execution Allowed:  {'YES (--execute-tests)' if args.execute_tests else 'NO (analysis-only)'}")
    print("-" * 72)
    print(f"Total Findings Ingested: {result['total_findings']}")
    print(f"Total Tasks Planned:     {result['total_tasks']}")
    print(f"Repairs Applied:         {result['applied_repairs_count']}")
    print(f"Repairs Blocked/Skipped: {result['blocked_repairs_count']}")

    print("\nGenerated Phase 4 Artifacts:")
    for name, p in result["generated_files"].items():
        print(f"  * {name}: {p}")

    print("=" * 72)
    if args.mode in ("plan", "draft"):
        print(f"Mode is '{args.mode}'. Target repository files were left 100% untouched.")
    else:
        print("Repair execution completed. All modifications verified and backed up.")
    print("=" * 72)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

