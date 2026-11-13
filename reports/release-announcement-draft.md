# 🚀 Announcing RepoCraft 1.0.0-rc1 (Release Candidate)

We are excited to announce the release candidate for **RepoCraft**, a portable, reusable agentic repository-maintenance skill package for coding agents.

RepoCraft is not an application generator, web dashboard, or monolithic rewriting tool. Instead, it is installed into your existing project repository, invoked from your coding agent, and safely maintains codebase structure, documentation, security posture, tests, and Git publishing under strict, evidence-backed safety policies and human-in-the-loop approval gates.

---

## 🌟 What's in this Release Candidate?

- **Complete 7-phase repository engineering skill package for coding agents.**
- **Certified native support on Google Antigravity (.agent/skills/repocraft).**
- **Zero third-party pip dependencies required at runtime.**
- **Independent cryptographic human-in-the-loop approval gates for all file modifications and Git publishing operations.**
- **Deterministic, byte-for-byte reproducible distribution packaging.**
- **100% test coverage across 427 regression and integration test scenarios.**

## 🛡️ Core Safety Guarantees

RepoCraft is built from the ground up for safe execution in real-world repositories:
1. **Zero Silent Overwrites**: User modifications and existing skill files are strictly protected.
2. **Independent Approval Boundaries**: Staging approval, commit approval, and remote publishing require separate, explicit human authorization.
3. **Zero Third-Party Runtime Dependencies**: Runs entirely on the Python standard library (Python >= 3.9).
4. **No Secret Leaks**: Automated high-entropy token and URL credential redaction across all reports and reviews.
5. **Bounded Repairs**: Strict 3-attempt root cause limits and automatic rollback protecting subsequent user modifications.
6. **Gate E Development Repository Isolation**: The RepoCraft development repository is never automatically committed, pushed, or tagged.

## 📦 Distribution & Quick Start

### 1. Download & Verify Integrity
Distribution Archive: `repocraft-1.0.0-rc1.zip`  
SHA-256 Checksum: `44c3775c64a0e396d12d4d457230034fbb497436b9656d5c3a8543421207c145`  

Verify before installing:
```bash
echo "44c3775c64a0e396d12d4d457230034fbb497436b9656d5c3a8543421207c145  repocraft-1.0.0-rc1.zip" | sha256sum --check
```

### 2. Install into Your Target Project
```bash
# Local installer (standard)
python install.py --source /path/to/RepoCraft --target /path/to/your-project
```

### 3. Open in Your Coding Agent and Invoke
Open your project in **Google Antigravity** (certified primary agent) and prompt:

> *Run RepoCraft on this repository. Inspect the complete project, establish its Git and quality baseline, identify improvements, then safely maintain the codebase, documentation, GitHub presentation, security posture, tests, and CI/CD. Repair verified issues within policy, rerun relevant checks, review the complete diff, and publish only if every publishing condition is satisfied. Preserve my existing work. Produce a terminal summary and a detailed Markdown report.*

### 4. Verify Installation Health
```bash
python skill/scripts/repocraft_status.py --verify-installation
```

---

## 📋 Community & Feedback

- **Maintainer Review Status**: Release Candidate (Draft)
- **Documentation**: See `docs/PRODUCT-ARCHITECTURE.md` and `README.md`
- **Security Policy**: See `docs/SECURITY.md`

*Notice: This announcement is a draft generated during Phase 7 distribution preparation. Official publication will occur only when approved and tagged by the repository maintainer.*
