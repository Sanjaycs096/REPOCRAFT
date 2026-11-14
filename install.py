#!/usr/bin/env python3
"""Install RepoCraft skill files into an existing project.

Local source installation is supported in Phase 0. Remote bootstrap is intentionally
not enabled until the canonical public repository URL and release integrity process
are finalized.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path

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


AGENT_PATHS = {
    "antigravity": Path(".agent/skills/repocraft"),
    "claude-code": Path(".claude/skills/repocraft"),
    "project": Path(".repocraft/skill"),
}

REQUIRED = [
    Path("SKILL.md"),
    Path("references/safety-and-git-baseline.md"),
    Path("references/quality-gates.md"),
    Path("references/repository-intelligence.md"),
    Path("references/maintenance-policy.md"),
    Path("references/documentation-policy.md"),
    Path("references/github-presentation-policy.md"),
    Path("references/security-testing-policy.md"),
    Path("references/repair-and-regression-policy.md"),
    Path("references/git-workflow-policy.md"),
    Path("references/agent-compatibility.md"),
    Path("references/release-and-portability-policy.md"),
    Path("scripts/repocraft_intel.py"),
    Path("scripts/repocraft_maintenance.py"),
    Path("scripts/repocraft_security.py"),
    Path("scripts/repocraft_repair.py"),
    Path("scripts/repocraft_git.py"),
    Path("scripts/repocraft_status.py"),
    Path("scripts/repocraft_release.py"),
    Path("scripts/repocraft_selfcheck.py"),
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description="Install RepoCraft into an existing project.")
    parser.add_argument("--source", type=Path, default=Path(__file__).resolve().parent,
                        help="Local RepoCraft source directory (default: installer directory).")
    parser.add_argument("--agent", choices=sorted(AGENT_PATHS), default="antigravity")
    parser.add_argument("--target", type=Path, default=Path.cwd(),
                        help="Existing project root (default: current directory).")
    parser.add_argument("--force", action="store_true",
                        help="Replace an existing RepoCraft installation after backing it up.")
    parser.add_argument("--upgrade", action="store_true",
                        help="Upgrade an existing RepoCraft installation after backing it up.")
    parser.add_argument("--verify", action="store_true",
                        help="Verify installed skill files against INSTALL-MANIFEST.json without modifying.")
    parser.add_argument("--rollback", action="store_true",
                        help="Roll back the installation to the most recent backup.")
    args = parser.parse_args()

    source = args.source.resolve()
    target = args.target.resolve()

    if not target.is_dir():
        safe_print(f"ERROR: target project directory does not exist: {target}", file=sys.stderr)
        return 2

    destination = target / AGENT_PATHS[args.agent]

    # Handle verify mode
    if args.verify:
        if not destination.is_dir():
            safe_print(f"ERROR: No installation found at {destination}", file=sys.stderr)
            return 1
        manifest_file = destination / "INSTALL-MANIFEST.json"
        if not manifest_file.is_file():
            safe_print(f"ERROR: Missing INSTALL-MANIFEST.json at {destination}", file=sys.stderr)
            return 1
        try:
            m_data = json.loads(manifest_file.read_text(encoding="utf-8"))
        except Exception as e:
            safe_print(f"ERROR: Corrupted manifest: {e}", file=sys.stderr)
            return 1
        mismatches = []
        for rel_str, exp_hash in m_data.get("files", {}).items():
            f_path = destination / rel_str
            if not f_path.is_file():
                mismatches.append(f"Missing file: {rel_str}")
            elif sha256(f_path) != exp_hash:
                mismatches.append(f"Hash mismatch: {rel_str}")
        if mismatches:
            safe_print("Verification failed:\n  " + "\n  ".join(mismatches), file=sys.stderr)
            return 1
        safe_print(f"Verification PASSED for {destination} ({len(m_data.get('files', {}))} files verified).")
        return 0

    # Handle rollback mode
    if args.rollback:
        parent = destination.parent
        backups = sorted(parent.glob(f"{destination.name}.backup*"), key=lambda p: p.stat().st_mtime, reverse=True)
        if not backups:
            safe_print(f"ERROR: No backup found to rollback at {destination}", file=sys.stderr)
            return 1
        latest_backup = backups[0]
        if destination.exists():
            shutil.rmtree(destination)
        shutil.copytree(latest_backup, destination)
        safe_print(f"Rollback successful: Restored {destination} from {latest_backup}")
        return 0

    # Standard / Force / Upgrade installation
    skill_source = source / "skill"
    if not skill_source.is_dir():
        safe_print(f"ERROR: skill source directory not found: {skill_source}", file=sys.stderr)
        return 2

    missing = [str(item) for item in REQUIRED if not (skill_source / item).is_file()]
    if missing:
        safe_print("ERROR: required skill files are missing: " + ", ".join(missing), file=sys.stderr)
        return 2

    prev_version = None
    if destination.exists():
        if not (args.force or args.upgrade):
            safe_print(f"STOP: destination already exists: {destination}")
            safe_print("Review it first. Re-run with --force or --upgrade only if you intentionally want a backup and replacement.")
            return 3

        # Read previous version if present
        prev_manifest = destination / "INSTALL-MANIFEST.json"
        if prev_manifest.is_file():
            try:
                prev_version = json.loads(prev_manifest.read_text(encoding="utf-8")).get("version")
            except Exception:
                pass

        backup = destination.with_name(destination.name + ".backup")
        suffix = 1
        while backup.exists():
            backup = destination.with_name(destination.name + f".backup-{suffix}")
            suffix += 1
        shutil.copytree(destination, backup)
        safe_print(f"Existing installation backed up to: {backup}")

    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        shutil.rmtree(destination)
    shutil.copytree(skill_source, destination)

    manifest = {
        "name": "RepoCraft",
        "version": "1.0.0-rc1",
        "agent": args.agent,
        "installed_to": str(destination),
        "previous_version": prev_version,
        "is_upgrade": bool(args.upgrade or prev_version),
        "files": {
            str(p.relative_to(destination)).replace("\\", "/"): sha256(p)
            for p in sorted(destination.rglob("*")) if p.is_file()
        },
    }
    (destination / "INSTALL-MANIFEST.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )

    action_label = "upgraded" if (args.upgrade or prev_version) else "installed"
    safe_print(f"RepoCraft skill {action_label}.")
    safe_print(f"Project: {target}")
    safe_print(f"Skill:   {destination}")
    safe_print("No application source files or project dependencies were changed.")
    safe_print("Next: open the project in your coding agent and invoke the RepoCraft skill.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
