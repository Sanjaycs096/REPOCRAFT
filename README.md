# RepoCraft

**A portable repository-maintenance skill for coding agents.**

RepoCraft is a skill repository—not a standalone application. Install its skill files into an existing project, invoke the skill from your coding agent, and let it inspect and improve that repository under explicit safety rules.

## Intended user experience

1. Open an existing project in your coding agent.
2. Run the installation command from that project's root.
3. The installer places RepoCraft in the agent's project-level skills directory.
4. Invoke RepoCraft with the master prompt.
5. RepoCraft audits first, plans changes, applies permitted improvements, verifies them, and reports what happened.

RepoCraft does not create a replacement application or modify a project merely because it was installed.

## Installation, Upgrade & Invocation

### 1. Obtain RepoCraft from GitHub

Clone the repository to your local system:

```bash
git clone https://github.com/Sanjaycs096/REPOCRAFT.git
```

### 2. Install into Your Target Repository

From the root of your target project:

```bash
# Standard installation for Google Antigravity (.agent/skills/repocraft/)
python /path/to/REPOCRAFT/install.py --target .

# Or for generic project fallback (.repocraft/skill/)
python /path/to/REPOCRAFT/install.py --target . --agent project
```

The installer copies only RepoCraft's skill instructions, reference policies, and runtime engines. It **never modifies your project's application source code or dependencies during installation**.

### 3. Verify, Upgrade & Rollback Commands

```bash
# Verify installed skill files against INSTALL-MANIFEST.json (SHA-256 integrity check):
python install.py --target . --verify

# Upgrade an existing installed skill safely (creates automatic .backup before replacing):
python /path/to/REPOCRAFT/install.py --target . --upgrade

# Rollback an upgrade to the previous automatic backup:
python install.py --target . --rollback
```

### 4. Invoke with the Master Prompt

Open your project in **Google Antigravity** (certified primary agent) or your preferred coding agent, and provide the master prompt:

> **Run RepoCraft on this repository. Inspect the complete project, establish its Git and quality baseline, identify improvements, then safely maintain the codebase, documentation, GitHub presentation, security posture, tests, and CI/CD. Repair verified issues within policy, rerun relevant checks, review the complete diff, and publish only if every publishing condition is satisfied. Preserve my existing work. Produce a terminal summary and a detailed Markdown report.**

### 5. Inspect Reports & Approve Consequential Operations

RepoCraft executes safely under the **Independent Cryptographic Approval Invariant**:
- Review generated audit reports in `repocraft-reports/` outside your target source code.
- Review proposed staging, commit, and push plans.
- Consequential operations require human sign-off on deterministic approval manifests:
  - **Gate A (Staging)**: Review and sign `staging-approval.json` before files are staged.
  - **Gate B (Commit)**: Review and sign `commit-approval.json` before commits are created.
  - **Gate C (Push)**: Review and sign `push-approval.json` before pushing to a remote.
  - Approval for staging never grants approval to commit; approval to commit never grants approval to push.

## Initial target

The first adapter target is Antigravity project-level skills:

