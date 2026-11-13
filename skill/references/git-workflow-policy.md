# RepoCraft Git Workflow and Publishing Policy

This document defines the strict operational rules, risk classifications, approval protocols, and safety guarantees for Git review, conditional staging, atomic committing, and verified publishing in RepoCraft Phase 5.

---

## 1. Core Principles

1. **Explicit Operational State Machine**:
   ```
   INSPECT → REVIEW → PLAN → APPROVE_STAGE → STAGE → VERIFY_STAGE → APPROVE_COMMIT → COMMIT → VERIFY_COMMIT → APPROVE_PUSH → PUSH → VERIFY_REMOTE
   ```
2. **Strict Independence of Approvals**:
   Approval for one Git operation never grants approval for another:
   - Staging approval does NOT authorize committing.
   - Commit approval does NOT authorize pushing.
   - Push approval does NOT authorize PR creation or release tagging.
   - Review completion does NOT authorize staging.
3. **Preservation of User Work**:
   RepoCraft must never silently:
   - Discard unstaged user modifications.
   - Reset or overwrite existing staged user modifications.
   - Delete untracked files or clean the working tree.
   - Stash user changes.
   - Rewrite Git history.
   - Perform force pushes (`--force`, `-f`, or `--force-with-lease`).
4. **Deterministic and Bounded Staging**:
   - `git add .` and `git add -A` are strictly forbidden.
   - Only explicitly approved file paths or validated hunks may be added to the index.
   - Paths outside the repository or path traversal attempts (`../`) are rejected.
5. **No Network Access by Default**:
   - Remote inspection is local and read-only by default.
   - Publishing operations require separate, explicit human authorization.
6. **Credential Redaction**:
   - URLs containing embedded credentials (`https://user:token@github.com/...`) are sanitized in memory, logs, and reports.
   - Raw environment variables and private tokens are never stored or printed.

---

## 2. Risk Classification Rules

Every changed file and hunk is evaluated against risk categories:

| Risk Tier | Criteria | Permitted Operations | Approval Requirement |
| :--- | :--- | :--- | :--- |
| `LOW` | Documentation, formatting, non-code assets, verified configuration comments | Plan, review, stage (if approved) | Per-operation approval |
| `MEDIUM` | Structural configs, safe `.gitignore` additions, test files, non-critical dev scripts | Plan, review, stage (if approved) | Explicit approval |
| `HIGH` | CI/CD workflows, dependency manifests/lockfiles, build scripts, deployment configs | Plan, review | Explicit per-operation approval required |
| `CRITICAL` | Auth/authz, crypto, payment logic, secret-bearing files, database migrations, licensing changes | Plan, review only | **CANNOT** be automatically staged or committed; manual developer intervention required |
| `UNKNOWN` | Unrecognized extensions, unparsed binary diffs, oversized files | Conservative handling | Treated as `HIGH` risk; explicit manual review required |

### Safety Constraints:
- **Test Weakening**: Removing or weakening test assertions is flagged as a high-risk policy violation.
- **License Changes**: Automatic license alterations are classified as `CRITICAL` and rejected.
- **Secrets in Diffs**: Potential secrets (API keys, private keys, passwords) are flagged; secret values are masked in reports.

---

## 3. Approval Protocols & Cryptographic Invalidation

### 3.1 Staging Approval (`staging-approval.json`)
Binds:
- Repository root path and repository ID
- Current branch and HEAD commit hash
- Approved file path list and hunk identifiers
- Expected original content hash (SHA-256)
- Expected staged patch hash (SHA-256)
- Approver identity and timestamp

**Invalidation Triggers**:
- Target file content modified after plan creation (`CONTENT_HASH_MISMATCH`)
- Branch or HEAD commit shifted (`HEAD_MISMATCH`)
- Path traversal or path outside repo detected (`PATH_OUTSIDE_REPO`)
- Blanket or wildcard approval attempted (`WILDCARD_APPROVAL_REJECTED`)
- Task categorized as `CRITICAL` (`CRITICAL_STAGING_FORBIDDEN`)

### 3.2 Commit Approval (`commit-approval.json`)
Binds:
- Exact staged patch hash (SHA-256 of staged diff)
- Parent commit hash
- Current branch
- Commit message text and commit message hash (SHA-256)
- Approved file list
- Approver identity and timestamp

**Invalidation Triggers**:
- Index differs from approved staged patch hash
- Parent commit differs
- Branch switched or detached HEAD
- Commit message edited without re-approval

### 3.3 Push Approval (`push-approval.json`)
Binds:
- Remote name and sanitized remote URL
- Source branch and destination branch
- Exact commit hash to be published
- Expected remote base commit hash
- Approver identity and timestamp

**Forbidden Push Behaviors**:
- Force push (`--force`, `--force-with-lease`)
- Pushing unapproved branches or tags
- Deleting remote branches
- Rewriting remote history

---

## 4. Hook and Environment Handling

- **Git Hooks**: Executed naturally by Git. RepoCraft never passes `--no-verify`. If a hook fails, the commit is aborted, user modifications are preserved, and the hook failure output is recorded in `commit-receipt.json`.
- **Detached HEAD**: Creating commits on a detached HEAD is rejected (`DETACHED_HEAD_REJECTED`).
- **Unresolved Operations**: Commits are rejected if a merge, rebase, cherry-pick, or revert is in progress (`OPERATION_IN_PROGRESS`).

---

## 5. Artifact Contracts

Executing Phase 5 produces 15 artifacts:
1. `git-state.json`: Repository environment, Git version, branches, remotes, operation status.
2. `git-change-review.md`: Human-readable Markdown change review.
3. `git-change-review.json`: Structured review with file-level risk classifications.
4. `staging-plan.json`: Exact proposed staging scope and diff hashes.
5. `staging-approval.json`: Human-editable staging authorization manifest.
6. `staging-result.json`: Staging verification record and post-stage diff hash.
7. `commit-proposal.md`: Proposed conventional commit message with rationale.
8. `commit-approval.json`: Exact commit authorization manifest.
9. `commit-receipt.json`: Post-commit verification receipt with commit hash and parent.
10. `remote-status.json`: Sanitized remote configuration and tracking status.
11. `push-plan.json`: Proposed publishing destination, base checks, and divergence state.
12. `push-approval.json`: Explicit publishing authorization manifest.
13. `push-result.json`: Remote publishing verification record.
14. `pull-request-draft.md`: Pull request description based on evidence and test logs.
15. `git-workflow-report.md`: End-to-end Git workflow and audit summary.

---

## 6. Exit Codes

| Code | Meaning |
|---|---|
| `0` | Operation completed and verified successfully |
| `1` | Invalid arguments or input parameters |
| `2` | Validation failed (e.g. hash mismatch, syntax error) |
| `3` | Approval missing, invalid, or expired |
| `4` | Repository safety guard blocked operation (e.g. user modifications, path traversal) |
| `5` | Git command execution failed |
| `6` | Remote conflict, divergence, or publishing rejected |
| `7` | Unsupported repository state (e.g. detached HEAD, rebase in progress) |
| `8` | Verification incomplete or unavailable |

