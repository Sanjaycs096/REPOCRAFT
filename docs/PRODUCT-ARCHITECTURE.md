# RepoCraft Product Architecture

## Product boundary

RepoCraft is a GitHub-hosted skill package. It is installed into an existing target repository and invoked by a supported coding agent. It is not a standalone repository dashboard or a replacement application.

## Repository contents

- `skill/SKILL.md`: canonical orchestrator instructions.
- `skill/references/`: safety, quality-gate, intelligence, maintenance, security, repair, and git policies.
  - `safety-and-git-baseline.md`: worktree safety and user change protection.
  - `quality-gates.md`: status vocabulary and check guidelines.
  - `repository-intelligence.md`: Phase 1 operational procedures and artifact specifications.
  - `maintenance-policy.md`: Phase 2 codebase organization and unused file rules.
  - `documentation-policy.md`: Phase 2 README standards and strict licensing safeguards.
  - `github-presentation-policy.md`: Phase 2 branding standards and remote metadata boundaries.
  - `security-testing-policy.md`: Phase 3 secret redaction, safe test execution, and CI/CD policies.
  - `repair-and-regression-policy.md`: Phase 4 bounded repair, change protection, and rollback policies.
  - `git-workflow-policy.md`: Phase 5 Git review, conditional staging, atomic commit, and verified publishing policies.
- `skill/scripts/`: repository intelligence, maintenance, security, repair, and Git runtime engines (Python standard library only).
  - `repocraft_intel.py`: Phase 1 CLI driver.
  - `repocraft_maintenance.py`: Phase 2 CLI driver (`--mode {audit,draft,apply}`).
  - `repocraft_security.py`: Phase 3 CLI driver (`--mode audit`, `--execute-tests`).
  - `repocraft_repair.py`: Phase 4 CLI driver (`--mode {plan,draft,apply-approved}`).
  - `repocraft_git.py`: Phase 5 CLI driver (`inspect`, `review`, `plan-stage`, `stage-approved`, `draft-commit`, `commit-approved`, `inspect-remote`, `plan-push`, `push-approved`, `draft-pr`).
  - `engine/`: modular analyzer package.
    - ...Phase 1 intelligence modules (`discovery`, `file_inventory`, `architecture`, `git_analyzer`, `governance`, `testing_ci`, `health_assessor`, `report_generator`, `orchestrator`).
    - `maintenance/`: Phase 2 maintenance modules (`organization_analyzer`, `reference_analyzer`, `unused_file_detector`, `readme_analyzer`, `readme_generator`, `documentation_auditor`, `license_auditor`, `media_auditor`, `github_presentation`, `maintenance_planner`, `maintenance_orchestrator`).
    - `security/`: Phase 3 security, testing & CI/CD modules (`secret_scanner`, `dependency_auditor`, `security_pattern_analyzer`, `configuration_auditor`, `supply_chain_analyzer`, `test_discovery`, `test_readiness`, `test_runner`, `test_result_analyzer`, `cicd_analyzer`, `security_risk_assessor`, `security_report_generator`, `security_orchestrator`).
    - `repair/`: Phase 4 bounded repair modules (`finding_ingestor`, `repair_classifier`, `risk_assessor`, `patch_generator`, `repair_planner`, `approval_manager`, `change_guard`, `backup_manager`, `repair_executor`, `repair_validator`, `regression_runner`, `attempt_controller`, `rollback_manager`, `repair_report_generator`, `repair_orchestrator`).
- `install.py`: local installer for the skill package.
- `adapters/`: agent-specific installation and invocation guidance.
- `docs/`: product, workflow, and compatibility documentation.
- `tests/`: installer, contract, intelligence, and comprehensive maintenance tests.

## Installation boundary

The installer copies the entire `skill/` directory into a selected skill destination. It does not run the installed skill and does not modify application source files.

Initial destinations:
- Antigravity: `.agent/skills/repocraft/`
- Claude Code: `.claude/skills/repocraft/`
- Generic project-local fallback: `.repocraft/skill/`

## Engine Architecture

