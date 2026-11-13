# Codebase Maintenance & Organization Policy

This reference governs **Phase 2: Codebase Maintenance & Organization**.
All codebase reorganization, unused-file detection, and structural maintenance must adhere to strict evidence and user safety standards.

---

## 1. Core Principles

1. **Evidence-Based Moves Only**: No file or directory reorganization may be proposed based merely on aesthetics. Every recommendation requires concrete architectural justification.
2. **Framework Convention Preservation**: Next.js App/Pages Router conventions, Nuxt routes, Django structures, Maven standard directory layouts, and framework-mandated patterns must NEVER be altered or classified as misplaced.
3. **No Automatic Deletion**: Uncertain files, obsolete scripts, or unused asset candidates are **never automatically deleted** in Phase 2. They are classified with calibrated confidence levels (`CONFIRMED_UNUSED`, `LIKELY_UNUSED`, `POSSIBLY_UNUSED`, `UNKNOWN`) and presented in `maintenance-analysis.json` for user review.
4. **User Work Protection**: Files with pre-existing user modifications (staged, unstaged, or untracked) must never be moved, renamed, or modified.
5. **Recoverable Backups**: Any file modified in `apply` mode must be backed up (e.g. `filename.backup`) prior to write operations.

---

## 2. Unused-File Classification Standards

- `CONFIRMED_UNUSED`: Obsolete temporary or backup files (e.g., `*.bak`, `*.tmp`, `*~`, `.DS_Store`, `Thumbs.db`, `.swp`, duplicate identical files with 0 references).
- `LIKELY_UNUSED`: Source or asset files with 0 static or dynamic references across all code, manifests, and documentation, and not matching any entry point or framework convention.
- `POSSIBLY_UNUSED`: Files with 0 static references but residing in plugin, script, mock, or fixture directories where dynamic reflection or external invocation is plausible.
- `UNKNOWN`: Files where runtime reflection, dynamic imports, or configuration-based loading prevents static verification.

---

## 3. Execution Modes

- `audit` (Default): Read-only inspection. Evaluates structure and produces `maintenance-analysis.json` and `maintenance-plan.json`. Modifies 0 target project files.
- `draft`: Emits proposed changes and draft documentation to the external reports directory. Modifies 0 target project files.
- `apply`: Applies only policy-authorized, reviewed changes after verifying Git baseline and creating recoverable backups.

