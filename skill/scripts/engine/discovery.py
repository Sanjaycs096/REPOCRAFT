"""Repository technology discovery engine for RepoCraft.

Identifies ecosystems, frameworks, dependencies, entry points, configuration files,
manifests, and monorepo structures using direct file and manifest evidence.
Handles malformed manifests gracefully.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from .types import FileInventoryItem


def safe_read_text(path: Path, max_chars: int = 50000) -> str:
    """Read file text safely with encoding fallbacks and size limits."""
    try:
        with path.open("r", encoding="utf-8", errors="replace") as f:
            return f.read(max_chars)
    except Exception:
        return ""


def parse_json_manifest(path: Path) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """Parse JSON manifest, returning (dict, None) or (None, error_str)."""
    text = safe_read_text(path)
    if not text.strip():
        return None, "File is empty"
    try:
        data = json.loads(text)
        if isinstance(data, dict):
            return data, None
        return None, "Manifest root is not a JSON object"
    except Exception as exc:
        return None, f"JSON parse error: {str(exc)}"


class EcosystemDetector:
    """Discovers programming languages, frameworks, package managers, and architecture."""

    def __init__(self, repo_root: Path, inventory: List[FileInventoryItem]):
        self.repo_root = repo_root
        self.inventory = inventory
        self.paths_set: Set[str] = {item.relative_path for item in inventory}
        self.ext_counts: Dict[str, int] = {}
        for item in inventory:
            ext = item.extension.lower()
            if ext:
                self.ext_counts[ext] = self.ext_counts.get(ext, 0) + 1

    def detect_languages(self) -> List[str]:
        """Detect primary programming languages based on source code presence."""
        langs = []
        mapping = [
            ("TypeScript", {".ts", ".tsx"}),
            ("JavaScript", {".js", ".jsx", ".mjs", ".cjs"}),
            ("Python", {".py", ".pyi"}),
            ("Java", {".java"}),
            ("Kotlin", {".kt", ".kts"}),
            ("Rust", {".rs"}),
            ("Go", {".go"}),
            ("C++", {".cpp", ".cc", ".cxx", ".hpp", ".hxx"}),
            ("C", {".c", ".h"}),
            ("C#", {".cs"}),
            ("PHP", {".php"}),
            ("Ruby", {".rb"}),
            ("Dart", {".dart"}),
            ("Swift", {".swift"}),
            ("Shell", {".sh", ".bash", ".zsh", ".ps1"}),
            ("HTML", {".html", ".htm"}),
            ("CSS", {".css", ".scss", ".sass", ".less"}),
        ]
        for name, exts in mapping:
            count = sum(self.ext_counts.get(e, 0) for e in exts)
            if count > 0:
                langs.append(name)
        return langs

    def detect_package_managers_and_manifests(self) -> Tuple[List[str], List[str], List[str]]:
        """Identify package managers, manifests, and lockfiles."""
        pms = []
        manifests = []
        lockfiles = []

        checks = [
            # Node / JS
            ("npm", ["package.json"], ["package-lock.json"]),
            ("pnpm", ["pnpm-lock.yaml", "pnpm-workspace.yaml"], ["pnpm-lock.yaml"]),
            ("yarn", ["yarn.lock"], ["yarn.lock"]),
            ("bun", ["bun.lockb", "bun.lock"], ["bun.lockb", "bun.lock"]),
            # Python
            ("pip", ["requirements.txt", "requirements-dev.txt"], []),
            ("poetry", ["poetry.lock"], ["poetry.lock"]),
            ("pipenv", ["Pipfile", "Pipfile.lock"], ["Pipfile.lock"]),
            ("uv", ["uv.lock"], ["uv.lock"]),
            ("flit", ["pyproject.toml"], []),
            ("setuptools", ["setup.py", "setup.cfg"], []),
            # Java / Kotlin
            ("maven", ["pom.xml"], []),
            ("gradle", ["build.gradle", "build.gradle.kts"], ["gradle.lockfile"]),
            # Rust
            ("cargo", ["Cargo.toml"], ["Cargo.lock"]),
            # Go
            ("go-modules", ["go.mod"], ["go.sum"]),
            # PHP
            ("composer", ["composer.json"], ["composer.lock"]),
            # Ruby
            ("bundler", ["Gemfile"], ["Gemfile.lock"]),
            # Dart / Flutter
            ("pub", ["pubspec.yaml"], ["pubspec.lock"]),
            # .NET
            ("nuget", ["*.csproj", "*.sln", "packages.config"], []),
        ]

        found_pms = set()
        for pm_name, manifest_patterns, lock_patterns in checks:
            for m in manifest_patterns:
                if any(self._matches_pattern(p, m) for p in self.paths_set):
                    found_pms.add(pm_name)
                    manifests.extend([p for p in self.paths_set if self._matches_pattern(p, m)])
            for l in lock_patterns:
                if any(self._matches_pattern(p, l) for p in self.paths_set):
                    found_pms.add(pm_name)
                    lockfiles.extend([p for p in self.paths_set if self._matches_pattern(p, l)])

        # Discovered package.json check
        if any(p.endswith("package.json") for p in self.paths_set) and not (
            "yarn" in found_pms or "pnpm" in found_pms or "bun" in found_pms
        ):
            found_pms.add("npm")

        return sorted(list(found_pms)), sorted(list(set(manifests))), sorted(list(set(lockfiles)))

    def _matches_pattern(self, path_str: str, pattern: str) -> bool:
        if pattern.startswith("*."):
            return path_str.endswith(pattern[1:])
        return path_str.lower() == pattern.lower() or path_str.lower().endswith("/" + pattern.lower())

    def detect_frameworks_and_tech(self) -> List[str]:
        """Detect web, backend, and utility frameworks based on manifests and files."""
        frameworks: Set[str] = set()

        # Check package.json dependencies
        pkg_paths = [p for p in self.paths_set if p.endswith("package.json")]
        for pp in pkg_paths:
            full_path = self.repo_root / pp
            data, err = parse_json_manifest(full_path)
            if data:
                all_deps = {
                    **data.get("dependencies", {}),
                    **data.get("devDependencies", {}),
                    **data.get("peerDependencies", {}),
                }
                dep_map = {
                    "react": "React",
                    "next": "Next.js",
                    "vue": "Vue.js",
                    "nuxt": "Nuxt.js",
                    "@angular/core": "Angular",
                    "svelte": "Svelte",
                    "@sveltejs/kit": "SvelteKit",
                    "express": "Express",
                    "fastify": "Fastify",
                    "@nestjs/core": "NestJS",
                    "koa": "Koa",
                    "hono": "Hono",
                    "tailwindcss": "Tailwind CSS",
                    "prisma": "Prisma ORM",
                    "@prisma/client": "Prisma ORM",
                    "typeorm": "TypeORM",
                    "drizzle-orm": "Drizzle ORM",
                    "mongoose": "Mongoose",
                    "redux": "Redux",
                    "@reduxjs/toolkit": "Redux Toolkit",
                    "zustand": "Zustand",
                    "pinia": "Pinia",
                    "astro": "Astro",
                    "remix": "Remix",
                    "@remix-run/react": "Remix",
                    "gatsby": "Gatsby",
                    "vite": "Vite",
                    "webpack": "Webpack",
                    "jest": "Jest",
                    "vitest": "Vitest",
                    "playwright": "Playwright",
                    "@playwright/test": "Playwright",
                    "cypress": "Cypress",
                    "eslint": "ESLint",
                    "prettier": "Prettier",
                }
                for dep_key, fw_name in dep_map.items():
                    if dep_key in all_deps:
                        frameworks.add(fw_name)

        # Check Python dependencies from requirements or pyproject.toml
        py_files = [p for p in self.paths_set if p in ("requirements.txt", "pyproject.toml", "setup.py", "Pipfile")]
        for pf in py_files:
            text = safe_read_text(self.repo_root / pf).lower()
            if "fastapi" in text:
                frameworks.add("FastAPI")
            if "flask" in text:
                frameworks.add("Flask")
            if "django" in text:
                frameworks.add("Django")
            if "celery" in text:
                frameworks.add("Celery")
            if "sqlalchemy" in text:
                frameworks.add("SQLAlchemy")
            if "pydantic" in text:
                frameworks.add("Pydantic")
            if "pytest" in text:
                frameworks.add("Pytest")
            if "ruff" in text:
                frameworks.add("Ruff")
            if "black" in text:
                frameworks.add("Black")
            if "flake8" in text:
                frameworks.add("Flake8")
            if "mypy" in text:
                frameworks.add("Mypy")

        # Java / JVM frameworks
        for jf in [p for p in self.paths_set if p in ("pom.xml", "build.gradle", "build.gradle.kts")]:
            text = safe_read_text(self.repo_root / jf).lower()
            if "spring-boot" in text or "springframework" in text:
                frameworks.add("Spring Boot")
            if "quarkus" in text:
                frameworks.add("Quarkus")
            if "micronaut" in text:
                frameworks.add("Micronaut")
            if "junit" in text:
                frameworks.add("JUnit")

        # Go frameworks
        if "go.mod" in self.paths_set:
            text = safe_read_text(self.repo_root / "go.mod").lower()
            if "gin-gonic/gin" in text:
                frameworks.add("Gin")
            if "gofiber/fiber" in text:
                frameworks.add("Fiber")
            if "labstack/echo" in text:
                frameworks.add("Echo")

        # Rust crates
        if "Cargo.toml" in self.paths_set:
            text = safe_read_text(self.repo_root / "Cargo.toml").lower()
            if "actix-web" in text:
                frameworks.add("Actix Web")
            if "axum" in text:
                frameworks.add("Axum")
            if "tokio" in text:
                frameworks.add("Tokio")

        # PHP frameworks
        if "composer.json" in self.paths_set:
            text = safe_read_text(self.repo_root / "composer.json").lower()
            if "laravel/framework" in text:
                frameworks.add("Laravel")
            if "symfony/symfony" in text or "symfony/framework-bundle" in text:
                frameworks.add("Symfony")

        # Ruby frameworks
        if "Gemfile" in self.paths_set:
            text = safe_read_text(self.repo_root / "Gemfile").lower()
            if "rails" in text:
                frameworks.add("Ruby on Rails")
            if "sinatra" in text:
                frameworks.add("Sinatra")

        # Dart / Flutter
        if "pubspec.yaml" in self.paths_set:
            text = safe_read_text(self.repo_root / "pubspec.yaml").lower()
            if "flutter:" in text or "sdk: flutter" in text:
                frameworks.add("Flutter")

        # Static Site Generators
        if "mkdocs.yml" in self.paths_set:
            frameworks.add("MkDocs")
        if "docusaurus.config.js" in self.paths_set or "docusaurus.config.ts" in self.paths_set:
            frameworks.add("Docusaurus")
        if "_config.yml" in self.paths_set:
            frameworks.add("Jekyll")
        if "hugo.toml" in self.paths_set or "config.toml" in self.paths_set:
            frameworks.add("Hugo")

        return sorted(list(frameworks))

    def detect_entry_points(self) -> List[str]:
        """Detect main application entry points."""
        entry_points = []

        # package.json main/module/bin
        pkg_json = self.repo_root / "package.json"
        if pkg_json.is_file():
            data, _ = parse_json_manifest(pkg_json)
            if data:
                for field in ("main", "module", "bin"):
                    val = data.get(field)
                    if isinstance(val, str) and (self.repo_root / val).is_file():
                        entry_points.append(Path(val).as_posix())
                    elif isinstance(val, dict):
                        for b_val in val.values():
                            if isinstance(b_val, str) and (self.repo_root / b_val).is_file():
                                entry_points.append(Path(b_val).as_posix())

        # Common known entry points
        standard_entries = [
            "src/index.ts", "src/index.js", "src/main.ts", "src/main.js", "src/App.tsx", "src/App.jsx",
            "app/page.tsx", "app/page.jsx", "pages/index.tsx", "pages/index.jsx",
            "index.js", "index.ts", "main.py", "app.py", "wsgi.py", "asgi.py", "server.py",
            "src/main.py", "src/app.py",
            "cmd/main.go", "main.go",
            "src/main.rs", "src/lib.rs",
            "index.html", "public/index.html",
            "src/index.php", "public/index.php",
        ]
        for candidate in standard_entries:
            if candidate in self.paths_set and candidate not in entry_points:
                entry_points.append(candidate)

        return entry_points

    def detect_monorepo(self) -> Tuple[bool, List[str]]:
        """Identify if repository is a monorepo and discover workspace packages."""
        monorepo_indicators = [
            "pnpm-workspace.yaml", "lerna.json", "nx.json", "turbo.json", "rush.json"
        ]
        is_mono = any(ind in self.paths_set for ind in monorepo_indicators)

        subpackages: List[str] = []
        # Look for packages/* or apps/* containing package.json or Cargo.toml
        for p in self.paths_set:
            parts = p.split("/")
            if len(parts) >= 2 and parts[0] in ("packages", "apps", "services", "modules"):
                if parts[-1] in ("package.json", "Cargo.toml", "pyproject.toml", "pom.xml", "build.gradle"):
                    pkg_dir = "/".join(parts[:-1])
                    if pkg_dir not in subpackages:
                        subpackages.append(pkg_dir)

        if len(subpackages) >= 2:
            is_mono = True

        return is_mono, sorted(subpackages)

    def detect_project_types(self, is_monorepo: bool) -> List[str]:
        """Determine high-level project type classifications."""
        types: List[str] = []

        if is_monorepo:
            types.append("Monorepository")

        # Static site or documentation-only check
        doc_count = sum(1 for p in self.paths_set if p.endswith((".md", ".rst", ".adoc")))
        source_count = sum(1 for item in self.inventory if item.category.value == "source")
        if doc_count > 0 and source_count == 0:
            types.append("Documentation-only Repository")

        if "index.html" in self.paths_set and source_count <= 2:
            types.append("Static Website")

        # Web Frontend
        fe_indicators = {"React", "Next.js", "Vue.js", "Nuxt.js", "Angular", "Svelte", "SvelteKit", "Astro", "Remix"}
        if any(fi in self.detect_frameworks_and_tech() for fi in fe_indicators):
            types.append("Web Application (Frontend)")

        # Web Backend / API
        be_indicators = {"Express", "NestJS", "Fastify", "FastAPI", "Flask", "Django", "Spring Boot", "Actix Web", "Axum", "Gin", "Laravel", "Ruby on Rails"}
        if any(bi in self.detect_frameworks_and_tech() for bi in be_indicators):
            types.append("Backend Web Service / API")

        # CLI Tool / Library
        if "pyproject.toml" in self.paths_set or "Cargo.toml" in self.paths_set or "package.json" in self.paths_set:
            pkg_json = self.repo_root / "package.json"
            if pkg_json.is_file():
                d, _ = parse_json_manifest(pkg_json)
                if d and "bin" in d and "CLI Tool" not in types:
                    types.append("CLI Tool")

        if not types:
            if source_count > 0:
                types.append("General Software Repository")
            else:
                types.append("Unclassified Repository")

        return types