### Phase 1: Repository Intelligence Engine
Produces 4 baseline artifacts (`inventory.json`, `repository-overview.md`, `repository-audit.md`, `recommendations.json`) by auditing Git baselines, file categories, ecosystem manifests, architectural dimensions, and quality checks.

### Phase 2: Maintenance, Documentation & GitHub Presentation Engine
Reuses Phase 1 intelligence evidence and performs in-depth maintenance analysis across five modules:

```text
skill/scripts/
├── repocraft_intel.py          # Phase 1 CLI
├── repocraft_maintenance.py    # Phase 2 CLI (--mode audit|draft|apply)
└── engine/
    ├── ... (Phase 1 modules)
    └── maintenance/
        ├── __init__.py
        ├── reference_analyzer.py       # Import & cross-reference graph extractor
        ├── unused_file_detector.py     # Calibrated unused file detection (NEVER deletes)
        ├── organization_analyzer.py    # Hierarchy, duplicate files & naming consistency
        ├── readme_analyzer.py          # 18-dimension README audit
        ├── readme_generator.py         # Evidence-backed tailored README draft generator
        ├── documentation_auditor.py    # Broken link & missing image detector, governance
        ├── license_auditor.py          # License type, copyright & manifest reconciliation
        ├── media_auditor.py            # Media bloat, screenshots & diagram capture specs
        ├── github_presentation.py      # Branding score, topics, Mermaid diagram, remote boundaries
        ├── maintenance_planner.py      # Unified, prioritized maintenance task synthesis
        └── maintenance_orchestrator.py # Multi-mode execution pipeline & artifact generator
```

### Phase 2 Artifact Contracts
The maintenance engine writes 6 artifacts to the reports directory (default: `../repocraft-reports/`):
1. `maintenance-analysis.json`: Organization findings, file health, duplicate files, and calibrated unused-file candidates.
2. `README-improved.md`: Evidence-grounded proposed README draft tailored to project type.
3. `documentation-audit.md`: Documentation inventory, link/image integrity, governance status, and command consistency.
4. `github-presentation-audit.md`: Branding assessment, recommended topics/description, Mermaid diagrams, and remote actions blocked confirmation.
5. `maintenance-plan.json`: Prioritized, actionable maintenance tasks with risk ratings and approval flags.
6. `phase2-report.md`: Executive summary of findings, proposed/applied changes, and safety limitations.

### Phase 3: Security, Testing & CI/CD Validation Engine
Reuses Phase 1 discovery and Phase 2 maintenance evidence to conduct in-depth security scans, test suite evaluation, and CI/CD validation:

```text
skill/scripts/
├── repocraft_security.py       # Phase 3 CLI (--mode audit, --execute-tests)
└── engine/
    └── security/
        ├── __init__.py
        ├── types.py                     # Enums, dataclasses, confidence & severity models
        ├── secret_scanner.py            # High-entropy & regex secret scanner with redaction
        ├── dependency_auditor.py        # Multi-ecosystem manifest & unpinned auditor
        ├── security_pattern_analyzer.py # SQLi, command injection, eval, deserialization
        ├── configuration_auditor.py     # .gitignore, .dockerignore, Dockerfile hygiene
        ├── supply_chain_analyzer.py     # Unpinned actions, write-all, script injection
        ├── test_discovery.py            # Test framework, runner, and file discovery
        ├── test_readiness.py            # Missing dependencies & execution readiness
        ├── test_runner.py               # Safe, controlled subprocess runner (whitelisted)
        ├── test_result_analyzer.py      # Output parsing (passed/failed/skipped/errors)
        ├── cicd_analyzer.py             # Multi-CI pipeline audit (GitHub, GitLab, CircleCI)
        ├── security_risk_assessor.py    # Risk synthesis without false safety claims
        ├── security_report_generator.py # 7 Phase 3 artifacts generation
        └── security_orchestrator.py     # End-to-end security pipeline coordinator
```

