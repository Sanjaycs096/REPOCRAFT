"""GitHub repository presentation and branding auditor for RepoCraft.

Evaluates repository identity, topics, descriptions, social preview images,
architecture diagrams, and badges. Strictly differentiates between local recommendations
and remote metadata actions, blocking unauthorized external modifications.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List, Optional


class PresentationRecommendation:
    def __init__(
        self,
        recommendation_type: str,  # LOCAL_RECOMMENDATION or REMOTE_METADATA_ACTION
        field: str,
        current_value: str | None,
        recommended_value: str,
        reason: str,
        requires_remote_authorization: bool = False,
    ):
        self.recommendation_type = recommendation_type
        self.field = field
        self.current_value = current_value
        self.recommended_value = recommended_value
        self.reason = reason
        self.requires_remote_authorization = requires_remote_authorization

    def to_dict(self) -> Dict[str, Any]:
        return {
            "recommendation_type": self.recommendation_type,
            "field": self.field,
            "current_value": self.current_value,
            "recommended_value": self.recommended_value,
            "reason": self.reason,
            "requires_remote_authorization": self.requires_remote_authorization,
        }


class GitHubPresentationResult:
    def __init__(
        self,
        repo_name: str,
        branding_score: int,  # 0 to 100
        has_logo: bool,
        has_social_preview: bool,
        recommended_topics: List[str],
        recommended_description: str,
        mermaid_architecture_diagram: str,
        badge_audit: List[Dict[str, Any]],
        recommendations: List[PresentationRecommendation],
        remote_actions_blocked: bool = True,
    ):
        self.repo_name = repo_name
        self.branding_score = branding_score
        self.has_logo = has_logo
        self.has_social_preview = has_social_preview
        self.recommended_topics = recommended_topics
        self.recommended_description = recommended_description
        self.mermaid_architecture_diagram = mermaid_architecture_diagram
        self.badge_audit = badge_audit
        self.recommendations = recommendations
        self.remote_actions_blocked = remote_actions_blocked

    def to_dict(self) -> Dict[str, Any]:
        return {
            "repo_name": self.repo_name,
            "branding_score": self.branding_score,
            "has_logo": self.has_logo,
            "has_social_preview": self.has_social_preview,
            "recommended_topics": self.recommended_topics,
            "recommended_description": self.recommended_description,
            "mermaid_architecture_diagram": self.mermaid_architecture_diagram,
            "badge_audit": self.badge_audit,
            "recommendations": [r.to_dict() for r in self.recommendations],
            "remote_actions_blocked": self.remote_actions_blocked,
        }


class GitHubPresentationAuditor:
    """Evaluates repository branding, GitHub About metadata, and visual presentation."""

    def __init__(
        self,
        repo_root: Path,
        file_paths: List[str],
        languages: List[str],
        frameworks: List[str],
        detected_types: List[str],
        existing_readme: str = "",
    ):
        self.repo_root = repo_root
        self.file_paths = file_paths
        self.languages = languages
        self.frameworks = frameworks
        self.detected_types = detected_types
        self.existing_readme = existing_readme

    def audit(self) -> GitHubPresentationResult:
        repo_name = self.repo_root.name
        recommendations: List[PresentationRecommendation] = []

        # 1. Check for Logo
        has_logo = any(
            re.search(r"logo\.(png|svg|jpg|webp)", p, re.IGNORECASE) for p in self.file_paths
        )
        if not has_logo:
            recommendations.append(
                PresentationRecommendation(
                    recommendation_type="LOCAL_RECOMMENDATION",
                    field="project_logo",
                    current_value=None,
                    recommended_value="assets/logo.svg or assets/logo.png",
                    reason="Adding a project logo elevates open-source presentation and visual identity in the README.",
                )
            )

        # 2. Check for Social Preview Image
        has_social_preview = any(
            re.search(r"(social-preview|opengraph|og-image)\.(png|jpg|webp)", p, re.IGNORECASE)
            for p in self.file_paths
        )
        if not has_social_preview:
            recommendations.append(
                PresentationRecommendation(
                    recommendation_type="LOCAL_RECOMMENDATION",
                    field="social_preview_image",
                    current_value=None,
                    recommended_value="assets/social-preview.png (1280x640 resolution)",
                    reason="A GitHub OpenGraph social preview image improves link previews when shared on social channels.",
                )
            )

        # 3. Recommend GitHub Topics
        topics: List[str] = []
        for lang in self.languages:
            topics.append(lang.lower().replace("+", "p").replace("#", "sharp"))
        for fw in self.frameworks:
            topics.append(fw.lower().replace(".", "").replace(" ", "-"))
        for dt in self.detected_types:
            if "Web" in dt:
                topics.append("web")
            if "API" in dt:
                topics.append("api")
            if "Monorepo" in dt:
                topics.append("monorepo")
            if "CLI" in dt:
                topics.append("cli")

        cleaned_topics = sorted(list(set(re.sub(r"[^a-z0-9-]", "", t) for t in topics if t)))[:10]

        recommendations.append(
            PresentationRecommendation(
                recommendation_type="REMOTE_METADATA_ACTION",
                field="github_topics",
                current_value=None,
                recommended_value=", ".join(cleaned_topics),
                reason="GitHub repository topics improve discoverability across the ecosystem.",
                requires_remote_authorization=True,
            )
        )

        # 4. Recommend Repository Description
        primary_type = self.detected_types[0] if self.detected_types else "software project"
        fw_str = f" using {', '.join(self.frameworks[:3])}" if self.frameworks else ""
        rec_desc = f"A portable, high-performance {primary_type.lower()}{fw_str}."

        recommendations.append(
            PresentationRecommendation(
                recommendation_type="REMOTE_METADATA_ACTION",
                field="repository_description",
                current_value=None,
                recommended_value=rec_desc,
                reason="Concise repository description for GitHub About sidebar.",
                requires_remote_authorization=True,
            )
        )

        # 5. Badges Audit
        badge_audit = []
        if self.existing_readme:
            badge_matches = re.findall(r"\[!\[([^\]]*)\]\(([^)]+)\)\]\(([^)]+)\)", self.existing_readme)
            for alt, img_url, link_url in badge_matches:
                is_fake = "example.com" in link_url or "TODO" in link_url or "100%" in alt
                badge_audit.append({
                    "badge_name": alt or "badge",
                    "image_url": img_url,
                    "target_link": link_url,
                    "verified": not is_fake,
                    "warning": "Unverified or placeholder badge detected in README." if is_fake else None,
                })

        # 6. Mermaid Architecture Diagram
        diagram = self._generate_mermaid_diagram()
        recommendations.append(
            PresentationRecommendation(
                recommendation_type="LOCAL_RECOMMENDATION",
                field="architecture_diagram",
                current_value=None,
                recommended_value=diagram,
                reason="Mermaid architecture diagram visually clarifies system components in README.",
            )
        )

        # Branding Score calculation (0 to 100)
        score = 50
        if has_logo:
            score += 15
        if has_social_preview:
            score += 15
        if self.existing_readme and len(self.existing_readme.split()) > 100:
            score += 20

        return GitHubPresentationResult(
            repo_name=repo_name,
            branding_score=min(100, score),
            has_logo=has_logo,
            has_social_preview=has_social_preview,
            recommended_topics=cleaned_topics,
            recommended_description=rec_desc,
            mermaid_architecture_diagram=diagram,
            badge_audit=badge_audit,
            recommendations=recommendations,
            remote_actions_blocked=True,  # Phase 2 safety policy
        )

    def _generate_mermaid_diagram(self) -> str:
        lines = [
            "```mermaid",
            "flowchart TD",
            f"    User([Client / User]) --> App[{self.repo_root.name}]",
        ]
        if self.frameworks:
            lines.append(f"    App --> Engine['Framework: {self.frameworks[0]}']")
        lines.append("    App --> Storage[('Storage / Assets')]")
        lines.append("```")
        return "\n".join(lines)

