"""Intelligent file inventory module for RepoCraft.

Traverses repository files safely, categorizes files, respects exclusion boundaries,
and treats sensitive filenames with strict confidentiality (metadata only, NO content inspection).
"""
from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Dict, List, Set, Tuple

from .types import FileCategory, FileInventoryItem

# Standard directory exclusion list
EXCLUDED_DIRECTORIES: Set[str] = {
    ".git",
    "node_modules",
    ".next",
    ".nuxt",
    ".svelte-kit",
    "dist",
    "build",
    "out",
    "coverage",
    ".nyc_output",
    ".venv",
    "venv",
    "env",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".gradle",
    "target",  # Maven/Rust target (often generated)
    "vendor",
    "bower_components",
    "Pods",
    ".turbo",
    ".parcel-cache",
    ".cache",
    ".tox",
    ".idea",
    ".vscode",
    ".agent",  # Keep skill isolated
    ".claude",
    ".repocraft",
}

# Patterns for sensitive / secret files
SENSITIVE_PATTERNS = [
    re.compile(r"^\.env(\..+)?$", re.IGNORECASE),
    re.compile(r"^.*id_(rsa|dsa|ecdsa|ed25519)(\.pub)?$", re.IGNORECASE),
    re.compile(r"^.*\.(pem|key|pkcs12|pfx|p12|kdbx)$", re.IGNORECASE),
    re.compile(r"^.*(credentials|client_secret|service-account.*)\.json$", re.IGNORECASE),
    re.compile(r"^.*\.(htpasswd|netrc)$", re.IGNORECASE),
    re.compile(r"^.*token.*\.txt$", re.IGNORECASE),
]

# Classification mapping by extension and filename
EXT_TO_CATEGORY: Dict[str, Tuple[FileCategory, str]] = {
    # Source - JS/TS
    ".js": (FileCategory.SOURCE, "javascript-source"),
    ".mjs": (FileCategory.SOURCE, "javascript-esm-source"),
    ".cjs": (FileCategory.SOURCE, "javascript-cjs-source"),
    ".jsx": (FileCategory.SOURCE, "react-jsx-source"),
    ".ts": (FileCategory.SOURCE, "typescript-source"),
    ".tsx": (FileCategory.SOURCE, "react-tsx-source"),
    ".vue": (FileCategory.SOURCE, "vue-source"),
    ".svelte": (FileCategory.SOURCE, "svelte-source"),
    # Source - Python
    ".py": (FileCategory.SOURCE, "python-source"),
    ".pyi": (FileCategory.SOURCE, "python-interface"),
    # Source - Systems / Compiled
    ".c": (FileCategory.SOURCE, "c-source"),
    ".h": (FileCategory.SOURCE, "c-header"),
    ".cpp": (FileCategory.SOURCE, "cpp-source"),
    ".cc": (FileCategory.SOURCE, "cpp-source"),
    ".cxx": (FileCategory.SOURCE, "cpp-source"),
    ".hpp": (FileCategory.SOURCE, "cpp-header"),
    ".hxx": (FileCategory.SOURCE, "cpp-header"),
    ".rs": (FileCategory.SOURCE, "rust-source"),
    ".go": (FileCategory.SOURCE, "go-source"),
    ".java": (FileCategory.SOURCE, "java-source"),
    ".kt": (FileCategory.SOURCE, "kotlin-source"),
    ".kts": (FileCategory.SOURCE, "kotlin-script"),
    ".scala": (FileCategory.SOURCE, "scala-source"),
    ".cs": (FileCategory.SOURCE, "csharp-source"),
    ".fs": (FileCategory.SOURCE, "fsharp-source"),
    ".swift": (FileCategory.SOURCE, "swift-source"),
    ".dart": (FileCategory.SOURCE, "dart-source"),
    ".php": (FileCategory.SOURCE, "php-source"),
    ".rb": (FileCategory.SOURCE, "ruby-source"),
    # Web & Style Assets
    ".html": (FileCategory.ASSETS, "html-document"),
    ".htm": (FileCategory.ASSETS, "html-document"),
    ".css": (FileCategory.ASSETS, "css-stylesheet"),
    ".scss": (FileCategory.ASSETS, "scss-stylesheet"),
    ".sass": (FileCategory.ASSETS, "sass-stylesheet"),
    ".less": (FileCategory.ASSETS, "less-stylesheet"),
    # Images & Media Assets
    ".png": (FileCategory.ASSETS, "png-image"),
    ".jpg": (FileCategory.ASSETS, "jpeg-image"),
    ".jpeg": (FileCategory.ASSETS, "jpeg-image"),
    ".gif": (FileCategory.ASSETS, "gif-image"),
    ".svg": (FileCategory.ASSETS, "svg-vector"),
    ".webp": (FileCategory.ASSETS, "webp-image"),
    ".ico": (FileCategory.ASSETS, "icon-asset"),
    ".pdf": (FileCategory.ASSETS, "pdf-document"),
    ".mp4": (FileCategory.ASSETS, "video-asset"),
    # Documentation
    ".md": (FileCategory.DOCUMENTATION, "markdown-documentation"),
    ".markdown": (FileCategory.DOCUMENTATION, "markdown-documentation"),
    ".rst": (FileCategory.DOCUMENTATION, "restructuredtext-documentation"),
    ".adoc": (FileCategory.DOCUMENTATION, "asciidoc-documentation"),
    ".txt": (FileCategory.DOCUMENTATION, "text-documentation"),
    # Configuration / Structured Data
    ".json": (FileCategory.CONFIGURATION, "json-configuration"),
    ".yaml": (FileCategory.CONFIGURATION, "yaml-configuration"),
    ".yml": (FileCategory.CONFIGURATION, "yaml-configuration"),
    ".toml": (FileCategory.CONFIGURATION, "toml-configuration"),
    ".ini": (FileCategory.CONFIGURATION, "ini-configuration"),
    ".xml": (FileCategory.CONFIGURATION, "xml-configuration"),
    ".proto": (FileCategory.CONFIGURATION, "protobuf-definition"),
    ".graphql": (FileCategory.SOURCE, "graphql-schema"),
    ".gql": (FileCategory.SOURCE, "graphql-schema"),
    ".sql": (FileCategory.SOURCE, "sql-script"),
    # Shell & Scripts
    ".sh": (FileCategory.SOURCE, "shell-script"),
    ".bash": (FileCategory.SOURCE, "shell-script"),
    ".zsh": (FileCategory.SOURCE, "shell-script"),
    ".ps1": (FileCategory.SOURCE, "powershell-script"),
    ".bat": (FileCategory.SOURCE, "batch-script"),
    ".cmd": (FileCategory.SOURCE, "batch-script"),
    # Data
    ".csv": (FileCategory.DATA, "csv-data"),
    ".tsv": (FileCategory.DATA, "tsv-data"),
    ".sqlite": (FileCategory.DATA, "sqlite-database"),
    ".db": (FileCategory.DATA, "database-file"),
}