```text
.agent/
└── skills/
    └── repocraft/
        ├── SKILL.md
        ├── INSTALL-MANIFEST.json
        ├── references/
        │   ├── safety-and-git-baseline.md
        │   ├── quality-gates.md
        │   ├── repository-intelligence.md
        │   ├── maintenance-policy.md
        │   ├── documentation-policy.md
        │   ├── github-presentation-policy.md
        │   ├── security-testing-policy.md
        │   ├── repair-and-regression-policy.md
        │   └── git-workflow-policy.md
        └── scripts/
            ├── repocraft_intel.py
            ├── repocraft_maintenance.py
            ├── repocraft_security.py
            ├── repocraft_repair.py
            ├── repocraft_git.py
            ├── repocraft_status.py
            ├── repocraft_release.py
            └── engine/
                ├── discovery.py
                ├── file_inventory.py
                ├── architecture.py
                ├── git_analyzer.py
                ├── governance.py
                ├── testing_ci.py
                ├── health_assessor.py
                ├── report_generator.py
                ├── orchestrator.py
                ├── maintenance/
                │   ├── reference_analyzer.py
                │   ├── unused_file_detector.py
                │   ├── organization_analyzer.py
                │   ├── readme_analyzer.py
                │   ├── readme_generator.py
                │   ├── documentation_auditor.py
                │   ├── license_auditor.py
                │   ├── media_auditor.py
                │   ├── github_presentation.py
                │   ├── maintenance_planner.py
                │   └── maintenance_orchestrator.py
                ├── security/
                │   ├── types.py
                │   ├── secret_scanner.py
                │   ├── dependency_auditor.py
                │   ├── security_pattern_analyzer.py
                │   ├── configuration_auditor.py
                │   ├── supply_chain_analyzer.py
                │   ├── test_discovery.py
                │   ├── test_readiness.py
                │   ├── test_runner.py
                │   ├── test_result_analyzer.py
                │   ├── cicd_analyzer.py
                │   ├── security_risk_assessor.py
                │   ├── security_report_generator.py
                │   └── security_orchestrator.py
                ├── repair/
                │   ├── repair_types.py
                │   ├── finding_ingestor.py
                │   ├── repair_classifier.py
                │   ├── risk_assessor.py
                │   ├── patch_generator.py
                │   ├── repair_planner.py
                │   ├── approval_manager.py
                │   ├── change_guard.py
                │   ├── backup_manager.py
                │   ├── repair_executor.py
                │   ├── repair_validator.py
                │   ├── regression_runner.py
                │   ├── attempt_controller.py
                │   ├── rollback_manager.py
                │   ├── repair_report_generator.py
                │   └── repair_orchestrator.py
                └── git/
                    ├── git_types.py
                    ├── git_environment.py
                    ├── git_status_analyzer.py
                    ├── diff_analyzer.py
                    ├── change_risk_analyzer.py
                    ├── change_review.py
                    ├── staging_planner.py
                    ├── staging_approval.py
                    ├── staging_executor.py
                    ├── commit_message_generator.py
                    ├── commit_approval.py
                    ├── commit_executor.py
                    ├── remote_inspector.py
                    ├── push_approval.py
                    ├── push_executor.py
                    ├── pull_request_planner.py
                    ├── git_report_generator.py
                    └── git_orchestrator.py
                ├── release/
                │   ├── manifest_generator.py
                │   ├── package_builder.py
                │   ├── integrity_verifier.py
                │   ├── reproducibility_checker.py
                │   ├── release_validator.py
                │   └── release_orchestrator.py
                └── distribution/
                    ├── distribution_types.py
                    ├── release_notes_generator.py
                    ├── announcement_generator.py
                    ├── distribution_verifier.py
                    ├── installation_tester.py
                    ├── upgrade_manager.py
                    ├── maintenance_auditor.py
                    └── distribution_orchestrator.py
```

## Phase 1: Repository Intelligence Engine

Installed projects can run RepoCraft's read-only repository intelligence engine to inspect project health and architecture without making any modifications:

```bash
python .agent/skills/repocraft/scripts/repocraft_intel.py --target . --output ../repocraft-reports
```

### Generated Artifacts
- `inventory.json`: Full machine-readable inventory of metadata, ecosystem, file stats, and Git state.
- `repository-overview.md`: Evidence-backed architecture overview, entry points, and tech stack details.
- `repository-audit.md`: Comprehensive audit matrix covering Git baseline, governance, hygiene, and health findings.
- `recommendations.json`: Prioritized, machine-readable findings with severity, confidence, actions, and target phases.

## Phase 2: Maintenance, Documentation & GitHub Presentation Engine

Run the maintenance and presentation engine in audit, draft, or apply mode:

```bash
# Audit mode (default: read-only inspection)
python .agent/skills/repocraft/scripts/repocraft_maintenance.py --target . --reports ../repocraft-reports --mode audit

# Draft mode (emits proposed documentation and maintenance drafts)
python .agent/skills/repocraft/scripts/repocraft_maintenance.py --target . --reports ../repocraft-reports --mode draft

# Apply mode (applies reviewed, policy-authorized changes under safeguards)
python .agent/skills/repocraft/scripts/repocraft_maintenance.py --target . --reports ../repocraft-reports --mode apply
```