### Phase 3 Artifact Contracts
The security engine generates 7 dedicated artifacts in the reports directory (default: `../repocraft-reports/`):
1. `security-findings.json`: All discovered secrets, code patterns, configuration issues, and supply chain risks.
2. `dependency-audit.json`: Manifests, pinned/unpinned dependencies, lockfile presence, and offline status.
3. `test-analysis.json`: Discovered test frameworks, test files, empty test files, and readiness blockers.
4. `test-execution-report.json`: Execution status (`PASSED`, `FAILED`, `NOT_RUN`, `BLOCKED_BY_POLICY`, `TIMED_OUT`), exit codes, durations, and redacted outputs.
5. `cicd-audit.json`: Workflow triggers, jobs, step coverage, action pinning, and permissions.
6. `security-quality-report.md`: Detailed human-readable markdown report with findings tables and actionable remediations.
7. `phase3-report.md`: Executive scorecard, boundary classifications, and human verification requirements.

### Phase 4: Bounded Repair, Safe Code Improvements & Regression Validation Engine
Consumes Phase 1, Phase 2, and Phase 3 findings to construct prioritized, risk-classified repair plans, enforce explicit approval, protect user modifications, apply bounded patches, validate regressions, and track 3-attempt limits:

```text
skill/scripts/
├── repocraft_repair.py         # Phase 4 CLI (--mode {plan, draft, apply-approved})
└── engine/
    └── repair/
        ├── __init__.py
        ├── repair_types.py             # Enums, dataclasses, lifecycle states
        ├── finding_ingestor.py         # Multi-phase artifact ingestor & deduplicator
        ├── repair_classifier.py        # Category & risk classification
        ├── risk_assessor.py            # Authorization boundary & autonomous policy
        ├── patch_generator.py          # Deterministic patch constructor & hasher
        ├── repair_planner.py           # Structured repair task prioritization
        ├── approval_manager.py         # Approval manifest & patch hash verification
        ├── change_guard.py             # Git working tree & user change safeguard
        ├── backup_manager.py           # External verified pre-repair backup manager
        ├── repair_executor.py          # Safe patch applicator with hash tracking
        ├── repair_validator.py         # Level 1 (integrity) & Level 2 (syntax) validator
        ├── regression_runner.py        # Level 3/4 test runner & baseline comparator
        ├── attempt_controller.py       # Bounded 3-attempt limit & persistent history
        ├── rollback_manager.py         # Safe rollback protecting subsequent user work
        ├── repair_report_generator.py  # 7 Phase 4 artifacts generation
        └── repair_orchestrator.py      # End-to-end Phase 4 coordinator
```

### Phase 4 Artifact Contracts
The repair engine generates 7 dedicated artifacts in the reports directory (default: `../repocraft-reports/`):
1. `repair-findings.json`: All normalized findings ingested from Phase 1, 2, and 3.
2. `repair-plan.json`: Full repair plan with tasks, priorities, risk ratings, and proposed patches.
3. `approval-manifest.json`: Per-task approval status and expected patch hashes.
4. `repair-execution.json`: Execution results, modified files, and applied patches.
5. `regression-comparison.json`: Baseline vs post-repair validation comparisons.
6. `rollback-report.json`: Rollback actions, restored files, and protected user modifications.
7. `phase4-report.md`: Comprehensive executive report, scorecards, and remaining manual recommendations.

### Phase 5: Git Review, Conditional Commit & Publishing Engine
Executes reviewable, approved Git operations across an explicit state machine:
`INSPECT → REVIEW → PLAN → APPROVE_STAGE → STAGE → VERIFY_STAGE → APPROVE_COMMIT → COMMIT → VERIFY_COMMIT → APPROVE_PUSH → PUSH → VERIFY_REMOTE`

