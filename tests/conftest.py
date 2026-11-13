"""Pytest fixtures and environment configuration."""
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILL_SCRIPTS = REPO_ROOT / "skill" / "scripts"

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(SKILL_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SKILL_SCRIPTS))