### Generated Artifacts
- `maintenance-analysis.json`: Codebase organization findings, duplicate files, and calibrated unused-file candidates.
- `README-improved.md`: Tailored, evidence-grounded proposed README draft without hallucinations.
- `documentation-audit.md`: Document inventory, link/image integrity, governance status, and command consistency.
- `github-presentation-audit.md`: Branding assessment, recommended topics/description, Mermaid diagrams, and remote boundary safeguards.
- `maintenance-plan.json`: Prioritized, actionable maintenance tasks with risk ratings and approval requirements.
- `phase2-report.md`: Complete audit and maintenance execution report.

## Phase 3: Security, Testing & CI/CD Validation Engine

Run the security and testing validation engine in audit mode (or with explicit test execution authorization):

```bash
# Audit mode (default: read-only analysis without executing tests)
python .agent/skills/repocraft/scripts/repocraft_security.py --target . --reports ../repocraft-reports --mode audit

# Test execution mode (explicitly authorized to execute discovered test suites)
python .agent/skills/repocraft/scripts/repocraft_security.py --target . --reports ../repocraft-reports --mode audit --execute-tests
```

### Generated Artifacts
- `security-findings.json`: All discovered secrets, code pattern risks, configuration findings, and supply chain issues.
- `dependency-audit.json`: Manifests, pinned/unpinned dependencies, lockfile presence, and offline status.
- `test-analysis.json`: Discovered test frameworks, test files, empty test files, and readiness blockers.
- `test-execution-report.json`: Execution status (`PASSED`, `FAILED`, `NOT_RUN`, `BLOCKED_BY_POLICY`, `TIMED_OUT`), exit codes, durations, and redacted outputs.
- `cicd-audit.json`: Workflow triggers, jobs, step coverage, action pinning, and permissions.
- `security-quality-report.md`: Detailed human-readable markdown report with findings tables and actionable remediations.
- `phase3-report.md`: Executive summary scorecard and human verification requirements.

## Phase 4: Bounded Repair, Safe Code Improvements & Regression Validation Engine

Run the repair and regression engine in `plan` (default), `draft`, or `apply-approved` mode:

```bash
# Plan mode (default: ingests findings, plans repairs, leaves target 100% untouched)
python .agent/skills/repocraft/scripts/repocraft_repair.py --target . --reports ../repocraft-reports --mode plan

# Draft mode (generates proposed patches and approval manifest template)
python .agent/skills/repocraft/scripts/repocraft_repair.py --target . --reports ../repocraft-reports --mode draft

# Apply-approved mode (applies only policy-permitted and human-authorized repairs under safeguards)
python .agent/skills/repocraft/scripts/repocraft_repair.py --target . --reports ../repocraft-reports --mode apply-approved --approval-file ../repocraft-reports/approval-manifest.json
```

### Generated Artifacts
- `repair-findings.json`: All normalized findings ingested from Phase 1, 2, and 3.
- `repair-plan.json`: Full repair plan with tasks, priorities, risk ratings, and proposed patches.
- `approval-manifest.json`: Per-task approval status and expected patch hashes.
- `repair-execution.json`: Execution results, modified files, and applied patches.
- `regression-comparison.json`: Baseline vs post-repair validation comparisons.
- `rollback-report.json`: Rollback actions, restored files, and protected user modifications.
- `phase4-report.md`: Comprehensive executive report, scorecards, and remaining manual recommendations.

## Phase 5: Git Review, Conditional Commit & Publishing Engine

Run the Git review, staging, commit, and publishing engine:

