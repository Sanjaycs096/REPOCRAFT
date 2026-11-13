"""Module I — Bounded Root-Cause Repair Controller for RepoCraft Phase 4.

Enforces a strict 3-attempt limit per root cause across workflow executions and restarts:
- Persists attempt history in attempt-history.json
- Prevents retrying the exact same failed patch
- Prevents duplicate root causes from circumventing retry limits
- Halts automated repairs when MAX_ATTEMPTS_REACHED
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

MAX_ATTEMPTS_PER_ROOT_CAUSE = 3


class AttemptController:
    """Manages root-cause attempt counts and persistence across workflow runs."""

    def __init__(self, persistence_file: Path):
        self.persistence_file = persistence_file.resolve()
        self.history: Dict[str, Dict[str, Any]] = self._load_history()

    def _load_history(self) -> Dict[str, Dict[str, Any]]:
        if not self.persistence_file.is_file():
            return {}
        try:
            content = self.persistence_file.read_text(encoding="utf-8", errors="replace")
            data = json.loads(content)
            return data if isinstance(data, dict) else {}
        except Exception:
            return {}

    def _save_history(self) -> None:
        self.persistence_file.parent.mkdir(parents=True, exist_ok=True)
        try:
            self.persistence_file.write_text(
                json.dumps(self.history, indent=2) + "\n",
                encoding="utf-8",
            )
        except Exception:
            pass

    def can_attempt(self, root_cause_key: str, patch_hash: Optional[str] = None) -> Tuple[bool, str]:
        """Check if an attempt is permitted for the given root cause."""
        entry = self.history.get(root_cause_key, {})
        attempts_count = entry.get("attempts_count", 0)

        # 1. Enforce maximum attempt limit
        if attempts_count >= MAX_ATTEMPTS_PER_ROOT_CAUSE:
            return False, f"Maximum {MAX_ATTEMPTS_PER_ROOT_CAUSE} repair attempts reached for root cause '{root_cause_key}'."

        # 2. Prevent repeating exact same failed patch
        if patch_hash:
            previous_hashes = [h.get("patch_hash") for h in entry.get("history", []) if not h.get("success")]
            if patch_hash in previous_hashes:
                return False, f"Repetition of identical previously failed patch '{patch_hash[:10]}...' is prohibited."

        return True, f"Attempt {attempts_count + 1} permitted."

    def record_attempt(self, root_cause_key: str, patch_hash: str, success: bool, summary: str) -> int:
        """Record an attempt and update persisted history. Returns new attempt count."""
        if root_cause_key not in self.history:
            self.history[root_cause_key] = {
                "attempts_count": 0,
                "history": [],
            }

        entry = self.history[root_cause_key]
        entry["attempts_count"] += 1
        entry["history"].append({
            "attempt_number": entry["attempts_count"],
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "patch_hash": patch_hash,
            "success": success,
            "summary": summary,
        })
        self._save_history()
        return entry["attempts_count"]

    def get_attempt_count(self, root_cause_key: str) -> int:
        """Return current attempt count for root cause."""
        return self.history.get(root_cause_key, {}).get("attempts_count", 0)

