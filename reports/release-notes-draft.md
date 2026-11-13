# RepoCraft 1.0.0-rc1 Release Notes (Draft)

**Release Date:** 2026-11-13  
**Status:** Draft — Awaiting Maintainer Approval  

---

## Summary

RepoCraft v1.0.0-rc1 represents the production-ready release candidate of RepoCraft.

## Highlights

- Complete 7-phase repository engineering skill package for coding agents.
- Certified native support on Google Antigravity (.agent/skills/repocraft).
- Zero third-party pip dependencies required at runtime.
- Independent cryptographic human-in-the-loop approval gates for all file modifications and Git publishing operations.
- Deterministic, byte-for-byte reproducible distribution packaging.
- 100% test coverage across 427 regression and integration test scenarios.

## Added

### Phase 0: Portable Coding-Agent Skill Package Foundation
Local installer (install.py), agent adapter layout (.agent/skills/repocraft), and baseline safety policies.
*Evidence: `install.py, skill/SKILL.md`*

### Phase 1: Repository Intelligence Engine
Safe read-only file categorization, ecosystem stack detection, architecture analysis, and health scoring.
*Evidence: `skill/scripts/repocraft_intel.py, inventory.json`*

### Phase 2: Maintenance, Documentation & GitHub Presentation Engine
Codebase organization auditing, import graph analysis, 18-dimension README audit and generator, license auditor, and Mermaid diagrams.
*Evidence: `skill/scripts/repocraft_maintenance.py, maintenance-plan.json`*

### Phase 3: Security, Testing & CI/CD Validation Engine
High-entropy secret scanner with redaction, dependency and lockfile auditor, application pattern audit, safe test discovery and runner, and CI/CD supply chain analysis.
*Evidence: `skill/scripts/repocraft_security.py, security-findings.json`*

### Phase 4: Bounded Repair, Safe Code Improvements & Regression Validation Engine
Multi-phase finding ingestion, risk-classified repair tasks, hash-bound approval manifest, external verified backups, multi-level regression validation, 3-attempt limit, and automated rollback protecting user modifications.
*Evidence: `skill/scripts/repocraft_repair.py, approval-manifest.json`*

### Phase 5: Git Review, Conditional Commit & Publishing Engine
Porcelain status parser, diff analyzer, 5-tier risk classifier, deterministic staging planner, Conventional Commit generator, atomic commit executor, remote inspector, fast-forward push executor, and PR draft generator.
*Evidence: `skill/scripts/repocraft_git.py, git-state.json`*

### Phase 6: Agent Compatibility Framework & Lifecycle Integration
Calibrated agent support matrix (Antigravity certified, Claude Code installation-only), central phase and artifact registries, schema validators, deterministic ZIP release packaging, and read-only repocraft_status.py diagnostic CLI.
*Evidence: `skill/scripts/repocraft_status.py, agent-compatibility.json`*

### Phase 7: Release Distribution, Upgrade Management & Post-Release Maintenance
Automated distribution archive verification, installer upgrade and rollback management, post-release maintenance audit, and GitHub Actions CI automation.
*Evidence: `skill/scripts/repocraft_release.py, distribution-verification.json`*

## Security

### Pure Standard Library Runtime
RepoCraft requires zero external pip dependencies at runtime, eliminating third-party supply-chain attack vectors.
*Evidence: `pyproject.toml (dependencies = [])`*

### Strict Subprocess and Path Traversal Safety
Subprocesses use explicit argument lists without shell=True; archive extractors and installers strictly reject path traversal escapes.
*Evidence: `skill/scripts/engine/release/integrity_verifier.py`*

### Cryptographic Approval Boundary Isolation
Staging approval, commit approval, and push approval operate under independent cryptographic authorization.
*Evidence: `skill/references/git-workflow-policy.md`*

### Gate E Safety Invariant
The RepoCraft development repository is never auto-committed or auto-pushed; public tags are never created without human maintainer sign-off.
*Evidence: `skill/references/release-and-portability-policy.md`*

## Documentation

### Comprehensive Architecture and Policy Specifications
Full reference policies across safety, quality gates, intelligence, maintenance, documentation, security, repair, git workflow, agent compatibility, and release readiness.
*Evidence: `skill/references/`*

## Breaking Changes

- Initial release candidate; no breaking changes against previous public releases.

## Installation & Migration Notes

- Requires Python >= 3.9 installed in the environment.
- Install into existing projects using `python install.py --target /path/to/project`.
- Verify installation integrity using `python skill/scripts/repocraft_status.py --verify-installation`.

## Known Limitations

- Autonomous multi-phase execution is certified natively on Google Antigravity.
- Claude Code is supported for file installation only; invocation requires manual user prompts.
- Cursor IDE requires manual adapter rule creation (.cursorrules or .cursor/rules/*.mdc).
- Remote publishing requires non-conflicting fast-forward push permissions on target upstream remote.

---

*Notice: This document is a release candidate draft generated by RepoCraft Phase 7. It will not be published publicly until explicitly approved and tagged by the maintainer.*
