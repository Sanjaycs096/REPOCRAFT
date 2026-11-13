# RepoCraft Release & Maintenance Process

This document outlines the official, evidence-backed release lifecycle, verification checklist, and maintainer runbook for publishing releases of **RepoCraft**.

---

## 1. Release Principles & Governance

1. **Semantic Versioning (SemVer 2.0.0)**: Releases follow `MAJOR.MINOR.PATCH[-PRERELEASE]`.
   - `MAJOR`: Incompatible API or CLI changes, architecture overhauls.
   - `MINOR`: New features, analyzers, or policies added in a backwards-compatible manner.
   - `PATCH`: Backwards-compatible bug fixes and security remediations.
   - `PRERELEASE`: Release candidates (e.g. `1.0.0-rc1`) undergo rigorous multi-stage gating before GA tagging.
2. **Gate E - Sole Maintainer Authority**:
   - Automated scripts, coding agents, and CI pipelines are **strictly prohibited** from automatically committing, pushing, or tagging the RepoCraft repository itself.
   - Final release promotion and git tagging require explicit, authenticated maintainer action.
3. **Reproducible Deterministic Packaging**:
   - Every distribution archive is built from canonical source files tracked in `MANIFEST.json` and verified with SHA-256 checksums.

---

## 2. Release Lifecycle Stages

The release process comprises eight sequential verification stages:

```text
[1. AUDIT] ──> [2. PACKAGE] ──> [3. VERIFY] ──> [4. TEST INSTALL] ──> [5. DRAFT NOTES] ──> [6. CI GATES] ──> [7. SIGN & TAG] ──> [8. PUBLISH]
```

### Stage 1: Pre-Release Verification & Auditing
Run the release driver to inspect release readiness:
```bash
python skill/scripts/repocraft_release.py inspect-release
python skill/scripts/repocraft_release.py validate-release --json
```
- Validates version synchronization across `pyproject.toml`, `MANIFEST.json`, `install.py`, and CLI scripts.
- Verifies that all required policy documents exist in `skill/references/`.
- Verifies that zero external runtime dependencies exist.

### Stage 2: Packaging & Deterministic Archive Creation
Generate the distribution archive (if updating):
```bash
python skill/scripts/engine/release/packager.py
```
- Validates the resulting `dist/repocraft-<version>.zip`.
- Computes canonical SHA-256 digest and records it in `reports/distribution-verification.json`.

### Stage 3: Distribution Verification
Audit the package archive against integrity, security, and path-traversal invariants:
```bash
python skill/scripts/repocraft_release.py verify-distribution --package dist/repocraft-1.0.0-rc1.zip
```
- Ensures no zip-slip or directory traversal entries exist.
- Confirms zero tracked secrets or credential patterns in the archive.
- Confirms all required runtime engines and policies are bundled.

### Stage 4: Clean Installation & Upgrade Acceptance Testing
Run isolated fixture installation and upgrade tests:
```bash
python skill/scripts/repocraft_release.py test-installation
```
- Verifies clean installation into an empty directory.
- Verifies that user application code is strictly preserved.
- Verifies that `.backup` snapshots are created automatically.

### Stage 5: Release Notes & Announcement Drafting
Generate evidence-backed release notes and announcements:
```bash
python skill/scripts/repocraft_release.py draft-release-notes
```
- Outputs `reports/release-notes-draft.md` summarizing changes across all phases.
- Outputs `reports/release-announcement-draft.md` for community and user communication.

### Stage 6: Multi-Platform CI/CD Verification
Push PR to GitHub to trigger `.github/workflows/ci.yml` and `.github/workflows/release-candidate-verification.yml`:
- Matrix runs across Ubuntu and Windows on Python 3.9, 3.10, 3.11, and 3.12.
- 100% test pass rate required.

### Stage 7: Maintainer Sign-Off & Cryptographic Tagging (Gate E)
Once all automated gates pass and maintainers review the draft artifacts:
```bash
# Maintainer reviews diff and working tree
git status
git diff

# Maintainer creates signed git tag
git tag -s v1.0.0 -m "RepoCraft Release v1.0.0"

# Maintainer pushes commit and tag
git push origin master
git push origin v1.0.0
```

### Stage 8: GitHub Release Publication
1. Navigate to the GitHub Releases page.
2. Create a release targeting `v1.0.0`.
3. Copy the content of `reports/release-notes-draft.md` into the release description.
4. Upload `dist/repocraft-1.0.0.zip` and publish the corresponding SHA-256 checksum.

---

## 3. Post-Release Maintenance & Health Audits

Post-release health checks are executed via the maintenance auditor:
```bash
python skill/scripts/repocraft_release.py generate-maintenance-report --reports reports/
```
The audit generates `reports/maintenance-report.json` evaluating:
- Manifest consistency and file coverage.
- AST-verified zero telemetry invariant.
- Policy completeness and documentation links.
- Schema compatibility for all generated JSON reports.