```text
skill/scripts/
├── repocraft_git.py            # Phase 5 CLI driver
└── engine/
    └── git/
        ├── __init__.py
        ├── git_types.py                # Contracts, enums, status models, hashes
        ├── git_environment.py          # State inspection, URL sanitization, detached HEAD
        ├── git_status_analyzer.py      # Porcelain -z parser for staged/unstaged/untracked/renames
        ├── diff_analyzer.py            # Bounded hunk extractor, mode/binary checks
        ├── change_risk_analyzer.py     # 5-tier risk classifier, secret redaction, test weakening
        ├── change_review.py            # Markdown & JSON change review generator
        ├── staging_planner.py          # Deterministic staging planner (no git add .)
        ├── staging_approval.py         # Staging manifest validator & hash checks
        ├── staging_executor.py         # Per-file staging executor & post-stage verification
        ├── commit_message_generator.py # Conventional Commit proposal generator
        ├── commit_approval.py          # Commit authorization manifest validator
        ├── commit_executor.py          # Atomic commit executor with receipt verification
        ├── remote_inspector.py         # Remote tracker, divergence checker, push planner
        ├── push_approval.py            # Publishing authorization validator (no force push)
        ├── push_executor.py            # Fast-forward push executor & remote verification
        ├── pull_request_planner.py     # Evidence-backed PR description draft generator
        ├── git_report_generator.py     # Compiles 15 Phase 5 artifacts into workflow report
        └── git_orchestrator.py         # Master coordinator for Phase 5 pipeline
```

### Phase 5 Artifact Contracts
The Git engine generates 15 dedicated artifacts in the reports directory (default: `.repocraft/reports/`):
1. `git-state.json`: Repository environment, branch, HEAD, remotes, operations in progress.
2. `git-change-review.md`: Human-readable Markdown change and risk review.
3. `git-change-review.json`: Structured file-level change classifications and risk metrics.
4. `staging-plan.json`: Exact proposed staging scope and diff hashes.
5. `staging-approval.json`: Human-editable staging authorization manifest.
6. `staging-result.json`: Staging verification record and post-stage diff hash.
7. `commit-proposal.md`: Proposed Conventional Commit message with rationale.
8. `commit-approval.json`: Exact commit authorization manifest.
9. `commit-receipt.json`: Post-commit verification receipt with commit hash and parent.
10. `remote-status.json`: Sanitized remote configuration and tracking status.
11. `push-plan.json`: Proposed publishing destination, base checks, and divergence state.
12. `push-approval.json`: Explicit publishing authorization manifest.
13. `push-result.json`: Remote publishing verification record.
14. `pull-request-draft.md`: Pull request description based on evidence and test logs.
15. `git-workflow-report.md`: End-to-end Git workflow and audit summary.

### Phase 6: Agent Compatibility, Lifecycle Integration, Release Packaging & Production Readiness
Integrates all completed phases into a unified, installable, deterministic distribution candidate with verified agent compatibility, full lifecycle handoff validation, and rigorous release gate assessment:

```text
skill/scripts/
├── repocraft_status.py         # Phase 6 diagnostic and environment inspector CLI
└── engine/
    ├── compatibility/          # Agent Compatibility Framework
    │   ├── __init__.py
    │   ├── compatibility_types.py    # Enums, AgentDefinition, support levels
    │   ├── agent_registry.py          # Central registry of supported/candidate agents
    │   ├── agent_detector.py          # Project & environment agent marker detector
    │   ├── installation_adapter.py    # Target path calculations & safe layout validation
    │   ├── invocation_adapter.py      # Agent prompt templates & CLI guidance
    │   ├── capability_matrix.py       # Cross-agent capability evaluation
    │   ├── compatibility_validator.py # Installed skill integrity validator
    │   └── compatibility_report.py    # Agent compatibility JSON and Markdown generator
    ├── integration/            # Full Lifecycle Integration Engine
    │   ├── __init__.py
    │   ├── integration_types.py       # PhaseContract, ArtifactContract, HandoffResult
    │   ├── phase_registry.py          # Central registry of 7 lifecycle phase contracts
    │   ├── artifact_registry.py       # Central registry of 39 artifact contracts
    │   ├── schema_validator.py        # JSON schema validation and field verification
    │   ├── dependency_graph.py        # Topological DAG and prerequisite evaluator
    │   ├── integration_validator.py   # Phase-to-phase handoff & approval boundary isolation
    │   ├── lifecycle_orchestrator.py  # Master read-only lifecycle orchestrator
    │   └── integration_report.py      # Lifecycle report and registry exporter
    ├── release/                # Release Packaging & Readiness Engine
    │   ├── __init__.py
    │   ├── release_types.py           # ReleaseGate, PackageManifest, PackageValidation
    │   ├── manifest_generator.py      # Runtime file inventory and SHA-256 calculator
    │   ├── package_builder.py         # Deterministic ZIP distribution builder
    │   ├── integrity_verifier.py      # Path traversal safety, extraction & secret audit
    │   ├── reproducibility_checker.py # Dual-build byte-for-byte reproducibility validator
    │   ├── release_validator.py       # 9 completion gates (Gates A through I) evaluator
    │   ├── audit_runner.py            # Codebase architecture & supply-chain security auditor
    │   ├── release_report.py          # Release manifest, package integrity & checklist generator
    │   └── release_orchestrator.py    # End-to-end Phase 6 evaluation coordinator
    └── distribution/           # Phase 7 Distribution & Maintenance Engine
        ├── __init__.py
        ├── distribution_types.py      # ReleaseNoteEntry, DistributionVerificationResult, UpgradePlan
        ├── release_notes_generator.py # Evidence-backed release notes generator across phases
        ├── announcement_generator.py  # Public release announcement draft generator
        ├── distribution_verifier.py   # ZIP archive verification, SHA-256, traversal safety & secrets
        ├── installation_tester.py     # Clean installation and user file preservation tester
        ├── upgrade_manager.py         # In-place upgrade planning, backups, execution & rollback
        ├── maintenance_auditor.py     # Post-release manifest, policy, CLI & zero-telemetry auditor
        └── distribution_orchestrator.py # End-to-end Phase 7 artifact coordinator
```