def is_sensitive_filename(name: str) -> bool:
    """Check if filename matches sensitive credential or private key patterns."""
    for pattern in SENSITIVE_PATTERNS:
        if pattern.match(name):
            return True
    return False


def is_test_file(relative_path_posix: str) -> bool:
    """Determine if a file is designated for testing based on path and name."""
    parts = relative_path_posix.lower().split("/")
    filename = parts[-1]

    # Check directory cues
    test_dirs = {"test", "tests", "__tests__", "spec", "specs", "testing", "e2e", "cypress"}
    if any(p in test_dirs for p in parts[:-1]):
        return True

    # Check filename patterns
    test_patterns = [
        re.compile(r"^test_.*\.py$"),
        re.compile(r"^.*_test\.py$"),
        re.compile(r"^.*\.(test|spec)\.(js|jsx|ts|tsx)$"),
        re.compile(r"^Test.*\.java$"),
        re.compile(r"^.*Test\.java$"),
        re.compile(r"^.*Tests\.cs$"),
        re.compile(r"^.*_test\.go$"),
        re.compile(r"^test_.*\.rb$"),
    ]
    for pat in test_patterns:
        if pat.match(filename):
            return True
    return False


def classify_file(relative_path: Path, size_bytes: int) -> FileInventoryItem:
    """Classify a single file into category, classification, and sensitivity."""
    posix_path = relative_path.as_posix()
    name = relative_path.name
    ext = relative_path.suffix.lower()

    # 1. Check for sensitive files FIRST
    if is_sensitive_filename(name):
        return FileInventoryItem(
            relative_path=posix_path,
            extension=ext,
            category=FileCategory.CONFIGURATION,
            size_bytes=size_bytes,
            classification="sensitive-environment-or-key",
            is_sensitive=True,
            warning="Sensitive filename detected. Content strictly uninspected for security.",
        )

    # 2. Check for testing files
    if is_test_file(posix_path):
        return FileInventoryItem(
            relative_path=posix_path,
            extension=ext,
            category=FileCategory.TESTING,
            size_bytes=size_bytes,
            classification="automated-test-suite",
            is_sensitive=False,
        )

    # 3. Check specific known filenames
    known_filenames = {
        "dockerfile": (FileCategory.CONFIGURATION, "docker-container-definition"),
        "docker-compose.yml": (FileCategory.CONFIGURATION, "docker-compose-manifest"),
        "docker-compose.yaml": (FileCategory.CONFIGURATION, "docker-compose-manifest"),
        "makefile": (FileCategory.CONFIGURATION, "make-build-script"),
        "cmakelists.txt": (FileCategory.CONFIGURATION, "cmake-build-script"),
        "vagrantfile": (FileCategory.CONFIGURATION, "vagrant-definition"),
        "procfile": (FileCategory.CONFIGURATION, "process-definition"),
        ".gitignore": (FileCategory.CONFIGURATION, "git-ignore-rules"),
        ".gitattributes": (FileCategory.CONFIGURATION, "git-attributes"),
        ".editorconfig": (FileCategory.CONFIGURATION, "editor-configuration"),
        "license": (FileCategory.DOCUMENTATION, "project-license"),
        "license.md": (FileCategory.DOCUMENTATION, "project-license"),
        "licence": (FileCategory.DOCUMENTATION, "project-license"),
        "copying": (FileCategory.DOCUMENTATION, "project-license"),
        "readme": (FileCategory.DOCUMENTATION, "project-readme"),
        "readme.md": (FileCategory.DOCUMENTATION, "project-readme"),
        "contributing.md": (FileCategory.DOCUMENTATION, "contributing-guide"),
        "code_of_conduct.md": (FileCategory.DOCUMENTATION, "code-of-conduct"),
        "security.md": (FileCategory.DOCUMENTATION, "security-policy"),
        "changelog.md": (FileCategory.DOCUMENTATION, "changelog"),
    }
    if name.lower() in known_filenames:
        cat, cls = known_filenames[name.lower()]
        return FileInventoryItem(
            relative_path=posix_path,
            extension=ext,
            category=cat,
            size_bytes=size_bytes,
            classification=cls,
            is_sensitive=False,
        )

    # 4. Check extension mapping
    if ext in EXT_TO_CATEGORY:
        cat, cls = EXT_TO_CATEGORY[ext]
        return FileInventoryItem(
            relative_path=posix_path,
            extension=ext,
            category=cat,
            size_bytes=size_bytes,
            classification=cls,
            is_sensitive=False,
        )

    # 5. Fallback unknown
    return FileInventoryItem(
        relative_path=posix_path,
        extension=ext,
        category=FileCategory.UNKNOWN,
        size_bytes=size_bytes,
        classification="unclassified-file",
        is_sensitive=False,
    )


