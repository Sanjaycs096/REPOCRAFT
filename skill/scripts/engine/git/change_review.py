"""Module 3.6 — Change Review Generator for RepoCraft Phase 5.

Generates human-readable Markdown review (git-change-review.md) and
machine-readable JSON review (git-change-review.json).
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from .change_risk_analyzer import ChangeRiskAnalyzer
from .diff_analyzer import DiffAnalyzer
from .git_environment import GitEnvironment
from .git_types import ChangeFile, ChangeReview, ChangeRisk


class ChangeReviewGenerator:
    """Produces comprehensive change reviews from repository diffs and risk analysis."""

    def __init__(self, target_dir: str, env: Optional[GitEnvironment] = None):
        self.target_dir = Path(target_dir).resolve()
        self.env = env or GitEnvironment(str(self.target_dir))
        self.diff_analyzer = DiffAnalyzer(str(self.target_dir), self.env)
        self.risk_analyzer = ChangeRiskAnalyzer()

    def generate_review(self) -> ChangeReview:
        """Run diff analysis and risk classification, compiling a ChangeReview object."""
        state = self.env.inspect_state()
        raw_files = self.diff_analyzer.analyze_changes()
        evaluated_files, overall_risk = self.risk_analyzer.evaluate_all(raw_files)

        now_str = datetime.now(timezone.utc).isoformat()
        review_id = f"REV-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"

        critical_files = [f.file_path for f in evaluated_files if f.risk == ChangeRisk.CRITICAL]
        high_risk_files = [f.file_path for f in evaluated_files if f.risk == ChangeRisk.HIGH]
        sensitive_files = [f.file_path for f in evaluated_files if f.sensitive_patterns]
        binary_files = [f.file_path for f in evaluated_files if f.is_binary]
        untracked_files = [f.file_path for f in evaluated_files if f.untracked]

        recommendations: List[str] = []
        if critical_files:
            recommendations.append(f"BLOCK: {len(critical_files)} critical files detected. Automatic staging/committing strictly prohibited.")
        if high_risk_files:
            recommendations.append(f"REVIEW: {len(high_risk_files)} high-risk files require explicit per-file authorization.")
        if sensitive_files:
            recommendations.append(f"WARNING: Sensitive or secret patterns detected in {len(sensitive_files)} files. Remove secrets immediately.")
        if binary_files:
            recommendations.append(f"INFO: {len(binary_files)} binary files detected. Review individually.")
        if not recommendations:
            recommendations.append("All changes appear low-to-medium risk. Proceed with staging plan.")

        summary = (
            f"Repository change review evaluated {len(evaluated_files)} files. "
            f"Overall risk: {overall_risk.value}. "
            f"Critical: {len(critical_files)}, High: {len(high_risk_files)}, Medium/Low: {len(evaluated_files) - len(critical_files) - len(high_risk_files)}."
        )

        return ChangeReview(
            review_id=review_id,
            timestamp=now_str,
            repository_path=str(self.target_dir),
            branch=state.current_branch,
            head_commit=state.head_commit,
            files=evaluated_files,
            overall_risk=overall_risk,
            critical_files=critical_files,
            high_risk_files=high_risk_files,
            sensitive_files=sensitive_files,
            binary_files=binary_files,
            untracked_files=untracked_files,
            summary=summary,
            review_recommendations=recommendations,
        )

    def write_reports(self, review: ChangeReview, output_dir: Path) -> Dict[str, Path]:
        """Write git-change-review.md and git-change-review.json to output directory."""
        output_dir.mkdir(parents=True, exist_ok=True)
        md_path = output_dir / "git-change-review.md"
        json_path = output_dir / "git-change-review.json"

        # 1. JSON
        json_path.write_text(json.dumps(review.to_dict(), indent=2), encoding="utf-8")

        # 2. Markdown
        md_content = self._render_markdown(review)
        md_path.write_text(md_content, encoding="utf-8")

        return {"md": md_path, "json": json_path}

    def _render_markdown(self, review: ChangeReview) -> str:
        """Render human-readable Markdown change review."""
        lines = [
            f"# RepoCraft Git Change Review — `{review.review_id}`",
            "",
            f"- **Repository**: `{review.repository_path}`",
            f"- **Branch**: `{review.branch}`",
            f"- **HEAD Commit**: `{review.head_commit}`",
            f"- **Timestamp**: `{review.timestamp}`",
            f"- **Overall Risk**: **{review.overall_risk.value}**",
            "",
            "## Summary",
            review.summary,
            "",
        ]

        if review.review_recommendations:
            lines.append("## Recommendations")
            for rec in review.review_recommendations:
                lines.append(f"- {rec}")
            lines.append("")

        if review.critical_files:
            lines.append("## ⚠️ Critical Files (Staging Blocked)")
            for cf in review.critical_files:
                lines.append(f"- `{cf}`")
            lines.append("")

        lines.extend([
            "## Changed Files Overview",
            "",
            "| File Path | Change Type | Status | Risk | Lines (+/-) | Recommendation |",
            "| :--- | :--- | :--- | :--- | :--- | :--- |",
        ])

        for f in review.files:
            status = "Staged" if f.staged else ("Unstaged" if f.unstaged else "Untracked")
            lines.append(
                f"| `{f.file_path}` | {f.change_type.value} | {status} | **{f.risk.value}** | +{f.added_lines}/-{f.deleted_lines} | {f.recommendation} |"
            )

        lines.append("")
        lines.append("## Detailed File Findings")
        for f in review.files:
            lines.append(f"### `{f.file_path}`")
            lines.append(f"- **Change Type**: {f.change_type.value}")
            lines.append(f"- **Risk**: {f.risk.value}")
            lines.append(f"- **Approval Requirement**: `{f.approval_requirement}`")
            if f.risk_reasons:
                lines.append("- **Reasons**:")
                for r in f.risk_reasons:
                    lines.append(f"  - {r}")
            if f.sensitive_patterns:
                lines.append("- **Sensitive Patterns Detected**:")
                for sp in f.sensitive_patterns:
                    lines.append(f"  - ⚠️ {sp}")
            lines.append("")

        return "\n".join(lines)

