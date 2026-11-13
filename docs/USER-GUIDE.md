# RepoCraft User & Adoption Guide

## 1. What is RepoCraft?

RepoCraft is a portable repository-engineering skill package designed to run inside supported AI coding agents. It understands existing codebases, audits repository health, identifies maintenance and security improvements, plans safe repairs, verifies changes through regression testing, and conditionalizes publishing under explicit human-in-the-loop authorization gates.

RepoCraft is **NOT**:
- A standalone web application or hosted SaaS dashboard.
- A replacement application generator.
- A tool designed exclusively for a single programming language or framework.
- An autonomous rewriter that silently mutates or publishes your code.

---

## 2. Quick-Start Installation

### Prerequisites
- Python >= 3.9 installed on your system.
- Git >= 2.20.
- A supported coding agent (Google Antigravity is the primary certified agent).

### Obtaining RepoCraft from GitHub
```bash
git clone https://github.com/Sanjaycs096/REPOCRAFT.git
```

### Installing into an Existing Target Repository
From your project's root directory:

```bash
# Install for Google Antigravity (default target: .agent/skills/repocraft/)
python /path/to/REPOCRAFT/install.py --target .

# Or install for generic project fallback:
python /path/to/REPOCRAFT/install.py --target . --agent project
```

The installer copies only RepoCraft's instructions, reference policies, and runtime engines. It **never modifies your project's source code or dependencies during installation**.

---

## 3. First-Run & Master Prompt

Open your project in **Google Antigravity** and invoke RepoCraft with the master prompt:

> **Run RepoCraft on this repository. Inspect the complete project, establish its Git and quality baseline, identify improvements, then safely maintain the codebase, documentation, GitHub presentation, security posture, tests, and CI/CD. Repair verified issues within policy, rerun relevant checks, review the complete diff, and publish only if every publishing condition is satisfied. Preserve my existing work. Produce a terminal summary and a detailed Markdown report.**

Antigravity will automatically discover the skill instructions in `.agent/skills/repocraft/SKILL.md` and execute the pipeline safely.

---

## 4. Multi-Phase Lifecycle Architecture

RepoCraft executes through seven ordered, evidence-backed phases:

```text
INSTALL → INITIALIZE → INTELLIGENCE → MAINTENANCE → SECURITY → REPAIR → GIT_REVIEW → CONDITIONAL_PUBLISH → REPORT
```

1. **Phase 0 (Initialization)**: Verifies Git worktree, records branch and HEAD, identifies pre-existing user changes, and protects uncommitted work.
2. **Phase 1 (Intelligence)**: Inventories files, identifies tech stack, detects entry points, and discovers test/build commands (read-only).
3. **Phase 2 (Maintenance & Presentation)**: Audits directory structure, unused files, README quality (18 dimensions), documentation links, licenses, and GitHub presentation.
4. **Phase 3 (Security & CI/CD)**: Scans for high-entropy secrets (with strict redaction), audits dependencies and unpinned actions, inspects unsafe patterns, and runs whitelisted tests when opted in.
5. **Phase 4 (Bounded Repair)**: Ingests findings, classifies risks, prepares hash-bound approval manifests, creates verified external backups, applies bounded patches, and enforces a strict 3-attempt limit with automated rollback.
6. **Phase 5 (Git Review & Conditional Publish)**: Evaluates file-level risk, prepares deterministic staging plans, drafts Conventional Commits, inspects remotes, and publishes fast-forward commits only upon independent cryptographic authorization.
7. **Phase 6 (Compatibility & Release Readiness)**: Audits agent compatibility, verifies artifact schemas, packages deterministic distribution archives, and provides diagnostic CLI commands.

---

## 5. CLI Reference

All CLI tools reside in `scripts/` inside your installed skill:

```bash
# Environment diagnostics and installation verification
python .agent/skills/repocraft/scripts/repocraft_status.py --verify-installation

# Phase 1: Repository intelligence audit
python .agent/skills/repocraft/scripts/repocraft_intel.py --target . --output ../repocraft-reports

# Phase 2: Codebase and documentation audit
python .agent/skills/repocraft/scripts/repocraft_maintenance.py --target . --reports ../repocraft-reports --mode audit

# Phase 3: Security & testing audit
python .agent/skills/repocraft/scripts/repocraft_security.py --target . --reports ../repocraft-reports --mode audit

# Phase 4: Repair planning
python .agent/skills/repocraft/scripts/repocraft_repair.py --target . --reports ../repocraft-reports --mode plan

# Phase 5: Git review
python .agent/skills/repocraft/scripts/repocraft_git.py review --target . --reports ../repocraft-reports

# Phase 7: Release & distribution management
python .agent/skills/repocraft/scripts/repocraft_release.py validate-release --json
```

---

## 6. Safety & Approval Model

RepoCraft strictly adheres to the **Independent Cryptographic Approval Invariant**:
- Approval to stage files does **NOT** grant approval to commit.
- Approval to commit does **NOT** grant approval to push.
- Approval to push does **NOT** grant approval to draft or submit pull requests.
- Force-pushes (`--force`, `--force-with-lease`), history rewrites, and pre-commit hook bypassing are strictly forbidden.
- Gate E: The RepoCraft development repository itself is never auto-committed or auto-pushed.

---

## 7. Troubleshooting Guide

- **`STOP: destination already exists`**: RepoCraft detected an existing installation. Re-run with `--force` or `--upgrade` to create an automatic backup before replacing.
- **`Branch mismatch in staging approval`**: The repository was switched to another branch after the staging plan was generated. Regenerate the plan with `repocraft_git.py plan-stage`.
- **`Patch hash mismatch`**: The target file was modified by the user after the repair plan was created. RepoCraft halts to prevent overwriting user modifications.

