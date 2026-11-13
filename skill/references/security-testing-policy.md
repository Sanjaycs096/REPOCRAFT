# RepoCraft Security & Testing Validation Policy

This policy governs the behavior, boundaries, and safety constraints of the **RepoCraft Phase 3 Security, Testing & CI/CD Validation Engine**.

---

## 1. Fundamental Principles

1. **Never Claim 100% Secure**:
   - Absence of findings from static scanners, linters, or pattern matchers is NOT proof of security.
   - The engine explicitly labels all scans as heuristic audits and never declares any repository "completely secure" or "guaranteed vulnerability-free".

2. **Strict Evidence & Operational Boundaries**:
   The engine always separates:
   - **Verified**: Directly observed facts (e.g. file existence, regex matches, executed command exit codes).
   - **Inferred**: Derived conclusions (e.g. risk level, credential exposure likelihood).
   - **Executed**: Commands actually run on the local machine with explicit authorization.
   - **Unverified**: Status of external dependencies and CVE databases when evaluated offline.
   - **Human Approval Required**: Any change that modifies credentials, dependencies, or permissions.

---

## 2. Secret Redaction & Handling Policy

1. **Mandatory Redaction**:
   - Plaintext secrets, private keys, API tokens, passwords, and connection strings must NEVER be printed to terminal stdout/stderr, written unredacted to JSON/Markdown artifacts, or surfaced unredacted in agent responses.
   - All secret evidence is masked (e.g. `sk_live_...` -> `sk_live_********` or `[REDACTED]`).

2. **Sensitive File Quarantine**:
   - Committed `.env`, `.pem`, `.key`, or `id_rsa` files are flagged as critical/high security risks.
   - RepoCraft does NOT delete or rewrite user credential files automatically in Phase 3; it notifies the user and provides actionable guidance.

---

## 3. Sandboxed & Offline Execution Policy

1. **No External Network Calls by Default**:
   - The security auditor runs completely offline.
   - Dependency vulnerability checks default to `UNVERIFIED` in offline environments rather than fabricating or assuming clean CVE status.

2. **Controlled Subprocess Execution**:
   - In default `audit` mode, NO user code or test suite is executed.
   - Subprocess execution is strictly gated behind the explicit `--execute-tests` CLI flag.
   - Commands are validated against an allowed prefix whitelist:
     `pytest`, `python -m pytest`, `python -m unittest`, `npm test`, `npm run test`, `yarn test`, `pnpm test`, `cargo test`, `go test`, `mvn test`, `./gradlew test`, `gradle test`.
   - Any command containing destructive operators, shell redirection, `rm`, `del`, `sudo`, `install`, `deploy`, or chaining (`&&`, `;`, `||`, `|`) is blocked with state `BLOCKED_BY_POLICY`.
   - Execution has a hard timeout of 30 seconds per suite.
   - Terminal stdout and stderr are sanitized and truncated at 20,000 characters to prevent buffer bloat.

---

## 4. Supply Chain & CI/CD Rules

1. **Immutable Action Pinning**:
   - GitHub Actions referenced by mutable tags (e.g. `@v3`, `@main`) are flagged for supply chain pinning to immutable 40-character commit SHAs.

2. **Least Privilege Permissions**:
   - Workflows with `permissions: write-all` or unconstrained access are flagged as high risk.

3. **Untrusted Script Injection Prevention**:
   - Direct interpolation of `${{ github.event.* }}` (such as PR titles, issue bodies, or comments) into shell scripts is flagged as critical/high command injection risk.

---

## 5. Artifact Delivery Contract

Phase 3 produces 7 dedicated validation artifacts stored strictly outside the target repository:

1. `security-findings.json`: All discovered secrets, code pattern risks, configuration findings, and supply chain issues.
2. `dependency-audit.json`: Manifests, pinned/unpinned dependencies, lockfile presence, and offline status.
3. `test-analysis.json`: Discovered test frameworks, test files, empty test files, and readiness blockers.
4. `test-execution-report.json`: Execution status (`PASSED`, `FAILED`, `NOT_RUN`, `BLOCKED_BY_POLICY`, `TIMED_OUT`), exit codes, durations, and redacted outputs.
5. `cicd-audit.json`: Workflow triggers, jobs, step coverage, action pinning, and permissions.
6. `security-quality-report.md`: Detailed human-readable markdown report with findings tables and actionable remediations.
7. `phase3-report.md`: Executive summary scorecard and human verification requirements.

