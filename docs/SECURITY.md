# Security Policy for RepoCraft

The RepoCraft maintainers and community take software security, developer safety, and privacy with utmost seriousness. Because RepoCraft runs in developer environments and inside AI coding agents, our security posture is engineered to prevent unauthorized code modifications, data leakage, and supply-chain vulnerabilities.

---

## 1. Supported Versions

Security updates and patches are actively provided for the following releases:

| Version | Supported | Status |
| :--- | :--- | :--- |
| `1.0.x` / `1.0.0-rc1` | :white_check_mark: Yes | Current Active Release Candidate |
| `< 1.0.0` | :x: No | Development fixtures and prototypes |

---

## 2. Core Security Model & Architectural Guarantees

RepoCraft is built from the ground up with defensive security principles:

### 2.1 Offline, Zero-Telemetry Execution
- RepoCraft **never** phones home, transmits metrics, or initiates outbound network calls.
- There are no analytics beacons, crash reporters, or tracking identifiers embedded in the engine or CLI drivers.
- All analysis, auditing, repair planning, and verification operations execute locally on the host machine.

### 2.2 Strict Secret Protection & Plaintext Redaction
- The security engine (Phase 3) scans codebases for leaked credentials, private keys, API tokens, and high-entropy strings.
- **Invariant**: Secrets discovered during analysis are **never** logged, persisted in reports, or included in commit messages in plaintext.
- All identified secrets are immediately replaced with cryptographic redaction markers (`[REDACTED:entropy-token-sha256:...]`) before writing to reports or terminal outputs.

### 2.3 Bounded Repair & Automatic Rollback
- The repair engine (Phase 4) will **never** perform unbounded autonomous code generation.
- All proposed fixes must match pre-declared repair categories (`readme_repair`, `gitignore_sync`, `license_fix`, `workflow_pinning`).
- Before applying any modification, an external backup is generated and verified.
- The repair engine enforces a strict **3-attempt maximum**. If regression tests fail or new defects are introduced, the engine immediately initiates a verified rollback to the pre-repair snapshot.

### 2.4 Cryptographic Approval Separation (Gates A–D)
- RepoCraft strictly enforces distinct, non-transitive human approval boundaries:
  - **Gate A (Staging Approval)**: Does not grant permission to commit.
  - **Gate B (Commit Approval)**: Does not grant permission to push.
  - **Gate C (Push Approval)**: Requires explicit opt-in confirmation; force-pushes are programmatically blocked.
  - **Gate D (PR Drafting)**: Drafts pull request summaries for review only without autonomous submission.
- **Gate E (Development Repository Protection)**: The RepoCraft development repository itself cannot be automatically committed, pushed, or tagged by its own engine.

### 2.5 Archive Integrity & Path Traversal Safeguards
- Distribution archives (`dist/repocraft-*.zip`) are validated against SHA-256 cryptographic digests.
- The package unpacker and installer explicitly check for **Zip Slip** vulnerabilities (directory traversal via `../` or absolute path prefixes). Any entry attempting to write outside the destination root causes immediate abort.

---

## 3. Reporting a Vulnerability

If you believe you have discovered a security vulnerability in RepoCraft:

1. **Do NOT report security vulnerabilities via public GitHub issues, discussions, or pull requests.**
2. Send a detailed report via encrypted email to:
   `security@repocraft.local` (or through GitHub's Private Vulnerability Reporting feature once the repository is published).
3. Include in your report:
   - A description of the vulnerability and its potential impact.
   - Exact steps or proof-of-concept code to reproduce the issue safely.
   - The version of RepoCraft, Python, and the operating system tested.
4. **Response Timeline**:
   - Initial acknowledgment: within **24 hours**.
   - Triage and vulnerability validation: within **48 hours**.
   - Remediation and patch release: within **7 business days**.

We deeply appreciate responsible disclosure and will credit researchers in our release notes and security advisories.

