"""Reference and dependency analyzer for RepoCraft codebase maintenance.

Analyzes static/dynamic imports, framework routing conventions, manifest entrypoints,
CSS/HTML asset references, and build tool references to understand file usage.
"""
from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Dict, List, Set, Tuple


class ReferenceAnalyzer:
    """Discovers internal cross-references, imports, asset links, and framework entrypoints."""

    def __init__(self, repo_root: Path, file_paths: List[str]):
        self.repo_root = repo_root
        self.file_paths = file_paths
        self.paths_set: Set[str] = set(file_paths)
        # Map basename to list of paths
        self.basename_map: Dict[str, List[str]] = {}
        for p in file_paths:
            bn = Path(p).name
            self.basename_map.setdefault(bn, []).append(p)

    def analyze_references(self) -> Dict[str, Set[str]]:
        """Maps each file path to the set of files that reference it.

        Returns:
            Dict[target_file_path, Set[referencing_file_paths]]
        """
        references: Dict[str, Set[str]] = {p: set() for p in self.file_paths}

        for rel_path in self.file_paths:
            full_path = self.repo_root / rel_path
            try:
                # Skip binary files or massive files
                if full_path.stat().st_size > 1024 * 1024:
                    continue
                content = self._safe_read(full_path)
                if not content:
                    continue

                ext = Path(rel_path).suffix.lower()

                # 1. Python imports
                if ext in (".py", ".pyi"):
                    self._extract_python_refs(rel_path, content, references)

                # 2. JS / TS / JSX / TSX / Vue / Svelte imports
                elif ext in (".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs", ".vue", ".svelte"):
                    self._extract_jsts_refs(rel_path, content, references)

                # 3. HTML / Web assets
                elif ext in (".html", ".htm"):
                    self._extract_html_refs(rel_path, content, references)

                # 4. CSS / SCSS
                elif ext in (".css", ".scss", ".sass", ".less"):
                    self._extract_css_refs(rel_path, content, references)

                # 5. Manifests and configs (package.json, pyproject.toml, etc.)
                elif rel_path.endswith((".json", ".toml", ".yaml", ".yml")):
                    self._extract_config_refs(rel_path, content, references)

                # 6. Dockerfile, Makefile, Shell scripts
                elif Path(rel_path).name.lower() in ("dockerfile", "makefile") or ext in (".sh", ".bash", ".ps1"):
                    self._extract_script_refs(rel_path, content, references)

                # 7. Documentation links
                elif ext in (".md", ".rst"):
                    self._extract_doc_refs(rel_path, content, references)

            except Exception:
                continue

        return references

    def identify_framework_conventions(self) -> Set[str]:
        """Identifies files that are framework entrypoints or routes (never considered unused)."""
        convention_files: Set[str] = set()

        for p in self.file_paths:
            parts = p.split("/")
            name = parts[-1].lower()

            # Next.js App Router conventions: app/**/(page|layout|route|loading|error|not-found|template|default).*
            if parts[0] == "app" or (len(parts) > 1 and parts[1] == "app"):
                stem = Path(p).stem.lower()
                if stem in ("page", "layout", "route", "loading", "error", "not-found", "template", "default"):
                    convention_files.add(p)

            # Next.js / Nuxt / SvelteKit Pages Router conventions: pages/**/*
            if parts[0] == "pages" or (len(parts) > 1 and parts[1] == "pages"):
                convention_files.add(p)

            # SvelteKit src/routes/**/*
            if "routes" in parts:
                convention_files.add(p)

            # Standard entrypoints
            if name in (
                "index.js", "index.ts", "index.jsx", "index.tsx", "index.html",
                "app.js", "app.ts", "app.jsx", "app.tsx",
                "main.py", "app.py", "wsgi.py", "asgi.py", "server.py", "__init__.py", "__main__.py",
                "main.go", "main.rs", "lib.rs", "application.java",
            ):
                convention_files.add(p)

            # Django conventions
            if name in ("urls.py", "models.py", "views.py", "settings.py", "admin.py", "apps.py", "manage.py"):
                convention_files.add(p)

            # Configuration & root files
            if len(parts) == 1 and (p.startswith(".") or p.endswith((".json", ".toml", ".yaml", ".yml", ".config.js", ".config.ts"))):
                convention_files.add(p)

            # Test files
            if any(test_dir in parts for test_dir in ("tests", "test", "__tests__", "spec", "specs", "e2e")):
                convention_files.add(p)
            if re.search(r"(test_.*\.py|.*_test\.py|.*\.(test|spec)\.[jt]sx?)$", name):
                convention_files.add(p)

            # Governance files
            if name in (
                "readme.md", "license", "license.md", "licence", "copying",
                "contributing.md", "code_of_conduct.md", "security.md", "changelog.md",
            ):
                convention_files.add(p)

        return convention_files

    def _safe_read(self, path: Path) -> str:
        try:
            return path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            return ""

    def _extract_python_refs(self, source_path: str, content: str, references: Dict[str, Set[str]]) -> None:
        source_dir = Path(source_path).parent.as_posix()
        if source_dir == ".":
            source_dir = ""

        # from .submodule import ... or from foo import bar
        from_matches = re.findall(r"^\s*from\s+([.\w]+)\s+import", content, re.MULTILINE)
        import_matches = re.findall(r"^\s*import\s+([\w\.]+)", content, re.MULTILINE)

        for mod in from_matches + import_matches:
            # Check relative import
            if mod.startswith("."):
                rel_mod = mod.lstrip(".")
                candidate_py = (Path(source_dir) / f"{rel_mod}.py").as_posix() if source_dir else f"{rel_mod}.py"
                candidate_pkg = (Path(source_dir) / rel_mod / "__init__.py").as_posix() if source_dir else f"{rel_mod}/__init__.py"
                if candidate_py in self.paths_set:
                    references[candidate_py].add(source_path)
                if candidate_pkg in self.paths_set:
                    references[candidate_pkg].add(source_path)
            else:
                mod_parts = mod.split(".")
                # Check top-level or relative
                cand1 = f"{'/'.join(mod_parts)}.py"
                cand2 = f"{'/'.join(mod_parts)}/__init__.py"
                cand3 = f"src/{'/'.join(mod_parts)}.py"
                cand4 = f"src/{'/'.join(mod_parts)}/__init__.py"
                for cand in (cand1, cand2, cand3, cand4):
                    if cand in self.paths_set:
                        references[cand].add(source_path)

    def _extract_jsts_refs(self, source_path: str, content: str, references: Dict[str, Set[str]]) -> None:
        source_dir = Path(source_path).parent.as_posix()
        if source_dir == ".":
            source_dir = ""

        # import ... from '...' or require('...') or import('...')
        pattern = r"""(?:import|require|from)\s*\(?['"]([^'"]+)['"]\)?|import\s+['"]([^'"]+)['"]"""
        matches = re.findall(pattern, content)

        for match_tuple in matches:
            import_str = match_tuple[0] or match_tuple[1]
            if not import_str or not import_str.startswith("."):
                # Non-relative (e.g. "@/components/Button")
                if import_str.startswith("@/"):
                    clean = import_str[2:]
                    self._match_jsts_candidate(clean, source_path, references)
                elif import_str.startswith("~/"):
                    clean = import_str[2:]
                    self._match_jsts_candidate(clean, source_path, references)
                continue

            # Relative path
            try:
                base_dir = Path(source_dir) if source_dir else Path(".")
                target_path = (base_dir / import_str).resolve()
                # Find relative to repo_root
                rel_target = target_path.relative_to(self.repo_root).as_posix()
                self._match_jsts_candidate(rel_target, source_path, references)
            except Exception:
                # If resolve fails outside repo
                norm = os.path.normpath(os.path.join(source_dir, import_str)).replace("\\", "/")
                self._match_jsts_candidate(norm, source_path, references)

    def _match_jsts_candidate(self, base_cand: str, source_path: str, references: Dict[str, Set[str]]) -> None:
        extensions = ["", ".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".vue", ".svelte", "/index.ts", "/index.js", "/index.tsx", "/index.jsx"]
        for ext in extensions:
            cand = f"{base_cand}{ext}"
            if cand in self.paths_set:
                references[cand].add(source_path)

    def _extract_html_refs(self, source_path: str, content: str, references: Dict[str, Set[str]]) -> None:
        source_dir = Path(source_path).parent.as_posix()
        # Find src="...", href="..."
        matches = re.findall(r"""(?:src|href)=['"]([^'"]+)['"]""", content)
        for m in matches:
            if m.startswith(("http://", "https://", "mailto:", "#", "javascript:")):
                continue
            clean = m.split("?")[0].split("#")[0].lstrip("/")
            # check directly or relative to source
            cand1 = clean
            cand2 = f"{source_dir}/{clean}" if source_dir else clean
            for cand in (cand1, cand2):
                if cand in self.paths_set:
                    references[cand].add(source_path)

    def _extract_css_refs(self, source_path: str, content: str, references: Dict[str, Set[str]]) -> None:
        source_dir = Path(source_path).parent.as_posix()
        matches = re.findall(r"""url\(['"]?([^'"\)]+)['"]?\)""", content)
        for m in matches:
            if m.startswith(("http://", "https://", "data:")):
                continue
            clean = m.split("?")[0].split("#")[0].lstrip("/")
            cand1 = clean
            cand2 = f"{source_dir}/{clean}" if source_dir else clean
            for cand in (cand1, cand2):
                if cand in self.paths_set:
                    references[cand].add(source_path)

    def _extract_config_refs(self, source_path: str, content: str, references: Dict[str, Set[str]]) -> None:
        # Search for occurrences of any inventoried filename inside config
        for bn, paths in self.basename_map.items():
            if bn in content:
                for p in paths:
                    references[p].add(source_path)

    def _extract_script_refs(self, source_path: str, content: str, references: Dict[str, Set[str]]) -> None:
        for p in self.file_paths:
            if p in content:
                references[p].add(source_path)

    def _extract_doc_refs(self, source_path: str, content: str, references: Dict[str, Set[str]]) -> None:
        # Markdown links [text](path) or ![img](path)
        matches = re.findall(r"""\[(?:[^\]]*)\]\(([^)]+)\)""", content)
        source_dir = Path(source_path).parent.as_posix()
        for m in matches:
            link = m.split("#")[0].split("?")[0].strip()
            if link.startswith(("http://", "https://", "mailto:")):
                continue
            cand1 = link
            cand2 = f"{source_dir}/{link}" if source_dir else link
            cand3 = os.path.normpath(cand2).replace("\\", "/")
            for cand in (cand1, cand2, cand3):
                if cand in self.paths_set:
                    references[cand].add(source_path)
