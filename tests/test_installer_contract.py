import json
import subprocess
import sys
from pathlib import Path


def test_local_install_creates_skill_and_manifest(tmp_path: Path):
    repo = Path(__file__).resolve().parents[1]
    target = tmp_path / "sample-project"
    target.mkdir()

    result = subprocess.run(
        [
            sys.executable, str(repo / "install.py"),
            "--source", str(repo),
            "--agent", "antigravity",
            "--target", str(target),
        ],
        capture_output=True, text=True, check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr

    installed = target / ".agent" / "skills" / "repocraft"
    assert (installed / "SKILL.md").is_file()
    manifest = json.loads((installed / "INSTALL-MANIFEST.json").read_text())
    assert manifest["name"] == "RepoCraft"
    assert manifest["agent"] == "antigravity"


def test_existing_installation_is_not_overwritten(tmp_path: Path):
    repo = Path(__file__).resolve().parents[1]
    target = tmp_path / "sample-project"
    destination = target / ".agent" / "skills" / "repocraft"
    destination.mkdir(parents=True)
    sentinel = destination / "keep-me.txt"
    sentinel.write_text("user data")

    result = subprocess.run(
        [
            sys.executable, str(repo / "install.py"),
            "--source", str(repo),
            "--agent", "antigravity",
            "--target", str(target),
        ],
        capture_output=True, text=True, check=False,
    )
    assert result.returncode == 3
    assert sentinel.read_text() == "user data"
