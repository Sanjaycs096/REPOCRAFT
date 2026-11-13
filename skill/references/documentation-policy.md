# Documentation & Licensing Policy

This reference governs **Phase 2: README, Documentation, and Licensing Review**.

---

## 1. README Standards

Every generated or improved README must be:
1. **Evidence-Grounded**: All claims regarding technology stacks, entry points, configuration flags, and workflows must come directly from repository manifests and source code.
2. **Tailored to Project Type**: Adapts sections and commands to whether the project is a CLI tool, Python library, React/Next.js web app, Java service, or Monorepo.
3. **Zero Hallucination**:
   - Never invent features, metrics, benchmarks, user counts, or security certifications.
   - Never fabricate screenshots or demo URLs.
   - Never include fake badges or unverified build statuses.
   - Where information is unknown, use explicit `<!-- TODO: Maintainer ... -->` placeholders.
4. **Draft-First Operation**: Propose improvements via `README-improved.md`. Do not overwrite the original README unless explicitly authorized in `apply` mode.

---

## 2. Licensing Compliance & Strict Safeguards

Licensing is a legally consequential area governed by immutable safety rules:
1. **Never Select a License**: RepoCraft must never select or choose a license on behalf of the project maintainer.
2. **Never Overwrite an Existing License**: Existing `LICENSE`, `COPYING`, or license header text must never be replaced.
3. **Never Fabricate a License File**: If no license exists, RepoCraft generates a finding in the audit report explaining that the project owner must make the legal determination.
4. **Reconcile Inconsistencies**: Detect and report mismatches between manifest declarations (e.g. `package.json` `"license": "Apache-2.0"`) and file contents (e.g. `LICENSE` containing MIT text).

---

## 3. Governance Policies

Identify the presence and completeness of:
- `CONTRIBUTING.md`
- `CODE_OF_CONDUCT.md`
- `SECURITY.md`
- `CHANGELOG.md`
- Issue and Pull Request templates

Drafts for missing governance policies may be generated in reports for user review, but never silently inserted into the repository without authorization.

