"""README and documentation intelligence analyzer for RepoCraft.

Evaluates completeness, readability, section coverage, formatting quality,
and placeholders in repository README files against 18 standard dimensions.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple


class ReadmeSectionResult:
    def __init__(self, section_name: str, present: bool, quality_score: int, details: str):
        self.section_name = section_name
        self.present = present
        self.quality_score = quality_score  # 0 to 10
        self.details = details

    def to_dict(self) -> Dict[str, Any]:
        return {
            "section_name": self.section_name,
            "present": self.present,
            "quality_score": self.quality_score,
            "details": self.details,
        }


class ReadmeAuditResult:
    def __init__(
        self,
        readme_path: str | None,
        exists: bool,
        word_count: int,
        overall_score: int,  # 0 to 100
        sections: Dict[str, ReadmeSectionResult],
        placeholders_detected: List[str],
        broken_badges: List[str],
        recommendations: List[str],
    ):
        self.readme_path = readme_path
        self.exists = exists
        self.word_count = word_count
        self.overall_score = overall_score
        self.sections = sections
        self.placeholders_detected = placeholders_detected
        self.broken_badges = broken_badges
        self.recommendations = recommendations

    def to_dict(self) -> Dict[str, Any]:
        return {
            "readme_path": self.readme_path,
            "exists": self.exists,
            "word_count": self.word_count,
            "overall_score": self.overall_score,
            "sections": {k: v.to_dict() for k, v in self.sections.items()},
            "placeholders_detected": self.placeholders_detected,
            "broken_badges": self.broken_badges,
            "recommendations": self.recommendations,
        }


class ReadmeAnalyzer:
    """Analyzes README files across 18 standard documentation criteria."""

    SECTIONS_TO_CHECK = [
        ("title", [r"^#\s+"]),
        ("short_description", [r"^#\s+.*\n\n\s*([^#\n]+)"]),
        ("problem_statement", [r"(problem|why|motivation|background)"]),
        ("features", [r"(features|key features|highlights|capabilities)"]),
        ("architecture", [r"(architecture|design|how it works|flowchart|structure)"]),
        ("tech_stack", [r"(tech\s*stack|built with|technologies|dependencies)"]),
        ("prerequisites", [r"(prerequisites|requirements|dependencies)"]),
        ("installation", [r"(installation|install|getting started|setup)"]),
        ("env_config", [r"(environment|configuration|env|\.env|options)"]),
        ("usage", [r"(usage|how to use|quick\s*start|example|api)"]),
        ("screenshots", [r"!\[.*\]\(.*(png|jpg|jpeg|gif|svg|webp).*\)"]),
        ("demo_links", [r"(demo|live|preview|http[s]?://)"]),
        ("testing", [r"(testing|tests|run tests|pytest|jest)"]),
        ("deployment", [r"(deployment|deploy|production|docker|release)"]),
        ("security_notes", [r"(security|vulnerability|reporting vulnerabilities)"]),
        ("contributing", [r"(contributing|contribute|development)"]),
        ("license", [r"(license|licence|copyright)"]),
        ("contact_author", [r"(contact|author|support|maintainers|community)"]),
    ]

    def __init__(self, repo_root: Path, readme_path: Path | None = None):
        self.repo_root = repo_root
        if readme_path and readme_path.is_file():
            self.readme_path = readme_path
        else:
            # Discover README in repo root
            candidates = ["README.md", "README.rst", "README.txt", "readme.md", "README"]
            found = None
            for c in candidates:
                cand_path = repo_root / c
                if cand_path.is_file():
                    found = cand_path
                    break
            self.readme_path = found

    def analyze(self) -> ReadmeAuditResult:
        if not self.readme_path or not self.readme_path.is_file():
            return ReadmeAuditResult(
                readme_path=None,
                exists=False,
                word_count=0,
                overall_score=0,
                sections={},
                placeholders_detected=[],
                broken_badges=[],
                recommendations=["Create an evidence-grounded README.md document in the repository root."],
            )

        content = self.readme_path.read_text(encoding="utf-8", errors="replace")
        words = len(content.split())
        rel_path = self.readme_path.relative_to(self.repo_root).as_posix()

        # Check sections
        section_results: Dict[str, ReadmeSectionResult] = {}
        earned_points = 0
        max_points = len(self.SECTIONS_TO_CHECK) * 10

        content_lower = content.lower()
        headings = [h.strip().lower() for h in re.findall(r"^#+\s+(.+)$", content, re.MULTILINE)]

        for sec_name, patterns in self.SECTIONS_TO_CHECK:
            present = False
            details = "Not found"
            score = 0

            # Special check for title: does it have a top-level # heading?
            if sec_name == "title":
                title_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
                if title_match:
                    present = True
                    score = 10
                    details = f"Title present: '{title_match.group(1).strip()}'"
            elif sec_name == "screenshots":
                if re.search(patterns[0], content, re.IGNORECASE):
                    present = True
                    score = 10
                    details = "Screenshot or media image embedded."
                else:
                    details = "No visual screenshots or media embedded."
            else:
                # Check headings or patterns
                for pat in patterns:
                    if any(re.search(pat, h) for h in headings):
                        present = True
                        score = 10
                        details = f"Dedicated section '{sec_name}' found in markdown headings."
                        break
                    elif re.search(pat, content_lower):
                        present = True
                        score = 5
                        details = f"Keyword matching '{sec_name}' found in text, but lacks dedicated section heading."
                        break

            section_results[sec_name] = ReadmeSectionResult(
                section_name=sec_name,
                present=present,
                quality_score=score,
                details=details,
            )
            earned_points += score

        # Check for placeholders
        placeholder_patterns = [
            r"TODO", r"TBD", r"FIXME", r"YOUR_API_KEY", r"Your Project Name",
            r"lorem ipsum", r"fill this in", r"under construction", r"REPLACE_WITH_",
        ]
        placeholders_found = []
        for pat in placeholder_patterns:
            if re.search(rf"\b{pat}\b", content, re.IGNORECASE):
                placeholders_found.append(pat)

        # Check badges
        broken_badges = []
        badge_matches = re.findall(r"\[!\[([^\]]*)\]\(([^)]+)\)\]\(([^)]+)\)", content)
        for alt, img, link in badge_matches:
            if "example.com" in link or "your-repo" in link or "TODO" in link:
                broken_badges.append(alt or img)

        # Calculate overall score (0 to 100)
        overall_score = min(100, int((earned_points / max_points) * 100))
        if placeholders_found:
            overall_score = max(0, overall_score - (len(placeholders_found) * 5))

        recommendations = []
        if not section_results.get("installation", ReadmeSectionResult("", False, 0, "")).present:
            recommendations.append("Add clear installation and setup instructions.")
        if not section_results.get("usage", ReadmeSectionResult("", False, 0, "")).present:
            recommendations.append("Provide concrete code or CLI usage examples.")
        if not section_results.get("testing", ReadmeSectionResult("", False, 0, "")).present:
            recommendations.append("Document test execution commands.")
        if not section_results.get("license", ReadmeSectionResult("", False, 0, "")).present:
            recommendations.append("Add explicit licensing and copyright reference.")
        if placeholders_found:
            recommendations.append(f"Remove or replace unfinished placeholders: {', '.join(placeholders_found)}.")

        return ReadmeAuditResult(
            readme_path=rel_path,
            exists=True,
            word_count=words,
            overall_score=overall_score,
            sections=section_results,
            placeholders_detected=placeholders_found,
            broken_badges=broken_badges,
            recommendations=recommendations,
        )

