# RepoCraft Upgrade, Rollback & Uninstallation Guide

This guide explains how to safely upgrade, verify, roll back, or uninstall RepoCraft within a target repository.

---

## 1. Safety Architecture & Principles

RepoCraft's upgrade engine is built on five core safety guarantees:

1. **Non-Destructive Target Codebase**: RepoCraft upgrades only affect the skill directory itself (e.g. `.agent/skills/repocraft/`). It **never** touches, modifies, or deletes the target repository's application code, git history, or configuration files during an upgrade.
2. **Atomic Pre-Upgrade Backups**: Before any files are overwritten or removed, the entire existing installation directory is mirrored to an isolated backup directory (`<destination>.backup` or `<destination>.backup-<timestamp>`).
3. **Cryptographic Manifest Verification**: Every installed file is tracked in an `INSTALL-MANIFEST.json` containing SHA-256 digests. Post-upgrade verification ensures every asset matches the distributed manifest.
4. **Deterministic Rollback**: If an upgrade fails, is interrupted, or exhibits unexpected behavior, the previous installation can be restored with a single command.
5. **Zero External Runtime Dependencies**: Upgrades and rollbacks use standard Python 3.9+ libraries without network downloads, external package managers, or root/administrator privileges.

---

## 2. Checking Current Installation Status

To inspect your currently installed version and verify file integrity:

```bash
# Verify installation integrity via the installer:
python /path/to/RepoCraft/install.py --target . --verify

# Or check diagnostic status via the status CLI:
python .agent/skills/repocraft/scripts/repocraft_status.py --verify-installation
```

The verification command checks:
- The existence of all manifest-registered files.
- SHA-256 checksum matches for every file.
- The installed version in `INSTALL-MANIFEST.json`.

---

## 3. Planning an Upgrade

Before applying an upgrade, you can simulate and inspect the upgrade plan using the release CLI:

```bash
python /path/to/RepoCraft/skill/scripts/repocraft_release.py plan-upgrade \
  --current 1.0.0-rc1 \
  --target-version 1.0.0 \
  --target .
```

The output indicates:
- Current installed version vs. target version.
- Upgrade classification (`patch`, `minor`, `major`).
- Backup directory destination.
- Files to be updated, added, or retired.
- Breaking change notices or migration requirements (if any).

---

## 4. Performing an In-Place Upgrade

To perform an automated upgrade of an installed RepoCraft skill:

```bash
# Upgrade the default Antigravity installation:
python /path/to/RepoCraft/install.py --target . --upgrade

# Upgrade a custom agent installation (e.g., project fallback):
python /path/to/RepoCraft/install.py --target . --agent project --upgrade
```

### What Happens During `--upgrade`:
1. **Safety Check**: Checks if the target installation directory exists and contains `INSTALL-MANIFEST.json`.
2. **Snapshot Creation**: The existing directory is safely copied to `.agent/skills/repocraft.backup`. If `.backup` already exists, a timestamped snapshot (`.backup-YYYYMMDD-HHMMSS`) is created to prevent clobbering prior backups.
3. **File Replacement**: New skill instructions, engines, CLI drivers, and reference policies are copied into place.
4. **Manifest Generation**: A fresh `INSTALL-MANIFEST.json` is generated with updated file paths, SHA-256 digests, and version metadata.
5. **Post-Upgrade Verification**: The installer validates that all new files are intact and readable.

---

## 5. Rollback Workflow

If you encounter issues with a newly upgraded version or need to revert to the previous release:

```bash
# Revert to the latest automatic backup:
python /path/to/RepoCraft/install.py --target . --rollback

# Or for a specific agent installation:
python /path/to/RepoCraft/install.py --target . --agent project --rollback
```

### Rollback Process:
1. **Locates Backup**: Scans for `.agent/skills/repocraft.backup` (or the most recent `.backup-*` directory).
2. **Atomic Swap / Restoration**: Removes the problematic installation directory and restores the backup directory to its original location.
3. **Integrity Confirmation**: Confirms that `INSTALL-MANIFEST.json` from the previous version is restored and readable.
4. **Safety Invariant**: The rollback operation is completely local and does not touch user files or Git staging.

---

## 6. Clean Uninstallation

If you wish to remove RepoCraft completely from your repository:

### Standard Removal:
RepoCraft leaves no hidden daemons, system registry keys, or global hooks. To uninstall:

```bash
# Remove the installed skill directory:
rm -rf .agent/skills/repocraft/

# Remove any pre-upgrade backup directories:
rm -rf .agent/skills/repocraft.backup*

# (Optional) Remove generated inspection reports:
rm -rf repocraft-reports/
```

On Windows PowerShell:
```powershell
Remove-Item -Recurse -Force .agent\skills\repocraft
Remove-Item -Recurse -Force .agent\skills\repocraft.backup*
```

---

## 7. Troubleshooting

| Symptom | Cause | Resolution |
| :--- | :--- | :--- |
| `Cannot rollback: No backup directory found` | No prior upgrade was performed, or backups were deleted. | Reinstall the desired version cleanly using `install.py --target . --force`. |
| `Verification failed: X file(s) corrupted or modified` | Files inside `.agent/skills/repocraft/` were edited manually. | Run `install.py --target . --upgrade` to re-sync files with the canonical package. |
| `PermissionError during upgrade or backup` | Another process (e.g. IDE or anti-virus) has a lock on skill files. | Close open terminals or editors inspecting `.agent/skills/` and rerun with `--upgrade`. |