def build_inventory(repo_root: Path) -> Tuple[List[FileInventoryItem], Dict[str, int], List[str]]:
    """Traverse repository safely and construct file inventory.

    Returns:
        (inventory_items, category_counts, excluded_directories_found)
    """
    items: List[FileInventoryItem] = []
    category_counts: Dict[str, int] = {cat.value: 0 for cat in FileCategory}
    excluded_found: Set[str] = set()

    visited_real_paths: Set[str] = set()

    for root_str, dirs, files in os.walk(str(repo_root), followlinks=False):
        current_dir = Path(root_str)

        # Symlink loop defense for directories
        try:
            real_path = os.path.realpath(root_str)
            if real_path in visited_real_paths:
                dirs.clear()
                continue
            visited_real_paths.add(real_path)
        except Exception:
            pass

        # Identify excluded subdirectories and prune them from os.walk
        pruned = []
        for d in list(dirs):
            if d in EXCLUDED_DIRECTORIES:
                excluded_found.add(d)
                pruned.append(d)
                dirs.remove(d)

        for f in files:
            file_path = current_dir / f
            try:
                # Handle symlinks safely: if broken or inaccessible, record gracefully
                if file_path.is_symlink():
                    try:
                        stat_res = file_path.stat()
                        size = stat_res.st_size
                    except (OSError, ValueError):
                        size = 0
                else:
                    size = file_path.stat().st_size

                rel_path = file_path.relative_to(repo_root)
                item = classify_file(rel_path, size)
                items.append(item)
                category_counts[item.category.value] += 1
            except (PermissionError, FileNotFoundError, OSError):
                # Gracefully record inaccessible file without breaking inventory
                try:
                    rel_path = file_path.relative_to(repo_root)
                    items.append(
                        FileInventoryItem(
                            relative_path=rel_path.as_posix(),
                            extension=file_path.suffix.lower(),
                            category=FileCategory.UNKNOWN,
                            size_bytes=0,
                            classification="inaccessible-file",
                            warning="File metadata could not be fully read due to permission or system error.",
                        )
                    )
                    category_counts[FileCategory.UNKNOWN.value] += 1
                except Exception:
                    pass

    # Sort items deterministically by relative path
    items.sort(key=lambda x: x.relative_path)

    return items, category_counts, sorted(list(excluded_found))

