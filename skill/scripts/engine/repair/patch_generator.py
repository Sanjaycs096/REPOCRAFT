"""Patch generator for RepoCraft Phase 4 safe repair operations.

Generates deterministic ProposedPatch objects for:
1. Documentation link corrections
2. README command corrections
3. Safe configuration additions (e.g. .gitignore rules)
4. Exact text replacements
"""
from __future__ import annotations

import hashlib
from pathlib import Path
from typing import List, Optional

from .repair_types import ProposedPatch


def sha256_of_text(text: str) -> str:
    """Compute sha256 hash of a string."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_of_file(file_path: Path) -> Optional[str]:
    """Compute sha256 hash of a file if it exists."""
    if not file_path.is_file():
        return None
    try:
        content = file_path.read_text(encoding="utf-8", errors="replace")
        return sha256_of_text(content)
    except Exception:
        return None


class PatchGenerator:
    """Constructs verifiable patches for supported repair operations."""

    def __init__(self, target_dir: str):
        self.target_dir = Path(target_dir).resolve()

    def generate_doc_link_patch(
        self, file_rel_path: str, broken_link: str, corrected_link: str
    ) -> Optional[ProposedPatch]:
        """Generate a patch replacing a broken relative documentation link."""
        full_path = self.target_dir / file_rel_path
        if not full_path.is_file():
            return None

        content = full_path.read_text(encoding="utf-8", errors="replace")
        if broken_link not in content:
            return None

        new_content = content.replace(broken_link, corrected_link)
        return ProposedPatch(
            file_path=file_rel_path,
            diff_or_description=f"Update broken link '{broken_link}' to '{corrected_link}' in {file_rel_path}",
            patch_type="text_replace",
            target_text=broken_link,
            replacement_text=corrected_link,
            original_content_hash=sha256_of_text(content),
            new_content_hash=sha256_of_text(new_content),
        )

    def generate_readme_command_patch(
        self, readme_rel_path: str, incorrect_cmd: str, correct_cmd: str
    ) -> Optional[ProposedPatch]:
        """Generate a patch replacing an incorrect README command."""
        full_path = self.target_dir / readme_rel_path
        if not full_path.is_file():
            return None

        content = full_path.read_text(encoding="utf-8", errors="replace")
        if incorrect_cmd not in content:
            return None

        new_content = content.replace(incorrect_cmd, correct_cmd)
        return ProposedPatch(
            file_path=readme_rel_path,
            diff_or_description=f"Correct command '{incorrect_cmd}' to '{correct_cmd}' in {readme_rel_path}",
            patch_type="text_replace",
            target_text=incorrect_cmd,
            replacement_text=correct_cmd,
            original_content_hash=sha256_of_text(content),
            new_content_hash=sha256_of_text(new_content),
        )

    def generate_gitignore_rule_patch(self, rule_to_add: str) -> ProposedPatch:
        """Generate a patch adding a missing critical exclusion pattern to .gitignore."""
        gitignore_path = self.target_dir / ".gitignore"
        if gitignore_path.is_file():
            content = gitignore_path.read_text(encoding="utf-8", errors="replace")
            orig_hash = sha256_of_text(content)
            # Ensure newline at end
            prefix = "\n" if content and not content.endswith("\n") else ""
            new_content = f"{content}{prefix}{rule_to_add}\n"
            new_hash = sha256_of_text(new_content)
            return ProposedPatch(
                file_path=".gitignore",
                diff_or_description=f"Add '{rule_to_add}' to .gitignore",
                patch_type="text_replace",
                target_text="",
                replacement_text=rule_to_add,
                original_content_hash=orig_hash,
                new_content_hash=new_hash,
                full_content=new_content,
            )
        else:
            new_content = f"{rule_to_add}\n"
            return ProposedPatch(
                file_path=".gitignore",
                diff_or_description=f"Create .gitignore containing '{rule_to_add}'",
                patch_type="file_create",
                full_content=new_content,
                original_content_hash=None,
                new_content_hash=sha256_of_text(new_content),
            )

    def generate_exact_text_patch(
        self, file_rel_path: str, target_text: str, replacement_text: str
    ) -> Optional[ProposedPatch]:
        """Generate an exact text replacement patch."""
        full_path = self.target_dir / file_rel_path
        if not full_path.is_file():
            return None

        content = full_path.read_text(encoding="utf-8", errors="replace")
        if target_text not in content:
            return None

        new_content = content.replace(target_text, replacement_text)
        return ProposedPatch(
            file_path=file_rel_path,
            diff_or_description=f"Replace '{target_text[:30]}' with '{replacement_text[:30]}' in {file_rel_path}",
            patch_type="text_replace",
            target_text=target_text,
            replacement_text=replacement_text,
            original_content_hash=sha256_of_text(content),
            new_content_hash=sha256_of_text(new_content),
        )

