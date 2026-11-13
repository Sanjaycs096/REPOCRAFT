"""License and legal compliance auditor for RepoCraft.

Identifies existing license types, copyright notices, manifest declarations,
and inconsistencies. Strictly enforces safety: NEVER select, overwrite,
or create a license file without explicit user authorization.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


class LicenseAuditResult:
    def __init__(
        self,
        has_license_file: bool,
        license_path: str | None,
        detected_license_type: str,
        copyright_holders: List[str],
        manifest_declarations: Dict[str, str],
        inconsistencies: List[str],
        findings: List[Dict[str, Any]],
        requires_user_action: bool,
    ):
        self.has_license_file = has_license_file
        self.license_path = license_path
        self.detected_license_type = detected_license_type
        self.copyright_holders = copyright_holders
        self.manifest_declarations = manifest_declarations
        self.inconsistencies = inconsistencies
        self.findings = findings
        self.requires_user_action = requires_user_action

    def to_dict(self) -> Dict[str, Any]:
        return {
            "has_license_file": self.has_license_file,
            "license_path": self.license_path,
            "detected_license_type": self.detected_license_type,
            "copyright_holders": self.copyright_holders,
            "manifest_declarations": self.manifest_declarations,
            "inconsistencies": self.inconsistencies,
            "findings": self.findings,
            "requires_user_action": self.requires_user_action,
        }


class LicenseAuditor:
    """Inspects repository license files and package metadata."""

    LICENSE_PATTERNS = [
        ("MIT", [r"mit\s+license", r"permission is hereby granted, free of charge"]),
        ("Apache-2.0", [r"apache\s+license,\s+version\s+2\.0", r"http://www.apache.org/licenses/LICENSE-2.0"]),
        ("BSD-3-Clause", [r"redistribution and use in source and binary forms", r"neither the name of"]),
        ("BSD-2-Clause", [r"redistribution and use in source and binary forms"]),
        ("GPL-3.0", [r"gnu\s+general\s+public\s+license\s+version\s+3", r"gplv3"]),
        ("LGPL-3.0", [r"gnu\s+lesser\s+general\s+public\s+license"]),
        ("ISC", [r"permission to use, copy, modify, and/or distribute this software for any purpose"]),
        ("Unlicense", [r"this is free and unencumbered software released into the public domain"]),
        ("Proprietary", [r"all rights reserved", r"confidential and proprietary", r"proprietary"]),
    ]

    def __init__(self, repo_root: Path, file_paths: List[str]):
        self.repo_root = repo_root
        self.file_paths = file_paths

    def audit(self) -> LicenseAuditResult:
        license_path: Optional[str] = None
        for p in self.file_paths:
            name = Path(p).name.lower()
            if name in ("license", "license.md", "licence", "licence.md", "copying", "license.txt"):
                license_path = p
                break

        detected_type = "UNKNOWN"
        copyright_holders = []
        findings = []

        if license_path:
            full_path = self.repo_root / license_path
            try:
                text = full_path.read_text(encoding="utf-8", errors="replace")
                text_lower = text.lower()

                # Detect type
                for lic_name, patterns in self.LICENSE_PATTERNS:
                    if any(re.search(pat, text_lower) for pat in patterns):
                        detected_type = lic_name
                        break

                # Extract copyright holders
                cp_matches = re.findall(r"copyright\s+(?:\(c\)\s*)?(?:[0-9]{4}(?:-[0-9]{4})?\s+)?(.+)", text, re.IGNORECASE)
                for holder in cp_matches:
                    clean = holder.strip().rstrip(".,")
                    if clean and clean not in copyright_holders:
                        copyright_holders.append(clean)
            except Exception:
                pass
        else:
            findings.append({
                "finding_id": "FINDING-LIC-001",
                "severity": "MEDIUM",
                "issue": "Missing repository LICENSE file.",
                "explanation": "No formal LICENSE file was detected in repository root. Maintainer must decide license terms.",
                "requires_approval": True,
            })

        # Manifest declarations
        manifest_declarations: Dict[str, str] = {}
        inconsistencies: List[str] = []

        # package.json
        pkg_json = self.repo_root / "package.json"
        if pkg_json.is_file():
            try:
                data = json.loads(pkg_json.read_text(encoding="utf-8", errors="replace"))
                if "license" in data and isinstance(data["license"], str):
                    manifest_declarations["package.json"] = data["license"]
            except Exception:
                pass

        # pyproject.toml
        pyproject = self.repo_root / "pyproject.toml"
        if pyproject.is_file():
            try:
                txt = pyproject.read_text(encoding="utf-8", errors="replace")
                m = re.search(r"""license\s*=\s*(?:['"]([^'"]+)['"]|\{\s*text\s*=\s*['"]([^'"]+)['"]\s*\})""", txt)
                if m:
                    lic = m.group(1) or m.group(2)
                    manifest_declarations["pyproject.toml"] = lic
            except Exception:
                pass

        # Check inconsistencies
        for manifest_file, decl_lic in manifest_declarations.items():
            if detected_type != "UNKNOWN" and decl_lic.lower() != detected_type.lower():
                msg = (
                    f"Mismatch: {manifest_file} declares license '{decl_lic}', but LICENSE file "
                    f"text matches '{detected_type}'."
                )
                inconsistencies.append(msg)
                findings.append({
                    "finding_id": "FINDING-LIC-002",
                    "severity": "HIGH",
                    "issue": f"Conflicting license declaration in {manifest_file}.",
                    "explanation": msg,
                    "requires_approval": True,
                })

        return LicenseAuditResult(
            has_license_file=license_path is not None,
            license_path=license_path,
            detected_license_type=detected_type,
            copyright_holders=copyright_holders,
            manifest_declarations=manifest_declarations,
            inconsistencies=inconsistencies,
            findings=findings,
            requires_user_action=len(findings) > 0,
        )

