# RepoCraft — Agent Compatibility Policy & Discovery Specifications

## 1. Principles of Agent Compatibility

RepoCraft is a portable coding-agent skill engineered to maintain existing software repositories.

**Core Invariants:**
1. **Never fabricate compatibility**: A coding agent must never be marked `SUPPORTED` based solely on file placement or theoretical support. Full end-to-end automated verification is required.
2. **Calibrated Support Taxonomy**: Support levels must be transparent and calibrated:
   - `SUPPORTED`: Certified end-to-end (installation, automatic skill discovery, prompt interpretation, subprocess execution, interactive approval gates, full multi-phase lifecycle).
   - `PARTIALLY_SUPPORTED`: Certified for specific phases; known limitations documented.
   - `INSTALLATION_ONLY`: Files install correctly to the agent's directory, but automated invocation is unverified.
   - `MANUAL_CONFIGURATION_REQUIRED`: Project-specific adapter or manual terminal invocation needed.
   - `NOT_SUPPORTED`: Incompatible with the agent's extension mechanism.
   - `NOT_TESTED`: No certified harness or testing performed.
3. **Pure Python Standard Library**: Runtime scripts must not require external pip dependencies, preventing installation failures across agent environments.
4. **No Developer Path Leaks**: An installed RepoCraft copy operates strictly within the target project directory and does not reference development checkouts or developer-specific paths.

---

## 2. Agent Specifications

### 2.1 Google Antigravity (Primary Supported Target)
- **Support Level**: `SUPPORTED`
- **Installation Target**: `.agent/skills/repocraft/`
- **Skill Discovery Format**: `SKILL.md` with standard YAML frontmatter:
  ```markdown
  ---
  name: repocraft
  description: Inspect, organize, maintain, secure, test, repair, and responsibly publish improvements to an existing software repository.
  ---
  ```
- **Invocation**: Triggered natively by natural language prompt or slash command. Antigravity discovers the skill instructions and executes runtime scripts via its sandboxed terminal tools.
- **Approval Handling**: Fully supports interactive approval gates for repair manifests, staging, commits, and pushes.

### 2.2 Claude Code (Anthropic)
- **Support Level**: `INSTALLATION_ONLY`
- **Installation Target**: `.claude/skills/repocraft/`
- **Discovery Format**: Markdown instruction document.
- **Invocation**: User prompts Claude Code to read `.claude/skills/repocraft/SKILL.md` and execute scripts via terminal tool. Headless automated multi-phase execution is uncertified.

### 2.3 Cursor IDE
- **Support Level**: `MANUAL_CONFIGURATION_REQUIRED`
- **Installation Target**: `.cursor/rules/repocraft.mdc` or project `.cursorrules`
- **Invocation**: User creates an adapter rule pointing to RepoCraft CLI commands and executes them in the integrated terminal.

### 2.4 Project-Local Standalone (Generic)
- **Support Level**: `MANUAL_CONFIGURATION_REQUIRED`
- **Installation Target**: `.repocraft/skill/`
- **Invocation**: User or custom agent reads `.repocraft/skill/SKILL.md` and executes CLI entry points directly via Python.

---

## 3. Installation Verification

When verifying an installation:
1. Check that `SKILL.md` exists and contains required frontmatter or instructions.
2. Check that all reference policy documents exist in `references/` and are non-empty.
3. Check that all runtime CLI scripts exist in `scripts/`.
4. Check that `INSTALL-MANIFEST.json` is present and SHA-256 hashes match installed files.
5. Check that running `python skill/scripts/repocraft_status.py --verify-installation` outputs `READY` or `READY_WITH_LIMITATIONS`.

