# Repository Intelligence Reference

This reference guides the execution of **Phase 1: Repository Intelligence**.
Phase 1 is strictly read-only, evidence-based, and non-destructive. It does not install dependencies, execute tests, change application code, or modify Git history.

---

## 1. Intelligence Objectives

When RepoCraft is invoked on a target project, Phase 1 establishes:
1. **Git Safety Baseline**: Worktree state, current branch, HEAD commit, remotes (with credentials redacted), and user-owned modifications.
2. **File Inventory**: Exhaustive classification of all repository files while safely skipping massive vendor/cache trees. Sensitive files (`.env`, private keys) are recorded as metadata only and **never read or printed**.
3. **Ecosystem & Technology Discovery**: Verified detection of languages, frameworks, package managers, manifests, entry points, and monorepository structures.
4. **Architectural Analysis**: Evidence-backed categorization of frontend, backend, routing, API contracts, databases, state management, and deployment. Any unverified dimension is strictly labeled `UNKNOWN`.
5. **Governance & Documentation**: Discovery of README, LICENSE, CONTRIBUTING, CODE_OF_CONDUCT, SECURITY, templates, and CI workflows. Missing documents are recorded as findings, never fabricated.
6. **Quality Gate Discovery**: Extraction of lint, typecheck, build, and test commands from manifests. Commands are recorded as **discovered, not verified**; they are not run in Phase 1.
7. **Health & Risk Assessment**: Prioritized findings classified by evidence and severity.
8. **Artifact Generation**: Deterministic production of 4 standard reports outside the target project by default (`../repocraft-reports/`).

---

## 2. Classification Standards

### Evidence Levels
- `VERIFIED`: Directly established by concrete repository evidence (configuration files, imports, schemas, code definitions).
- `LIKELY`: Supported by strong indirect evidence or standard conventions, but not conclusively proven.
- `UNKNOWN`: Insufficient evidence. Must remain `UNKNOWN`. Never infer or assume architecture.

### Severity Levels
- `CRITICAL`: Immediate security vulnerability, secret leak, or broken build baseline preventing any operation.
- `HIGH`: Major quality, safety, or testing gap (e.g. unignored `.env`, missing tests, uncommitted user changes).
- `MEDIUM`: Important documentation, governance, or CI gap (e.g. missing LICENSE, missing CI workflow, incomplete README).
- `LOW`: Improvement opportunity or organizational recommendation (e.g. missing CONTRIBUTING, scattered root files).
- `INFO`: Informational hygiene note (e.g. missing `.editorconfig`).

---

## 3. Mandatory Safety Rules

- **Zero Secret Exposure**: Never inspect or print contents of `.env*`, `*.pem`, `*.key`, `id_rsa`, or credentials files.
- **Credential Redaction**: Always redact authentication tokens and passwords from remote Git URLs (`https://***@github.com/...`).
- **Protect User Work**: Pre-existing staged, unstaged, or untracked changes belong entirely to the user. Never stash, reset, overwrite, or commit them.
- **No Command Execution**: Discovered tests and build scripts must not be executed during Phase 1.
- **No File Mutation**: No application source files or configurations within the target project are modified in Phase 1.

---

## 4. Output Artifacts

The intelligence engine writes 4 artifacts to `../repocraft-reports/` (or a custom `--output` directory):

1. **`inventory.json`**: Machine-readable JSON summary of repository metadata, technologies, file inventory statistics, Git baseline, governance, and discovered commands.
2. **`repository-overview.md`**: Human-readable architecture and project overview detailing purpose, tech stack, main directories, entry points, and CI/CD strategy with source citations.
3. **`repository-audit.md`**: Structured audit report containing executive summary, Git worktree safety, governance matrix, hygiene observations, prioritized health findings, and limitations.
4. **`recommendations.json`**: Machine-readable findings with unique IDs (`FINDING-<DOMAIN>-###`), severity, confidence, evidence, explanations, suggested actions, approval flags, and target maintenance phase.

---

## 5. Execution Command

Run the bundled intelligence script from the installed skill:

```bash
python .agent/skills/repocraft/scripts/repocraft_intel.py --target . --output ../repocraft-reports
```

Flags:
- `--target <path>`: Project directory to inspect (default: `.`).
- `--output <path>`: Report output directory (default: `../repocraft-reports`).
- `--json`: Output brief JSON summary to stdout.

