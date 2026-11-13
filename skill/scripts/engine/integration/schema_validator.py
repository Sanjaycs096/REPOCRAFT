"""Validates generated artifacts against registered schema specifications."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .artifact_registry import ArtifactRegistry


class SchemaValidator:
    """Validates artifact files against their registered schema contracts."""

    @classmethod
    def validate_file(cls, artifact_path: Path) -> Tuple[bool, List[str], List[str]]:
        """Validate an artifact file against its registered contract.
        
        Returns (is_valid, errors, warnings).
        """
        filename = artifact_path.name
        contract = ArtifactRegistry.get(filename)
        errors: List[str] = []
        warnings: List[str] = []

        if not artifact_path.is_file():
            return False, [f"Artifact file not found: {artifact_path}"], []

        if not filename.endswith(".json"):
            # Non-JSON artifacts (Markdown reports) are checked for non-empty content
            if artifact_path.stat().st_size == 0:
                errors.append(f"Markdown artifact {filename} is empty")
                return False, errors, warnings
            return True, errors, warnings

        # Read JSON
        try:
            content = artifact_path.read_text(encoding="utf-8")
            data = json.loads(content)
        except Exception as e:
            return False, [f"Corrupted or unparseable JSON in {filename}: {e}"], []

        if not isinstance(data, dict):
            return False, [f"Root of {filename} must be a JSON object, got {type(data).__name__}"], []

        if not contract:
            warnings.append(f"Unregistered artifact {filename}; skipping schema checks")
            return True, errors, warnings

        # Check schema version
        if "schema_version" not in data and "version" not in data:
            warnings.append(f"Missing schema_version field in {filename}")

        # Check required fields
        for field_name in contract.required_fields:
            if field_name == "files_count":
                if "files_count" not in data and "file_inventory_summary" not in data:
                    errors.append(f"Missing required field 'files_count' in {filename}")
            elif field_name not in data:
                errors.append(f"Missing required field '{field_name}' in {filename}")

        is_valid = len(errors) == 0
        return is_valid, errors, warnings

    @classmethod
    def validate_directory(cls, reports_dir: Path) -> Dict[str, Dict[str, Any]]:
        """Validate all JSON artifacts present in reports_dir."""
        results = {}
        if not reports_dir.is_dir():
            return results

        for f in sorted(reports_dir.iterdir()):
            if f.is_file() and (f.suffix == ".json" or f.suffix == ".md"):
                is_valid, errors, warnings = cls.validate_file(f)
                results[f.name] = {
                    "is_valid": is_valid,
                    "errors": errors,
                    "warnings": warnings,
                    "size_bytes": f.stat().st_size,
                }

        return results
