# Quality Gates

Discover checks from the repository's actual manifests, scripts, configuration, and CI workflows. Do not assume a stack or command.

Possible gates:
- Formatting
- Lint
- Type checking
- Unit tests
- Integration tests
- End-to-end tests
- Production build/package
- Dependency vulnerability checks
- Secret scanning
- CI workflow review
- Documentation links and local asset validation
- Final diff and staged-content review
- Remote publishing verification

Use one status per gate: `PASS`, `FAIL`, `BLOCKED`, `NOT CONFIGURED`, or `NOT RUN`.

A missing script is `NOT CONFIGURED`. A tool unavailable in the environment is `BLOCKED` or `NOT RUN`. A failed check remains `FAIL` until rerun successfully after a justified repair. Never weaken tests or disable gates to obtain a pass.
