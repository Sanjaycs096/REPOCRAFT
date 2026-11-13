# Agent adapters

The canonical skill instructions live in `skill/SKILL.md`.

Phase 0 provides installer destinations for:
- Antigravity (`.agent/skills/repocraft/`) — initial target.
- Claude Code (`.claude/skills/repocraft/`) — destination configured; compatibility must be validated.
- Generic project-local fallback (`.repocraft/skill/`) — files are installed but require manual invocation.

Do not claim an adapter is fully supported until installation, skill discovery, invocation, and a representative workflow have been tested on that agent.
