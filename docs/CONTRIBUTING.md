# Contributing to RepoCraft

Thank you for your interest in contributing to **RepoCraft**!

RepoCraft is a portable, evidence-backed repository engineering skill package for AI coding agents. To maintain absolute safety, portability, and trust across diverse user environments, all contributors and maintainers must adhere to the development policies outlined below.

---

## 1. Core Development Invariants & Philosophy

### Invariant 1: Development Repository Isolation (Gate E)
- When developing RepoCraft, the current working tree is the **development repository**, NOT a target project for RepoCraft's automated maintenance engine.
- **Never** execute automated commit, push, or repair workflows against the RepoCraft codebase itself.
- Committing, tagging, and publishing the RepoCraft development repository is **strictly reserved for manual human maintainer sign-off**.

### Invariant 2: Disposable Fixtures for Testing
- All tests and validation runs **must** execute against temporary, disposable Git repositories and directory structures created via pytest's `tmp_path` fixture.
- Never point tests or verification scripts at real user projects or live GitHub repositories.

### Invariant 3: Zero Telemetry Guarantee
- RepoCraft is strictly offline and privacy-first.
- **Zero tracking, analytics, phone-home, or telemetry code** is permitted anywhere in the repository.
- PRs introducing telemetry SDKs (e.g. Sentry, Mixpanel, Datadog, PostHog, Segment, Google Analytics) will be rejected immediately.

### Invariant 4: Zero External Runtime Dependencies
- RepoCraft engines and CLI drivers must run on **Python standard library only** (Python >= 3.9).
- External packages are permitted **only** in development/test environments (such as `pytest`).

---

## 2. Setting Up Your Development Environment

### Prerequisites
- Python 3.9, 3.10, 3.11, or 3.12
- Git >= 2.20
- A virtual environment is recommended:

```bash
# Clone the repository
git clone https://github.com/Sanjaycs096/REPOCRAFT.git
cd REPOCRAFT

# Create and activate a virtual environment
python -m venv .venv
# Linux/macOS:
source .venv/bin/activate
# Windows PowerShell:
.venv\Scripts\Activate.ps1

# Install test dependencies (pytest)
pip install pytest
```

---

## 3. Repository Architecture & Layout

```text
RepoCraft/
├── install.py                         # Single-file portable installer / upgrader
├── MANIFEST.json                      # Release metadata and package inventory
├── pyproject.toml                     # Project specification & test configuration
├── docs/                              # Architecture, user guides, security, release process
├── skill/                             # Installed skill payload
│   ├── SKILL.md                       # Master skill prompt and instructions
│   ├── references/                    # Operational policies and rules
│   │   ├── agent-compatibility.md
│   │   ├── git-workflow-policy.md
│   │   ├── release-and-portability-policy.md
│   │   └── repair-and-regression-policy.md
│   └── scripts/                       # Modular Python engines and CLI entry points
│       ├── repocraft_status.py        # Status & diagnostic CLI
│       ├── repocraft_intel.py         # Phase 1 intelligence CLI
│       ├── repocraft_maintenance.py   # Phase 2 maintenance CLI
│       ├── repocraft_security.py      # Phase 3 security CLI
│       ├── repocraft_repair.py        # Phase 4 bounded repair CLI
│       ├── repocraft_git.py           # Phase 5 Git workflow CLI
│       ├── repocraft_release.py       # Phase 7 release & distribution CLI
│       └── engine/                    # Underlying engine modules
└── tests/                             # Full test suite (Phases 0–7)
    ├── conftest.py
    ├── integration/                   # Lifecycle & agent integration tests
    └── distribution/                  # Phase 7 distribution, upgrade & rollback tests
```

---

## 4. Coding Standards

- **Language & Style**: Idiomatic Python 3.9+. Follow PEP 8 guidelines.
- **Type Annotations**: Use type hints on all public functions, classes, and methods.
- **Error Handling**: Use explicit, structured exceptions. Never silently swallow errors with bare `except: pass`.
- **Cross-Platform Compatibility**: Use `pathlib.Path` for all filesystem operations. Never assume Unix-style forward slashes or Windows-style backslashes.
- **Immutability & Pure Functions**: Wherever practical, make analyzers and verifiers pure functions that accept paths or data and return dataclass results.

---

## 5. Testing Guidelines

Before opening a pull request, ensure the full test suite passes locally:

```bash
# Run the entire test suite
pytest

# Run specific test suites
pytest tests/integration/
pytest tests/distribution/

# Run with verbose output
pytest -v
```

### Writing New Tests
- Place unit tests corresponding to engines in `tests/test_<engine_name>.py`.
- Place integration workflows in `tests/integration/test_<feature>.py`.
- Place distribution, upgrade, and release tests in `tests/distribution/test_<feature>.py`.
- Always use `tmp_path` to generate isolated fixture directories.
- Ensure all created git repositories and files are safely cleaned up.

---

## 6. Pull Request Process

1. **Create a Topic Branch**:
   ```bash
   git checkout -b feature/your-improvement-name
   ```
2. **Commit Changes**: Use [Conventional Commits](https://www.conventionalcommits.org/) format:
   - `feat(engine): add new secret entropy analyzer`
   - `fix(installer): handle Windows symlink edge cases`
   - `docs(user-guide): clarify rollback CLI usage`
   - `test(distribution): add test for corrupted zip archive`
3. **Verify Compliance**:
   - [ ] All tests pass across the entire suite (`pytest`).
   - [ ] No external runtime dependencies added.
   - [ ] Zero telemetry invariant maintained.
   - [ ] Code is formatted and typed.
   - [ ] New functionality includes corresponding unit and integration tests.
4. **Submit PR**: Open a pull request against the `master` branch. A maintainer will review your submission.