### Phase 6 Artifact Contracts
Phase 6 produces 15 dedicated artifacts outside target repositories:
1. `phase6-architecture-audit.json`: Structural findings, import integrity, and consistency.
2. `phase6-architecture-audit.md`: Human-readable architecture audit report.
3. `agent-compatibility.json`: Structured compatibility matrix across known agents.
4. `agent-compatibility.md`: Human-readable agent compatibility guide.
5. `phase-registry.json`: Machine-readable registry of all phase contracts.
6. `artifact-registry.json`: Machine-readable registry of all artifact contracts.
7. `lifecycle-integration-report.json`: Structured cross-phase integration results.
8. `lifecycle-integration-report.md`: Executive lifecycle integration summary.
9. `release-manifest.json`: Complete file inventory and SHA-256 digests.
10. `package-integrity.json`: Archive integrity, extraction safety, and security checks.
11. `release-readiness.json`: Assessment of Gates A through I and release candidate status.
12. `release-checklist.md`: Human maintainer sign-off checklist.
13. `phase6-security-audit.json`: Standard-library verification and subprocess audit.
14. `phase6-security-audit.md`: Security posture and supply-chain guarantees.
15. `phase6-report.md`: Comprehensive Phase 6 executive report.

### Phase 7 Artifact Contracts
Phase 7 produces 8 dedicated artifacts outside target repositories:
1. `release-validation.json`: Version alignment, gate evaluation, and release candidate validation.
2. `release-notes-draft.md`: Structured, evidence-backed changelog and phase summaries for maintainer review.
3. `release-announcement-draft.md`: Formatted release announcement for user adoption.
4. `distribution-verification.json`: Archive integrity, cryptographic hashes, entry count, and traversal safety.
5. `installation-acceptance.json`: Clean installation test results and user file preservation verification.
6. `upgrade-validation.json`: Upgrade simulation, backup creation verification, and rollback validation.
7. `maintenance-report.json`: Post-release health audit, manifest consistency, and AST-verified zero telemetry.
8. `phase7-report.md`: Comprehensive Phase 7 distribution and maintenance executive report.

## Development phases

0. Product foundation, package structure, skill contract, installer. *(Complete)*
1. Repository intelligence engine. *(Complete)*
2. Maintenance, documentation, and GitHub presentation engine. *(Complete)*
3. Security, testing, and CI/CD. *(Complete)*
4. Bounded repair and regression. *(Complete)*
5. Git review and conditional publishing. *(Complete)*
6. Agent compatibility, integration testing, release. *(Complete)*
7. Release publication, distribution, adoption & post-release maintenance. *(Complete)*
