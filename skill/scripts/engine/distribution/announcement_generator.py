"""Generates public release announcements and onboarding highlights."""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from .distribution_types import ReleaseNotes


class AnnouncementGenerator:
    """Generates release-announcement-draft.md for maintainer review."""

    @classmethod
    def generate_announcement(
        cls,
        notes: ReleaseNotes,
        archive_sha256: str = "",
        archive_name: str = "repocraft-1.0.0-rc1.zip",
    ) -> str:
        """Render public announcement draft."""
        lines = [
            f"# 🚀 Announcing RepoCraft {notes.version} (Release Candidate)",
            "",
            "We are excited to announce the release candidate for **RepoCraft**, a portable, "
            "reusable agentic repository-maintenance skill package for coding agents.",
            "",
            "RepoCraft is not an application generator, web dashboard, or monolithic rewriting tool. "
            "Instead, it is installed into your existing project repository, invoked from your coding agent, "
            "and safely maintains codebase structure, documentation, security posture, tests, and Git publishing "
            "under strict, evidence-backed safety policies and human-in-the-loop approval gates.",
            "",
            "---",
            "",
            "## 🌟 What's in this Release Candidate?",
            "",
        ]

        for hl in notes.highlights:
            lines.append(f"- **{hl}**")

        lines.extend([
            "",
            "## 🛡️ Core Safety Guarantees",
            "",
            "RepoCraft is built from the ground up for safe execution in real-world repositories:",
            "1. **Zero Silent Overwrites**: User modifications and existing skill files are strictly protected.",
            "2. **Independent Approval Boundaries**: Staging approval, commit approval, and remote publishing require separate, explicit human authorization.",
            "3. **Zero Third-Party Runtime Dependencies**: Runs entirely on the Python standard library (Python >= 3.9).",
            "4. **No Secret Leaks**: Automated high-entropy token and URL credential redaction across all reports and reviews.",
            "5. **Bounded Repairs**: Strict 3-attempt root cause limits and automatic rollback protecting subsequent user modifications.",
            "6. **Gate E Development Repository Isolation**: The RepoCraft development repository is never automatically committed, pushed, or tagged.",
            "",
            "## 📦 Distribution & Quick Start",
            "",
            "### 1. Download & Verify Integrity",
            f"Distribution Archive: `{archive_name}`  ",
        ])

        if archive_sha256:
            lines.append(f"SHA-256 Checksum: `{archive_sha256}`  \n")
            lines.append("Verify before installing:")
            lines.append("```bash")
            lines.append(f"echo \"{archive_sha256}  {archive_name}\" | sha256sum --check")
            lines.append("```\n")

        lines.extend([
            "### 2. Install into Your Target Project",
            "```bash",
            "# Local installer (standard)",
            "python install.py --source /path/to/RepoCraft --target /path/to/your-project",
            "```",
            "",
            "### 3. Open in Your Coding Agent and Invoke",
            "Open your project in **Google Antigravity** (certified primary agent) and prompt:",
            "",
            "> *Run RepoCraft on this repository. Inspect the complete project, establish its Git and quality baseline, identify improvements, then safely maintain the codebase, documentation, GitHub presentation, security posture, tests, and CI/CD. Repair verified issues within policy, rerun relevant checks, review the complete diff, and publish only if every publishing condition is satisfied. Preserve my existing work. Produce a terminal summary and a detailed Markdown report.*",
            "",
            "### 4. Verify Installation Health",
            "```bash",
            "python skill/scripts/repocraft_status.py --verify-installation",
            "```",
            "",
            "---",
            "",
            "## 📋 Community & Feedback",
            "",
            "- **Maintainer Review Status**: Release Candidate (Draft)",
            "- **Documentation**: See `docs/PRODUCT-ARCHITECTURE.md` and `README.md`",
            "- **Security Policy**: See `docs/SECURITY.md`",
            "",
            "*Notice: This announcement is a draft generated during Phase 7 distribution preparation. "
            "Official publication will occur only when approved and tagged by the repository maintainer.*",
            "",
        ])

        return "\n".join(lines)
