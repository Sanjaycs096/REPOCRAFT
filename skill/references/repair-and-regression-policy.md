# RepoCraft Bounded Repair & Regression Policy

This policy governs the behavior, boundaries, and safety constraints of the **RepoCraft Phase 4 Bounded Repair, Safe Code Improvements & Regression Validation Engine**.

---

## 1. Fundamental Principles

1. **Controlled Improvement, Not Unrestricted Rewriting**:
   - RepoCraft behaves like a careful senior engineer, not an autonomous auto-fixer.
   - It repairs only what is justified by evidence, respects user ownership, applies the smallest safe repair, and validates every outcome.
   - A repair is considered successful ONLY when the expected result is verified and regression checks pass.

2. **Strict Operational Boundaries**:
   The engine explicitly tracks the lifecycle state of every finding:
   - Finding detected
   - Repair recommended
   - Repair planned
   - Approval required
   - Repair authorized
   - Repair applied
   - Validation passed
   - Validation failed
   - Repair rolled back
   - Repair blocked

---

## 2. Risk Classification & Approval Policy

Every proposed repair is assigned a risk level and approval requirement:

### `LOW` Risk
- Narrowly scoped, high confidence, reversible, with local validation available.
- Examples: Correcting broken relative documentation links, fixing verified README command mismatches, fixing harmless typos.
- **Policy**: Potentially autonomous when no user-owned modification is involved.

### `MEDIUM` Risk
- Moving files, renaming files, build configuration changes, non-production application configuration, test configuration.
- **Policy**: Requires explicit human approval unless specifically authorized.

### `HIGH` Risk
- Dependency upgrades, security-sensitive code changes, CI/CD workflow modifications, Dockerfile changes, production configuration, authentication/authorization logic.
- **Policy**: ALWAYS requires explicit human approval via the approval manifest.

### `CRITICAL` Risk
- Cryptographic implementation changes, secret rotation or revocation, destructive file or history operations, license replacement, repository visibility or ownership changes.
- **Policy**: NEVER autonomously applied or executed in batch mode. Strictly requires manual human remediation.

---

## 3. Repository Change Guard & User Protection

Before any file modification:
1. Git working tree state is captured via `git status --porcelain`.
2. Staged, unstaged, and untracked files are identified.
3. Pre-existing user modifications are strictly protected:
   - **Never overwrite staged modifications**.
   - **Never overwrite unstaged user changes**.
   - **Never silently modify untracked user files**.
   - **Never stash changes**.
   - **Never run `git reset --hard` or `git clean`**.
   - **Never delete user files automatically**.
   - **Never run `git add .` or stage files**.
   - **Never commit or push**.
   - **Never rewrite Git history**.
4. If a target file has changed since the repair plan was created, that repair is immediately invalidated and marked `REPAIR_BLOCKED`.

---

## 4. Backup & Recovery Integrity

1. **Mandatory Pre-Repair Backups**:
   - Verified backups are created before touching existing files.
   - Stored in an external backup directory (`<reports>/backups/<repair_id>/`) outside the target project.
   - Original file SHA256 checksums are recorded and verified immediately after backup creation.
   - Existing backups are never overwritten.
2. **Rollback Safety**:
   - Rollback is permitted only for RepoCraft-owned modifications.
   - Prior to restoring, current file SHA256 is checked against RepoCraft's post-repair SHA256.
   - If the current file hash does not match, the user has edited the file after RepoCraft repaired it. In this case, rollback is BLOCKED (`ROLLBACK_BLOCKED_USER_MODIFICATION`) to prevent data loss.

---

## 5. Bounded 3-Attempt Root-Cause Limit

1. **Maximum: 3 attempts per root cause**.
   - This limit applies across repeated execution and restarts of the repair workflow (persisted in `attempt-history.json`).
2. **Attempt Behavior**:
   - **Attempt 1**: Inspect failure, propose smallest justified repair, apply if permitted, validate.
   - **Attempt 2**: Inspect new evidence, reassess root cause, propose alternative correction, validate.
   - **Attempt 3**: Final bounded investigation and repair attempt, validate, stop.
3. **Halting Condition**:
   - If 3 unsuccessful attempts are reached, task is marked `MAX_ATTEMPTS_REACHED`, automatic repair halts, and manual investigation is recommended.
   - Repeating the exact same failed patch is strictly forbidden.

---

## 6. Multi-Level Regression Validation

Every applied repair is validated across 4 distinct levels:
- **Level 1 — Patch Integrity**: Verifies target file exists, matches expected SHA256 hash, and contains replacement text.
- **Level 2 — Local Validation**: Structural and syntax validation (Python AST compilation, JSON parsing, Markdown link target existence).
- **Level 3 — Project Quality Gates**: Formatter, linter, and type-checker execution where configured.
- **Level 4 — Full Regression**: Dynamic project test suite execution when authorized (`--execute-tests`).

Validation outcomes use explicit status vocabulary:
`NOT_RUN`, `PASSED`, `FAILED`, `TIMED_OUT`, `BLOCKED_BY_POLICY`, `MISSING_DEPENDENCIES`, `EXECUTION_ERROR`.

Regression outcomes are classified as:
`NEW_FAILURE`, `PRE_EXISTING_FAILURE`, `RESOLVED_FAILURE`, `UNCHANGED_FAILURE`, `NEW_WARNING`, `RESOLVED_WARNING`, `UNVERIFIED`.
Any `NEW_FAILURE` immediately triggers automated rollback!

---

## 7. Artifact Delivery Contract

Phase 4 generates 7 dedicated artifacts outside the target project:
1. `repair-findings.json`: All normalized findings ingested from Phase 1, 2, and 3.
2. `repair-plan.json`: Full repair plan with tasks, priorities, risk ratings, and proposed patches.
3. `approval-manifest.json`: Per-task approval status and expected patch hashes.
4. `repair-execution.json`: Execution results, modified files, and applied patches.
5. `regression-comparison.json`: Baseline vs post-repair validation comparisons.
6. `rollback-report.json`: Rollback actions, restored files, and protected user modifications.
7. `phase4-report.md`: Comprehensive executive report, scorecards, and remaining manual recommendations.

