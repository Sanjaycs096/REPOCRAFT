# RepoCraft — Release Package Integrity & Hash Discrepancy Resolution Report

## 1. Executive Summary & Root Cause Investigation

### The Discrepancy
In the previous audit turn, the release ZIP file at `dist/repocraft-1.0.0-rc1.zip` retained its prior SHA-256 checksum:
`44c3775c64a0e396d12d4d457230034fbb497436b9656d5c3a8543421207c145` (126 entries)
despite modifications having been made to `install.py`, `skill/scripts/repocraft_*.py`, `skill/SKILL.md`, and `MANIFEST.json` for Windows `cp1252` encoding resiliency and the creation of `repocraft_selfcheck.py`.

### Root Cause Analysis
1. **Build Timeline**: The previous archive was generated at the conclusion of **Phase 6** (`v1.0.0-rc1` release packaging).
2. **Subsequent Additions**:
   - **Phase 7**: Added `repocraft_release.py`, 14 engine modules in `skill/scripts/engine/distribution/`, `release-and-portability-policy.md`, and documentation.
   - **CI Repair & Self-Verification**: Added `repocraft_selfcheck.py`, and modified `install.py` and CLI drivers for standard stream reconfiguration (`sys.stdout.reconfigure`) and ASCII glyph fallbacks.
3. **Stale Archive**: The archive had not been rebuilt after Phase 7 and CI hardening. It was missing 17 runtime files and contained stale pre-repair script versions.

---

## 2. Rebuilding & Deterministic Reproduction

The distribution package was regenerated using RepoCraft's deterministic `PackageBuilder`:

1. **Rollback Backup Created**:
   The Phase 6 archive and its manifest were safely backed up prior to replacement:
   - `dist/repocraft-1.0.0-rc1.zip.backup-phase6`
   - `reports/release-manifest-phase6.json`
2. **Rebuilt Archive**:
   - Target Archive: `dist/repocraft-1.0.0-rc1.zip`
   - Target Version: `1.0.0-rc1`
   - Manifest Synchronization: `reports/release-manifest.json` updated with full file SHA-256 digests.
3. **Deterministic Reproducibility Verification**:
   An independent second build was executed in a temporary isolated scratch directory (`scratch_repro/`).
   - Build 1 SHA-256: `04884637cb4f6921fcc557e47df70ff920f9aa7c39dfd05fe544d0f05951b1fa`
   - Build 2 SHA-256: `04884637cb4f6921fcc557e47df70ff920f9aa7c39dfd05fe544d0f05951b1fa`
   - **Byte-for-byte Identical**: `True`

---

## 3. Cryptographic and Structural Package Attributes

| Package Attribute | Verified Value |
| --- | --- |
| **Archive File** | `dist/repocraft-1.0.0-rc1.zip` |
| **Release Version** | `1.0.0-rc1` |
| **SHA-256 Digest** | `04884637cb4f6921fcc557e47df70ff920f9aa7c39dfd05fe544d0f05951b1fa` |
| **File Size** | `1,057,246 bytes` (~1.01 MB) |
| **Total Entries** | **143** files |
| **Compression Method** | `DEFLATE` (deterministic normalized timestamps) |
| **Permissions** | `0o755` (scripts/executables), `0o644` (regular files) |
| **Path Traversal Protection** | `True` (0 `../` or root-relative paths detected) |
| **Secret Scan Status** | `True` (0 private keys, tokens, or credentials found) |
| **Development Exclusions** | `True` (`tests/`, `reports/`, `__pycache__/`, `.git/` excluded) |

---

## 4. Source-to-Package File Reconciliation

An automated byte-by-byte audit compared every archive entry directly against its corresponding repository source file:

- **Total Entries in Archive**: `143`
- **Matching Source Files**: `143` (100.0%)
- **Mismatched Content**: `0`
- **Missing in Source**: `0`

### Included File Categories in Rebuilt Package (143 Files)
1. **Scaffold & Metadata (5 files)**:
   - `install.py` (with stream reconfiguration and `safe_print`)
   - `MANIFEST.json` (Phase 6, registered CLI drivers)
   - `README.md`
   - `LICENSE`
   - `pyproject.toml`
2. **Skill Core & Governance (12 files)**:
   - `skill/SKILL.md`
   - 11 Reference policies: `safety-and-git-baseline.md`, `quality-gates.md`, `repository-intelligence.md`, `maintenance-policy.md`, `github-presentation-policy.md`, `documentation-policy.md`, `security-testing-policy.md`, `repair-and-regression-policy.md`, `git-workflow-policy.md`, `agent-compatibility.md`, `release-and-portability-policy.md`.
3. **CLI Drivers (8 files)**:
   - `skill/scripts/repocraft_intel.py`
   - `skill/scripts/repocraft_maintenance.py`
   - `skill/scripts/repocraft_security.py`
   - `skill/scripts/repocraft_repair.py`
   - `skill/scripts/repocraft_git.py`
   - `skill/scripts/repocraft_status.py`
   - `skill/scripts/repocraft_release.py`
   - `skill/scripts/repocraft_selfcheck.py`
4. **Engine Subsystems (111 files)**:
   - Discovery, file inventory, architecture (`skill/scripts/engine/`)
   - Maintenance, docs, branding, license analysis (`skill/scripts/engine/maintenance/`)
   - Security scanning, vulnerability detection, CI/CD auditing (`skill/scripts/engine/security/`)
   - Repair planning, execution, verification, rollback (`skill/scripts/engine/repair/`)
   - Git review, staging, commit, conditional publish (`skill/scripts/engine/git/`)
   - Lifecycle orchestrator, phase registry, artifact contracts (`skill/scripts/engine/integration/`)
   - Release packaging, gate validation, manifest generator (`skill/scripts/engine/release/`)
   - Distribution verifier, installation tester, upgrade manager (`skill/scripts/engine/distribution/`)
5. **Documentation & Adapters (7 files)**:
   - `adapters/README.md`
   - `docs/CONTRIBUTING.md`, `docs/PRODUCT-ARCHITECTURE.md`, `docs/RELEASE-PROCESS.md`, `docs/SECURITY.md`, `docs/UPGRADE-AND-ROLLBACK.md`, `docs/USER-GUIDE.md`.

Full JSON manifest comparison is available at `reports/final-acceptance/source-to-package-comparison.json`.

---

## 5. Automated Verification Results Against Rebuilt Archive

1. **`DistributionVerifier` Engine**:
   - Status: `DistributionCheckStatus.VALID`
   - Errors: `[]`
   - Traversal Safe: `True`
   - Secret Scan: `True`
2. **`repocraft_release.py verify-distribution` CLI**:
   - Exit code: `0`
   - Output: `Distribution Check: VALID`
3. **Distribution Test Suite (`tests/distribution/`)**:
   - 29/29 tests passed (including clean install, force backup, upgrade, and rollback).
4. **Self-Verification Gates**:
   - `GATE_06_DISTRIBUTION_INTEGRITY`: `PASS`
   - `GATE_07_PACKAGE_REPRODUCIBILITY`: `PASS`
