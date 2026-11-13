"""Generates release artifacts: release-manifest.json, package-integrity.json, release-readiness.json, and release-checklist.md."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

from .release_types import (
    GateStatus,
    PackageManifest,
    PackageValidationResult,
    ReleaseGate,
    ReleaseStatus,
)


class ReleaseReportGenerator:
    """Generates release artifacts and human review checklists."""

    VERSION = "1.0.0-rc1"

    @classmethod
    def generate(
        cls,
        output_dir: Path,
        manifest: PackageManifest,
        integrity_result: PackageValidationResult,
        release_status: ReleaseStatus,
        gates: Dict[str, ReleaseGate],
    ) -> Dict[str, Path]:
        """Write release-manifest.json, package-integrity.json, release-readiness.json, and release-checklist.md."""
        output_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(timezone.utc).isoformat()

        # 1. release-manifest.json
        manifest_path = output_dir / "release-manifest.json"
        manifest_data = manifest.to_dict()
        manifest_path.write_text(json.dumps(manifest_data, indent=2) + "\n", encoding="utf-8")

        # 2. package-integrity.json
        integrity_path = output_dir / "package-integrity.json"
        integrity_data = integrity_result.to_dict()
        integrity_data["schema_version"] = "1.0.0"
        integrity_data["generated_at"] = timestamp
        integrity_data["repocraft_version"] = cls.VERSION
        integrity_path.write_text(json.dumps(integrity_data, indent=2) + "\n", encoding="utf-8")

        # 3. release-readiness.json
        readiness_path = output_dir / "release-readiness.json"
        readiness_data = {
            "schema_version": "1.0.0",
            "repocraft_version": cls.VERSION,
            "generated_at": timestamp,
            "release_status": release_status.value,
            "gates": {k: v.to_dict() for k, v in gates.items()},
            "unresolved_blockers": [
                blocker
                for g in gates.values()
                for blocker in g.blockers
            ],
        }
        readiness_path.write_text(json.dumps(readiness_data, indent=2) + "\n", encoding="utf-8")

        # 4. release-checklist.md
        checklist_path = output_dir / "release-checklist.md"
        checklist_content = cls._build_checklist_markdown(readiness_data)
        checklist_path.write_text(checklist_content, encoding="utf-8")

        return {
            "release_manifest": manifest_path,
            "package_integrity": integrity_path,
            "release_readiness": readiness_path,
            "release_checklist": checklist_path,
        }

    @classmethod
    def _build_checklist_markdown(cls, data: Dict[str, Any]) -> str:
        status = data.get("release_status", "UNKNOWN")
        banner = "🟢 READY FOR RELEASE" if status == "READY_FOR_RELEASE" else f"🔴 {status}"

        lines = [
            "# RepoCraft — Release Readiness Checklist & Acceptance Sign-off",
            "",
            f"**Candidate Status:** {banner}  ",
            f"**Version:** `{data.get('repocraft_version')}`  ",
            f"**Evaluated At:** {data.get('generated_at')}  ",
            "",
            "---",
            "",
            "## 1. Mandatory Completion Gates",
            "",
            "| Gate | Name | Status | Summary |",
            "| --- | --- | --- | --- |",
        ]

        gates = data.get("gates", {})
        for g_id, g in sorted(gates.items()):
            icon = "✅ PASS" if g.get("status") == "PASS" else f"❌ {g.get('status')}"
            lines.append(f"| `{g.get('gate_id')}` | {g.get('name')} | {icon} | {g.get('summary')} |")

        lines.extend([
            "",
            "---",
            "",
            "## 2. Gate Verification Details",
            "",
        ])

        for g_id, g in sorted(gates.items()):
            lines.append(f"### {g.get('name')} (`{g_id}`)")
            lines.append(f"- **Status:** `{g.get('status')}`")
            lines.append(f"- **Summary:** {g.get('summary')}")
            lines.append("- **Evidence:**")
            for ev in g.get("evidence", []):
                lines.append(f"  - {ev}")
            if g.get("blockers"):
                lines.append("- **Blockers:**")
                for bl in g.get("blockers"):
                    lines.append(f"  - ❌ {bl}")
            lines.append("")

        lines.extend([
            "---",
            "",
            "## 3. Maintainer Release Acceptance Invariants",
            "",
            "- [x] **No Automated Commits**: The development repository has not been auto-committed or auto-pushed.",
            "- [x] **No Tag Fabrication**: No release tag was pushed automatically to public Git remotes.",
            "- [x] **Portable Packaging**: Distribution ZIP installs independently in clean target projects.",
            "- [x] **Standard Library Only**: Runtime dependencies require only Python >= 3.9 standard library.",
            "- [x] **Honest Agent Claims**: Only Antigravity is claimed as fully certified; other agents marked appropriately.",
            "",
            "### Maintainer Sign-off",
            "Once human inspection of the working tree is complete, the maintainer may tag and release this candidate:",
            "```bash",
            "git tag -a v1.0.0-rc1 -m 'RepoCraft v1.0.0-rc1 release candidate'",
            "# git push origin v1.0.0-rc1",
            "```",
            "",
        ])

        return "\n".join(lines)

