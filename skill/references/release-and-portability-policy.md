# RepoCraft — Release Packaging, Portability & Production Readiness Policy

## 1. Release Invariants

1. **Gate E Safety Invariant**: The RepoCraft development repository is NEVER automatically committed or pushed by any tool or script. All development changes remain strictly under the maintainer's review.
2. **Deterministic Release Packaging**: Release ZIP archives must be reproducible. Zip entries use normalized forward-slash paths, deterministic alphabetical sorting, and fixed entry timestamps to avoid spurious hash differences.
3. **Strict Inclusion & Exclusion Rules**:
   - **Included**: `README.md`, `LICENSE`, `MANIFEST.json`, `install.py`, `pyproject.toml`, canonical `skill/` (instructions, references, scripts, engines), `adapters/`, `docs/`.
   - **Excluded**: `tests/`, test fixtures, `.git/`, `__pycache__/`, `*.pyc`, temporary directories, user reports, `.pytest_cache/`, `*.backup*`, secrets.
4. **Zero Path Traversal**: Package builders and extractors must strictly reject entries containing leading slashes, drive letters, or `..` directory traversals.
5. **Portability Guarantee**: An installed RepoCraft copy must function completely independently of the source repository checkout, home directories, or platform-specific paths.
6. **Standard Library Only**: Runtime engines must run on Python >= 3.9 standard library with zero external pip dependencies.
7. **Zero Telemetry Guarantee**: No tracking, phone-home, or analytics code allowed. All engine code is AST-audited for prohibited modules (`sentry_sdk`, `mixpanel`, `amplitude`, `segment`, `posthog`, `datadog`).

---

## 2. Mandatory Release Completion Gates

A release candidate may be marked `READY_FOR_RELEASE` only when all 9 gates pass:

- **Gate A — Architecture**: Modular CLI entry points, clean package namespaces, standard schemas, and DAG verified.
- **Gate B — Agent Compatibility**: Antigravity certified; non-Antigravity agents accurately classified without false claims.
- **Gate C — Lifecycle Integration**: All phase handoffs validated without schema breakages or identity mismatches.
- **Gate D — Packaging**: Distribution archive built, extracted safely, checksums verified, and no dev artifacts included.
- **Gate E — Portability**: Local installer verified; existing user files protected from unconfirmed overwrite; backups created on force install.
- **Gate F — Security**: No `shell=True` subprocess invocations; secret redaction verified; zero external runtime attack surfaces.
- **Gate G — Testing**: All Phase 6 integration and Phase 0–5 regression tests pass without weakening assertions.
- **Gate H — Documentation**: README, architecture specifications, skill instructions, and policies synchronized.
- **Gate I — Final Review**: Human maintainer review of working tree and explicit release tag authorization.

---

## 3. Phase 7: Distribution Verification & Upgrade Policies

### 3.1 Distribution Package Verification
- Distribution ZIP packages must pass automated verification via `DistributionVerifier`:
  - Archive existence and readability.
  - SHA-256 digest computation and manifest comparison.
  - Zero directory traversal entries (rejects `..` or absolute paths).
  - Absence of secret or credential patterns in packaged files.
  - Presence of core runtime components (`install.py`, `MANIFEST.json`, `skill/SKILL.md`).

### 3.2 Non-Destructive In-Place Upgrades
- Target repository application code must never be modified or removed during skill upgrade.
- Existing skill installation must be backed up to `.backup` or `.backup-<timestamp>` before replacement.
- An updated `INSTALL-MANIFEST.json` with new file hashes must be written upon completion.

### 3.3 Verified Rollback Policy
- A failed, interrupted, or problematic upgrade must be rollback-capable via `install.py --rollback`.
- Rollback restores the prior `.backup` directory atomically.
- If no backup directory exists, rollback must safely abort with exit code 1 without corrupting existing files.

### 3.4 Post-Release Maintenance Auditing
- Continuous post-release health is verified via `MaintenanceAuditor`:
  - `MANIFEST.json` entry completeness.
  - Mandatory policy file coverage (`agent-compatibility.md`, `git-workflow-policy.md`, `release-and-portability-policy.md`, `repair-and-regression-policy.md`).
  - CLI script syntax and executable validity.
  - Zero telemetry AST inspection across all engine modules.

---

## 4. Versioning & Release Tagging

- Release versions follow Semantic Versioning (`MAJOR.MINOR.PATCH[-RC]`).
- All metadata files (`pyproject.toml`, `MANIFEST.json`, `install.py`, `repocraft_status.py`, `repocraft_release.py`) must carry identical version strings.
- Automated tools must NEVER create or push public Git tags. The maintainer alone performs tagging:
  ```bash
  git tag -a v1.0.0 -m "RepoCraft v1.0.0 GA release"
  ```
