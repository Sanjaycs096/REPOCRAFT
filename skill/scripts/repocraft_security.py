#!/usr/bin/env python3
"""RepoCraft Phase 3: Security, Testing & CI/CD Validation CLI.

Inspects target repository for:
- Exposed secrets and sensitive configuration
- Vulnerable and unpinned dependencies
- Dangerous application security patterns
- Configuration and Dockerfile hygiene
- Supply chain and GitHub Actions risks
- Test discovery, readiness, and controlled execution
- CI/CD workflow security and posture assessment
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

from engine.security.security_orchestrator import run_security_pipeline


def main() -> int:
    parser = argparse.ArgumentParser(
        description="RepoCraft Phase 3: Security, Testing & CI/CD Validation Engine"
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
        help="Directory to write reports (default: ../repocraft-reports).",
    )
    parser.add_argument(
        "--mode",
        choices=["audit"],
        default="audit",
        help="Execution mode (default: audit).",
    )
    parser.add_argument(
        "--execute-tests",
        action="store_true",
        help="Explicit authorization to execute discovered test suites (runs approved commands only).",
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

    result = run_security_pipeline(
        target_dir=str(target),
        reports_dir=str(reports_dir),
        allow_execution=args.execute_tests,
        mode=args.mode,
    )

    if args.json:
        # Output JSON summary
        print(json.dumps(result, indent=2))
        return 0

    risk = result["risk_assessment"]
    summary = risk["severity_summary"]

    print("=" * 70)
    print(f"RepoCraft Phase 3 Security & Quality Validation: {target.name}")
    print("=" * 70)
    print(f"Target Directory:        {target}")
    print(f"Reports Directory:       {reports_dir}")
    print(f"Execution Mode:          {args.mode.upper()}")
    print(f"Test Execution Allowed:  {'YES (--execute-tests enabled)' if args.execute_tests else 'NO (analysis-only mode)'}")
    print(f"Assessed Risk Level:     {risk['overall_risk_level']}")
    print("-" * 70)
    print("Findings Breakdown:")
    print(f"  * CRITICAL:            {summary['critical']}")
    print(f"  * HIGH:                {summary['high']}")
    print(f"  * MEDIUM:              {summary['medium']}")
    print(f"  * LOW:                 {summary['low']}")
    print(f"  * INFO:                {summary['info']}")
    print("-" * 70)
    print(f"Secrets Detected:        {result['secrets_count']}")
    print(f"Dependency Manifests:    {result['dependencies_count']} ({risk['total_unpinned_dependencies']} unpinned, {risk['missing_lockfiles_count']} missing lockfiles)")
    print(f"Code Patterns Detected:  {result['patterns_count']}")
    print(f"Config / Docker Issues:  {result['configurations_count']}")
    print(f"Supply Chain Issues:     {result['supply_chain_count']}")
    print(f"Test Suites Evaluated:   {result['test_results_count']}")
    print(f"CI/CD Pipelines Audited: {result['cicd_audits_count']}")
    print("\nGenerated Phase 3 Artifacts:")
    for name, p in result["generated_files"].items():
        print(f"  * {name}: {p}")
    print("=" * 70)
    print(f"DISCLAIMER: {risk['safety_disclaimer']}")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