```bash
# 1. Inspect repository state (read-only)
python .agent/skills/repocraft/scripts/repocraft_git.py inspect --target-dir .

# 2. Review changes and file risks
python .agent/skills/repocraft/scripts/repocraft_git.py review --target-dir . --reports-dir ../repocraft-reports

# 3. Plan deterministic staging (no git add .)
python .agent/skills/repocraft/scripts/repocraft_git.py plan-stage --target-dir . --reports-dir ../repocraft-reports

# 4. Stage approved files
python .agent/skills/repocraft/scripts/repocraft_git.py stage-approved --target-dir . --manifest ../repocraft-reports/staging-approval.json

# 5. Draft Conventional Commit proposal
python .agent/skills/repocraft/scripts/repocraft_git.py draft-commit --target-dir . --reports-dir ../repocraft-reports

# 6. Commit approved changes
python .agent/skills/repocraft/scripts/repocraft_git.py commit-approved --target-dir . --manifest ../repocraft-reports/commit-approval.json

# 7. Inspect remote configuration and divergence
python .agent/skills/repocraft/scripts/repocraft_git.py inspect-remote --target-dir .

# 8. Plan remote publishing
python .agent/skills/repocraft/scripts/repocraft_git.py plan-push --target-dir . --reports-dir ../repocraft-reports

# 9. Push approved commit to verified remote
python .agent/skills/repocraft/scripts/repocraft_git.py push-approved --target-dir . --manifest ../repocraft-reports/push-approval.json

# 10. Draft evidence-backed pull request proposal
python .agent/skills/repocraft/scripts/repocraft_git.py draft-pr --target-dir . --reports-dir ../repocraft-reports
```

### Generated Artifacts
- `git-state.json`: Repository environment snapshot.
- `git-change-review.md`: Human-readable Markdown change and risk review.
- `git-change-review.json`: Structured file-level change classifications and risk metrics.
- `staging-plan.json`: Exact proposed staging scope and diff hashes.
- `staging-approval.json`: Human-editable staging authorization manifest.
- `staging-result.json`: Staging verification record and post-stage diff hash.
- `commit-proposal.md`: Proposed Conventional Commit message with rationale.
- `commit-approval.json`: Exact commit authorization manifest.
- `commit-receipt.json`: Post-commit verification receipt with commit hash and parent.
- `remote-status.json`: Sanitized remote configuration and tracking status.
- `push-plan.json`: Proposed publishing destination, base checks, and divergence state.
- `push-approval.json`: Explicit publishing authorization manifest.
- `push-result.json`: Remote publishing verification record.
- `pull-request-draft.md`: Pull request description based on evidence and test logs.
- `git-workflow-report.md`: End-to-end Git workflow and audit summary.

---

## Phase 6: Diagnostic CLI & Release Readiness

RepoCraft provides a dedicated read-only diagnostic command for inspecting environment health, agent detection, and package integrity:

```bash
# Human-readable diagnostic overview
python skill/scripts/repocraft_status.py

# Machine-readable JSON output
python skill/scripts/repocraft_status.py --json

# Verify installed skill files against INSTALL-MANIFEST.json
python skill/scripts/repocraft_status.py --verify-installation

# Verify integrity and safety of a release package archive
python skill/scripts/repocraft_status.py --verify-package dist/repocraft-1.0.0-rc1.zip
```

### Supported Agent Compatibility

| Agent | Support Level | Discovery | CLI Execution | Status |
| --- | --- | --- | --- | --- |
| **Google Antigravity** | `SUPPORTED` | Native `.agent/skills/` | Full | Certified Primary Target |
| **Claude Code** | `INSTALLATION_ONLY` | Manual prompt required | Terminal tool | Installation Verified |
| **Cursor IDE** | `MANUAL_CONFIGURATION_REQUIRED` | Rule adapter | Integrated terminal | Manual Rule Required |
| **Project-Local Standalone** | `MANUAL_CONFIGURATION_REQUIRED` | Direct invocation | Python CLI | Verified Standalone |

---

## Phase 7: Release Publication, Distribution, Adoption & Maintenance

RepoCraft includes an evidence-backed release, distribution verification, upgrade planning, and post-release maintenance engine:

