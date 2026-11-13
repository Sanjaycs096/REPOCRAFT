# RepoCraft — Agent Compatibility Matrix & Validation Report

**Generated:** 2026-11-13T17:10:15.137756+00:00  
**RepoCraft Version:** `1.0.0-rc1`  
**Target Repository:** `C:\Users\sanja\project\RepoCraft`  
**Detected Workspace Agent:** **None (Unconfigured)** (0% confidence)  

---

## 1. Executive Summary

RepoCraft is a portable coding-agent skill engineered primarily for **Google Antigravity**. To prevent misleading users, other agent targets are classified transparently using calibrated support levels rather than assuming successful file copying implies full invocation compatibility.

## 2. Support Level Definitions

- `SUPPORTED`: Certified end-to-end (installation, discovery, parsing, CLI execution, approval gates, lifecycle).
- `PARTIALLY_SUPPORTED`: Verified for specific phases or workflows; known gaps exist.
- `INSTALLATION_ONLY`: File layout and manifest copy correctly, but agent-driven automated execution is uncertified.
- `MANUAL_CONFIGURATION_REQUIRED`: Requires project-specific adapter rule or manual CLI execution.
- `NOT_SUPPORTED`: Incompatible with the agent's extension mechanism.
- `NOT_TESTED`: No certified harness or testing performed.

## 3. Capability Matrix

| Agent | Support Level | Install | Discovery | CLI Exec | Full Lifecycle | Status |
| --- | --- | --- | --- | --- | --- | --- |
| Google Antigravity | `SUPPORTED` | ✅ Yes | ✅ Yes | ✅ Yes | ✅ Yes | CERTIFIED |
| Claude Code (Anthropic) | `INSTALLATION_ONLY` | ✅ Yes | ❌ No | ✅ Yes | ❌ No | INSTALLATION_VERIFIED_INVOCATION_UNVERIFIED |
| Cursor IDE | `MANUAL_CONFIGURATION_REQUIRED` | ❌ No | ❌ No | ✅ Yes | ❌ No | NOT_CERTIFIED |
| Gemini CLI | `NOT_TESTED` | ❌ No | ❌ No | ❌ No | ❌ No | UNTESTED |
| Project-Local Standalone (Generic) | `MANUAL_CONFIGURATION_REQUIRED` | ✅ Yes | ❌ No | ✅ Yes | ❌ No | VERIFIED_STANDALONE |

---

## 4. Agent Validation Details

### Google Antigravity (`antigravity`)
- **Support Level:** `SUPPORTED`
- **Installation Status:** ⚠️ Incomplete or Not Installed
- **Configured Directory:** `.agent/skills/repocraft`
- **Validation Status:** `CERTIFIED`

**Compatibility Evidence:**
- Standard .agent/skills/ directory layout verified by installer contract tests.
- YAML frontmatter in skill/SKILL.md conforms to Antigravity skill specification.
- Full lifecycle execution verified across Phase 0-5 test suites.

**Known Limitations:**
- Requires Python >=3.9 installed in the environment for executing runtime scripts.

**Validation Deficiencies:**
- ❌ Skill directory does not exist: C:\Users\sanja\project\RepoCraft\.agent\skills\repocraft

---

### Claude Code (Anthropic) (`claude-code`)
- **Support Level:** `INSTALLATION_ONLY`
- **Installation Status:** ⚠️ Incomplete or Not Installed
- **Configured Directory:** `.claude/skills/repocraft`
- **Validation Status:** `INSTALLATION_VERIFIED_INVOCATION_UNVERIFIED`

**Compatibility Evidence:**
- install.py provides configured target for .claude/skills/repocraft.
- File placement and file integrity verified by installer tests.
- Invocation protocol not tested in certified headless test harness.

**Known Limitations:**
- Claude Code automated skill discovery and headless invocation protocol are unverified.
- Requires manual user prompting and terminal execution verification.
- Autonomous multi-phase pipeline is not certified for headless invocation.

**Validation Deficiencies:**
- ❌ Skill directory does not exist: C:\Users\sanja\project\RepoCraft\.claude\skills\repocraft

---

### Cursor IDE (`cursor`)
- **Support Level:** `MANUAL_CONFIGURATION_REQUIRED`
- **Installation Status:** ⚠️ Incomplete or Not Installed
- **Configured Directory:** `.cursor/rules/repocraft.mdc`
- **Validation Status:** `NOT_CERTIFIED`

**Compatibility Evidence:**
- CLI scripts can be executed manually in Cursor built-in terminal.

**Known Limitations:**
- Cursor uses .cursorrules or .cursor/rules/*.mdc conventions rather than .agent/skills directory tree.
- Requires manual adapter file creation.

**Validation Deficiencies:**
- ❌ Skill directory does not exist: C:\Users\sanja\project\RepoCraft\.cursor\rules\repocraft.mdc

---

### Gemini CLI (`gemini-cli`)
- **Support Level:** `NOT_TESTED`
- **Installation Status:** ⚠️ Incomplete or Not Installed
- **Configured Directory:** `.gemini/skills/repocraft`
- **Validation Status:** `UNTESTED`

**Compatibility Evidence:**
- None recorded.

**Known Limitations:**
- No official skill discovery convention or test harness available.

**Validation Deficiencies:**
- ❌ Skill directory does not exist: C:\Users\sanja\project\RepoCraft\.gemini\skills\repocraft

---

### Project-Local Standalone (Generic) (`project`)
- **Support Level:** `MANUAL_CONFIGURATION_REQUIRED`
- **Installation Status:** ⚠️ Incomplete or Not Installed
- **Configured Directory:** `.repocraft/skill`
- **Validation Status:** `VERIFIED_STANDALONE`

**Compatibility Evidence:**
- install.py provides configured target for .repocraft/skill.
- Installer integrity verified by contract tests.

**Known Limitations:**
- Does not integrate with agent-specific skill discovery protocols; requires manual invocation.

**Validation Deficiencies:**
- ❌ Skill directory does not exist: C:\Users\sanja\project\RepoCraft\.repocraft\skill

---

## 5. Honest Compatibility Guarantees

RepoCraft adheres to the following release invariants:
1. **Never fabricate compatibility**: An agent is never marked `SUPPORTED` without end-to-end automated verification.
2. **Standard Library Only**: Runtime scripts rely strictly on the Python standard library to maximize portability across host environments.
3. **Zero Developer Path Leaks**: An installed RepoCraft copy operates independently of the original checkout repository.