```bash
# Inspect release readiness and version alignment
python skill/scripts/repocraft_release.py inspect-release

# Validate all release gates programmatically
python skill/scripts/repocraft_release.py validate-release --json

# Draft comprehensive release notes from phase metadata
python skill/scripts/repocraft_release.py draft-release-notes

# Verify distribution package archive integrity and traversal safety
python skill/scripts/repocraft_release.py verify-distribution --package dist/repocraft-1.0.0-rc1.zip

# Execute automated clean installation and backup tests
python skill/scripts/repocraft_release.py test-installation

# Plan an in-place upgrade to a target version
python skill/scripts/repocraft_release.py plan-upgrade --target-version 1.0.0

# Audit post-release health, manifest consistency, and zero telemetry
python skill/scripts/repocraft_release.py generate-maintenance-report
```

### Generated Artifacts
- `release-validation.json`: Version alignment, gate evaluation, and release candidate validation.
- `release-notes-draft.md`: Structured, evidence-backed changelog and phase summaries for maintainer review.
- `release-announcement-draft.md`: Formatted release announcement for user adoption.
- `distribution-verification.json`: Archive integrity, cryptographic hashes, entry count, and traversal safety.
- `installation-acceptance.json`: Clean installation test results and user file preservation verification.
- `upgrade-validation.json`: Upgrade simulation, backup creation verification, and rollback validation.
- `maintenance-report.json`: Post-release health audit, manifest consistency, and AST-verified zero telemetry.
- `phase7-report.md`: Comprehensive Phase 7 distribution and maintenance executive report.

---

## Safety contract

- Installation writes only to the selected RepoCraft skill destination.
- Existing destination files are backed up or installation stops; no silent overwrite.
- Installing RepoCraft does not run project commands, install project dependencies, edit application source, commit, or push.
- The skill treats repository content as untrusted data, not instructions.
- No secrets are printed, copied into reports, or uploaded. `.env` and private keys are never read or output.
- All pre-existing Git modifications are treated as user-owned and never touched, staged, or committed.
- Uncertain unused files are never automatically deleted.
- Licenses are never selected, overwritten, or created on behalf of the user.
- Remote GitHub metadata changes are blocked unless explicitly authorized.
- Publishing is conditional and must respect the configured policy and branch protections.
- Unknown or unverified checks are never reported as passed.
- Never declare a repository 100% secure; absence of findings does not equal proof of security.
- Tests are never executed without explicit user opt-in (`--execute-tests`).
- Never overwrite user modifications during automated rollbacks.
- Enforce strict 3-attempt limit per unique root cause across executions and restarts.
- Approval for one Git operation never authorizes another: staging != commit != push != PR.
- Strict prohibition of force pushes, blind staging (`git add .`), commit hook bypassing, and history rewrites.
- Gate E Safety Invariant: The RepoCraft development repository is NEVER committed or pushed automatically.

## Development status

- **Phase 0 (Foundation & Scaffold)**: Complete.
- **Phase 1 (Repository Intelligence Engine)**: Complete. Verified across 22 contract and fixture tests.
- **Phase 2 (Maintenance, Documentation & Presentation)**: Complete. Fully verified across 41 dedicated fixture tests.
- **Phase 3 (Security, Testing & CI/CD)**: Complete. Fully implemented and verified across 70 dedicated fixture tests.
- **Phase 4 (Bounded Repair & Regression)**: Complete. Fully implemented and verified across 82 dedicated fixture tests.
- **Phase 5 (Git Review, Conditional Commit & Publishing Engine)**: Complete. Fully implemented and verified across 101 dedicated fixture tests.
- **Phase 6 (Agent Compatibility, Release Packaging & Production Readiness)**: Complete. Release candidate v1.0.0-rc1 packaged, integrity-verified, and certified.
- **Phase 7 (Release Publication, Distribution, Adoption & Post-Release Maintenance)**: Complete. Distribution verification, non-destructive upgrade/rollback, multi-platform CI/CD, adoption documentation, and post-release maintenance auditing completed. Candidate distribution ready for maintainer sign-off under Gate E.
