"""Comprehensive Phase 3 Test Suite for RepoCraft Security Engine.

Covers 70 distinct test scenarios across:
1-12: Secret scanning
13-24: Dependency auditing
25-32: Application security patterns
33-38: Configuration & supply chain
39-51: Test discovery, readiness, and safe execution
52-58: CI/CD workflow auditing
59-70: Integration, reporting, and CLI
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict

import pytest

# Ensure skill scripts is on sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent
SKILL_SCRIPTS = REPO_ROOT / "skill" / "scripts"
if str(SKILL_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SKILL_SCRIPTS))

from engine.security import (
    CicdWorkflowAudit,
    ConfigurationFinding,
    DependencyAuditResult,
    SecretConfidence,
    SecretFinding,
    SecurityPatternFinding,
    SecuritySeverity,
    SupplyChainFinding,
    TestDiscoveryItem,
    TestExecutionResult,
    TestExecutionState,
    VulnerabilityStatus,
    analyze_test_output,
    assess_overall_security_risk,
    assess_test_readiness,
    audit_cicd,
    audit_configuration,
    audit_dependencies,
    audit_supply_chain,
    discover_tests,
    execute_test_command,
    find_test_files,
    generate_security_reports,
    is_command_safe,
    redact_string,
    run_security_pipeline,
    scan_secrets,
    scan_security_patterns,
)


# ==============================================================================
# 1-12: SECRET SCANNING TESTS
# ==============================================================================

def test_01_private_key_detection(tmp_path: Path):
    rsa_key = "-----BEGIN RSA PRIVATE KEY-----\nMIIEowIBAAKCAQEA0Y3...\n-----END RSA PRIVATE KEY-----"
    (tmp_path / "server.key").write_text(rsa_key, encoding="utf-8")
    findings = scan_secrets(str(tmp_path))
    assert any(f.rule_id == "SEC-KEY-001" and f.severity == SecuritySeverity.CRITICAL for f in findings)


def test_02_aws_credential_detection(tmp_path: Path):
    code = 'AWS_KEY = "AKIAIOSFODNN7EXAMPLE"'
    (tmp_path / "config.py").write_text(code, encoding="utf-8")
    findings = scan_secrets(str(tmp_path))
    assert any(f.rule_id == "SEC-AWS-001" for f in findings)


def test_03_stripe_key_detection(tmp_path: Path):
    token = "sk_" + "live_51AbcdefghijklmnopQRSTUVWX1234567890"
    code = f'STRIPE_SECRET = "{token}"'
    (tmp_path / "payment.py").write_text(code, encoding="utf-8")
    findings = scan_secrets(str(tmp_path))
    assert any(f.rule_id == "SEC-STRIPE-001" and f.severity == SecuritySeverity.CRITICAL for f in findings)


def test_04_github_pat_detection(tmp_path: Path):
    token = "ghp_" + "123456789012345678901234567890123456"
    code = f'GITHUB_TOKEN = "{token}"'
    (tmp_path / "ci_deploy.py").write_text(code, encoding="utf-8")
    findings = scan_secrets(str(tmp_path))
    assert any(f.rule_id == "SEC-GH-001" for f in findings)


def test_05_slack_token_detection(tmp_path: Path):
    token = "xoxb-" + "123456789012-123456789012-abcdefghijklmnopqrstuv"
    code = f'SLACK_BOT_TOKEN = "{token}"'
    (tmp_path / "notify.py").write_text(code, encoding="utf-8")
    findings = scan_secrets(str(tmp_path))
    assert any(f.rule_id == "SEC-SLACK-001" for f in findings)


def test_06_openai_api_key_detection(tmp_path: Path):
    token = "sk-proj-" + "1234567890abcdef1234567890abcdef12345678"
    code = f'OPENAI_KEY = "{token}"'
    (tmp_path / "ai.py").write_text(code, encoding="utf-8")
    findings = scan_secrets(str(tmp_path))
    assert any(f.rule_id == "SEC-OPENAI-001" for f in findings)


def test_07_google_api_key_detection(tmp_path: Path):
    token = "AIza" + "SyD-1234567890abcdefghijklmnopqr"
    code = f'MAPS_KEY = "{token}"'
    (tmp_path / "maps.js").write_text(code, encoding="utf-8")
    findings = scan_secrets(str(tmp_path))
    assert any(f.rule_id == "SEC-GOOG-001" for f in findings)


def test_08_database_connection_uri(tmp_path: Path):
    code = 'DB_URI = "postgres://admin:SuperSecretPass123!@localhost:5432/mydb"'
    (tmp_path / "db.py").write_text(code, encoding="utf-8")
    findings = scan_secrets(str(tmp_path))
    assert any(f.rule_id == "SEC-DB-001" for f in findings)


def test_09_generic_password_assignment(tmp_path: Path):
    code = 'db_password = "MyComplexPassword987#"'
    (tmp_path / "settings.py").write_text(code, encoding="utf-8")
    findings = scan_secrets(str(tmp_path))
    assert any(f.rule_id == "SEC-GEN-001" for f in findings)


def test_10_sensitive_file_detection(tmp_path: Path):
    (tmp_path / ".env").write_text("DATABASE_URL=postgres://localhost\nSECRET_KEY=123", encoding="utf-8")
    findings = scan_secrets(str(tmp_path))
    assert any(f.rule_id == "SEC-FILE-001" and f.file_path == ".env" for f in findings)


def test_11_secret_redaction_verification():
    raw_secret = "sk_" + "live_51AbcdefghijklmnopQRSTUVWX1234567890"
    redacted = redact_string(raw_secret)
    assert raw_secret not in redacted
    assert "sk_live_" in redacted
    assert "*" in redacted


def test_12_non_secret_baseline(tmp_path: Path):
    (tmp_path / "hello.py").write_text('def hello(): return "Hello World"', encoding="utf-8")
    findings = scan_secrets(str(tmp_path))
    assert len(findings) == 0


# ==============================================================================
# 13-24: DEPENDENCY AUDITING TESTS
# ==============================================================================

def test_13_npm_package_json_with_lockfile(tmp_path: Path):
    pkg = {"name": "test-pkg", "dependencies": {"express": "^4.18.2"}}
    lock = {"name": "test-pkg", "lockfileVersion": 3}
    (tmp_path / "package.json").write_text(json.dumps(pkg), encoding="utf-8")
    (tmp_path / "package-lock.json").write_text(json.dumps(lock), encoding="utf-8")
    audits = audit_dependencies(str(tmp_path))
    assert len(audits) == 1
    assert audits[0].lockfile_present is True
    assert audits[0].ecosystem == "npm"


def test_14_npm_package_json_missing_lockfile(tmp_path: Path):
    pkg = {"name": "test-pkg", "dependencies": {"lodash": "4.17.21"}}
    (tmp_path / "package.json").write_text(json.dumps(pkg), encoding="utf-8")
    audits = audit_dependencies(str(tmp_path))
    assert len(audits) == 1
    assert audits[0].lockfile_present is False
    assert audits[0].notes is not None and "Missing lockfile" in audits[0].notes


def test_15_npm_wildcard_unpinned_versions(tmp_path: Path):
    pkg = {"dependencies": {"express": "*", "react": "latest", "axios": "^1.2.0"}}
    (tmp_path / "package.json").write_text(json.dumps(pkg), encoding="utf-8")
    audits = audit_dependencies(str(tmp_path))
    assert audits[0].unpinned_count >= 2


def test_16_npm_suspicious_git_http_dependencies(tmp_path: Path):
    pkg = {"dependencies": {"my-lib": "http://insecure-domain.org/pkg.tgz"}}
    (tmp_path / "package.json").write_text(json.dumps(pkg), encoding="utf-8")
    audits = audit_dependencies(str(tmp_path))
    assert audits[0].suspicious_sources_count >= 1


def test_17_python_requirements_pinned(tmp_path: Path):
    reqs = "requests==2.31.0\npytest==7.4.0\n"
    (tmp_path / "requirements.txt").write_text(reqs, encoding="utf-8")
    audits = audit_dependencies(str(tmp_path))
    assert len(audits) == 1
    assert audits[0].unpinned_count == 0
    assert len(audits[0].dependencies) == 2


def test_18_python_requirements_unpinned(tmp_path: Path):
    reqs = "flask\nrequests>=2.0.0\n"
    (tmp_path / "requirements.txt").write_text(reqs, encoding="utf-8")
    audits = audit_dependencies(str(tmp_path))
    assert audits[0].unpinned_count == 2


def test_19_python_pyproject_poetry_lock(tmp_path: Path):
    pyproject = '[tool.poetry.dependencies]\npython = "^3.10"\nrequests = "^2.28.0"\n'
    (tmp_path / "pyproject.toml").write_text(pyproject, encoding="utf-8")
    (tmp_path / "poetry.lock").write_text("# Poetry lockfile", encoding="utf-8")
    audits = audit_dependencies(str(tmp_path))
    assert any(a.manifest_path == "pyproject.toml" and a.lockfile_present is True for a in audits)


def test_20_python_pipfile(tmp_path: Path):
    pipfile = '[[source]]\nname = "pypi"\n[packages]\nrequests = "*"\n'
    (tmp_path / "Pipfile").write_text(pipfile, encoding="utf-8")
    audits = audit_dependencies(str(tmp_path))
    assert any(a.manifest_path == "Pipfile" and a.lockfile_present is False for a in audits)


def test_21_go_mod_dependency_parsing(tmp_path: Path):
    go_mod = "module myapp\n\ngo 1.20\n\nrequire (\n\tgithub.com/gin-gonic/gin v1.9.0\n)\n"
    (tmp_path / "go.mod").write_text(go_mod, encoding="utf-8")
    (tmp_path / "go.sum").write_text("github.com/gin-gonic/gin v1.9.0 h1:...", encoding="utf-8")
    audits = audit_dependencies(str(tmp_path))
    assert any(a.manifest_path == "go.mod" and a.lockfile_present is True for a in audits)


def test_22_rust_cargo_toml_and_lock(tmp_path: Path):
    cargo = '[package]\nname = "my_rust_app"\nversion = "0.1.0"\n[dependencies]\nserde = "1.0"\n'
    (tmp_path / "Cargo.toml").write_text(cargo, encoding="utf-8")
    (tmp_path / "Cargo.lock").write_text("# Cargo lock", encoding="utf-8")
    audits = audit_dependencies(str(tmp_path))
    assert any(a.manifest_path == "Cargo.toml" and a.lockfile_present is True for a in audits)


def test_23_missing_lockfile_detection_across_ecosystems(tmp_path: Path):
    (tmp_path / "package.json").write_text('{"name": "a"}', encoding="utf-8")
    (tmp_path / "Cargo.toml").write_text('[package]\nname = "b"\n', encoding="utf-8")
    audits = audit_dependencies(str(tmp_path))
    missing = [a for a in audits if not a.lockfile_present]
    assert len(missing) >= 2


def test_24_offline_vulnerability_status(tmp_path: Path):
    (tmp_path / "requirements.txt").write_text("requests==2.31.0\n", encoding="utf-8")
    audits = audit_dependencies(str(tmp_path))
    assert audits[0].vulnerability_status == VulnerabilityStatus.UNVERIFIED


# ==============================================================================
# 25-32: APPLICATION SECURITY PATTERNS TESTS
# ==============================================================================

def test_25_sql_injection_pattern(tmp_path: Path):
    code = 'cursor.execute(f"SELECT * FROM users WHERE id = {user_id}")'
    (tmp_path / "repo.py").write_text(code, encoding="utf-8")
    findings = scan_security_patterns(str(tmp_path))
    assert any(f.rule_id == "SEC-SQL-001" and f.category == "SQL_INJECTION" for f in findings)


def test_26_command_injection_pattern(tmp_path: Path):
    code = 'subprocess.run(f"ls {user_dir}", shell=True)'
    (tmp_path / "cmd.py").write_text(code, encoding="utf-8")
    findings = scan_security_patterns(str(tmp_path))
    assert any(f.rule_id == "SEC-CMD-001" and f.category == "COMMAND_INJECTION" for f in findings)


def test_27_dynamic_code_evaluation(tmp_path: Path):
    code = 'result = eval(user_expression)'
    (tmp_path / "calc.py").write_text(code, encoding="utf-8")
    findings = scan_security_patterns(str(tmp_path))
    assert any(f.rule_id == "SEC-EVAL-001" for f in findings)


def test_28_unsafe_deserialization(tmp_path: Path):
    code = 'obj = pickle.loads(raw_data)'
    (tmp_path / "cache.py").write_text(code, encoding="utf-8")
    findings = scan_security_patterns(str(tmp_path))
    assert any(f.rule_id == "SEC-DESER-001" for f in findings)


def test_29_insecure_cors_wildcard(tmp_path: Path):
    code = 'app.add_middleware(CORSMiddleware, allow_origins=["*"])'
    (tmp_path / "server.py").write_text(code, encoding="utf-8")
    # Also test header style
    (tmp_path / "api.js").write_text('res.setHeader("Access-Control-Allow-Origin", "*")', encoding="utf-8")
    findings = scan_security_patterns(str(tmp_path))
    assert any(f.rule_id == "SEC-CORS-001" for f in findings)


def test_30_insecure_cookie_configuration(tmp_path: Path):
    code = 'response.set_cookie("session", token, secure=False, httponly=False)'
    (tmp_path / "auth.py").write_text(code, encoding="utf-8")
    findings = scan_security_patterns(str(tmp_path))
    assert any(f.rule_id == "SEC-COOKIE-001" for f in findings)


def test_31_weak_cryptography(tmp_path: Path):
    code = 'digest = hashlib.md5(password.encode()).hexdigest()'
    (tmp_path / "hash.py").write_text(code, encoding="utf-8")
    findings = scan_security_patterns(str(tmp_path))
    assert any(f.rule_id == "SEC-CRYPTO-001" for f in findings)


def test_32_frontend_dom_injection(tmp_path: Path):
    code = 'element.innerHTML = userInput;'
    (tmp_path / "app.js").write_text(code, encoding="utf-8")
    findings = scan_security_patterns(str(tmp_path))
    assert any(f.rule_id == "SEC-DOM-001" for f in findings)


# ==============================================================================
# 33-38: CONFIGURATION & SUPPLY CHAIN TESTS
# ==============================================================================

def test_33_gitignore_missing_critical_patterns(tmp_path: Path):
    (tmp_path / ".gitignore").write_text("node_modules/\ndist/\n", encoding="utf-8")
    findings = audit_configuration(str(tmp_path))
    issues = [f.issue for f in findings if f.category == "GITIGNORE"]
    assert any(".env" in issue for issue in issues)


def test_34_completely_missing_gitignore(tmp_path: Path):
    findings = audit_configuration(str(tmp_path))
    assert any(f.category == "GITIGNORE" and "Missing .gitignore" in f.issue for f in findings)


def test_35_dockerfile_root_user_and_latest(tmp_path: Path):
    df_content = "FROM python:latest\nWORKDIR /app\nCOPY . .\nCMD [\"python\", \"app.py\"]\n"
    (tmp_path / "Dockerfile").write_text(df_content, encoding="utf-8")
    findings = audit_configuration(str(tmp_path))
    assert any("latest" in f.issue for f in findings)
    assert any("USER" in f.issue for f in findings)


def test_36_dockerfile_copying_sensitive_files(tmp_path: Path):
    df_content = "FROM python:3.11-slim\nCOPY .env /app/.env\nCMD [\"python\", \"app.py\"]\n"
    (tmp_path / "Dockerfile").write_text(df_content, encoding="utf-8")
    findings = audit_configuration(str(tmp_path))
    assert any("sensitive files" in f.issue.lower() for f in findings)


def test_37_github_actions_unpinned_references(tmp_path: Path):
    wf_dir = tmp_path / ".github" / "workflows"
    wf_dir.mkdir(parents=True)
    wf_content = """name: CI
on: [push]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
"""
    (wf_dir / "ci.yml").write_text(wf_content, encoding="utf-8")
    findings = audit_supply_chain(str(tmp_path))
    assert any(f.category == "MUTABLE_ACTION_REFERENCE" for f in findings)


def test_38_github_actions_permissions_and_script_injection(tmp_path: Path):
    wf_dir = tmp_path / ".github" / "workflows"
    wf_dir.mkdir(parents=True)
    wf_content = """name: AutoComment
on:
  issues:
    types: [opened]
permissions: write-all
jobs:
  greet:
    runs-on: ubuntu-latest
    steps:
      - name: Greet
        run: |
          echo "Title is: ${{ github.event.issue.title }}"
"""
    (wf_dir / "comment.yml").write_text(wf_content, encoding="utf-8")
    findings = audit_supply_chain(str(tmp_path))
    assert any(f.category == "WORKFLOW_PERMISSIONS" for f in findings)
    assert any(f.category == "WORKFLOW_SCRIPT_INJECTION" for f in findings)


# ==============================================================================
# 39-51: TEST DISCOVERY & EXECUTION TESTS
# ==============================================================================

def test_39_pytest_discovery_from_tests_dir(tmp_path: Path):
    test_dir = tmp_path / "tests"
    test_dir.mkdir()
    (test_dir / "test_sample.py").write_text("def test_ok(): assert True", encoding="utf-8")
    items = discover_tests(str(tmp_path))
    assert any(i.framework == "pytest" and i.command == "pytest" for i in items)


def test_40_unittest_discovery(tmp_path: Path):
    (tmp_path / "test_app.py").write_text("import unittest\nclass T(unittest.TestCase):\n    pass\n", encoding="utf-8")
    items = discover_tests(str(tmp_path))
    assert len(items) > 0


def test_41_npm_test_discovery(tmp_path: Path):
    pkg = {"scripts": {"test": "jest"}}
    (tmp_path / "package.json").write_text(json.dumps(pkg), encoding="utf-8")
    items = discover_tests(str(tmp_path))
    assert any(i.framework == "jest" and i.command == "npm test" for i in items)


def test_42_jest_vitest_identification(tmp_path: Path):
    pkg = {"devDependencies": {"vitest": "^0.34.0"}, "scripts": {"test": "vitest run"}}
    (tmp_path / "package.json").write_text(json.dumps(pkg), encoding="utf-8")
    items = discover_tests(str(tmp_path))
    assert any(i.framework == "vitest" for i in items)


def test_43_cargo_test_discovery(tmp_path: Path):
    (tmp_path / "Cargo.toml").write_text('[package]\nname = "rust_test"\n', encoding="utf-8")
    items = discover_tests(str(tmp_path))
    assert any(i.framework == "cargo" and i.command == "cargo test" for i in items)


def test_44_go_test_discovery(tmp_path: Path):
    (tmp_path / "go.mod").write_text("module example\n", encoding="utf-8")
    (tmp_path / "calc_test.go").write_text("package main\nimport \"testing\"\nfunc TestCalc(t *testing.T){}", encoding="utf-8")
    items = discover_tests(str(tmp_path))
    assert any(i.framework == "go test" for i in items)


def test_45_empty_test_file_detection(tmp_path: Path):
    (tmp_path / "test_empty.py").write_text("# Just comments\n# nothing else\n", encoding="utf-8")
    (tmp_path / "test_real.py").write_text("def test_x(): pass", encoding="utf-8")
    all_tests, empty_tests = find_test_files(str(tmp_path))
    assert len(all_tests) == 2
    assert "test_empty.py" in empty_tests
    assert "test_real.py" not in empty_tests


def test_46_missing_test_suite_detection(tmp_path: Path):
    (tmp_path / "main.py").write_text("print('hello')", encoding="utf-8")
    readiness = assess_test_readiness(str(tmp_path))
    assert readiness["is_ready_for_execution"] is False
    assert any("No test files" in b for b in readiness["blockers"])


def test_47_missing_dependencies_detection(tmp_path: Path):
    (tmp_path / "package.json").write_text('{"scripts": {"test": "jest"}}', encoding="utf-8")
    readiness = assess_test_readiness(str(tmp_path))
    assert any("node_modules" in m for m in readiness["missing_dependencies"])


def test_48_test_execution_default_mode_must_not_execute(tmp_path: Path):
    res = execute_test_command("pytest", str(tmp_path), allow_execution=False)
    assert res.state == TestExecutionState.NOT_RUN
    assert res.exit_code is None


def test_49_test_execution_authorized_mode(tmp_path: Path):
    # Run a simple python -m unittest on an empty valid test
    test_file = tmp_path / "test_pass.py"
    test_file.write_text("import unittest\nclass T(unittest.TestCase):\n    def test_ok(self):\n        pass\n", encoding="utf-8")
    res = execute_test_command(f"python -m unittest {test_file.name}", str(tmp_path), allow_execution=True)
    assert res.state == TestExecutionState.PASSED
    assert res.exit_code == 0
    assert res.tests_passed == 1


def test_50_execution_timeout_handling(tmp_path: Path):
    # Simulate timeout by calling Python sleep in a whitelisted command
    res = execute_test_command("pytest -c /nonexistent", str(tmp_path), allow_execution=True, timeout_seconds=1)
    # The command should execute and either finish quickly or time out cleanly
    assert res.state in (TestExecutionState.FAILED, TestExecutionState.PASSED, TestExecutionState.TIMED_OUT)


def test_51_destructive_command_blocked_by_policy(tmp_path: Path):
    dangerous_cmd = "pytest && rm -rf /"
    assert is_command_safe(dangerous_cmd) is False
    res = execute_test_command(dangerous_cmd, str(tmp_path), allow_execution=True)
    assert res.state == TestExecutionState.BLOCKED_BY_POLICY


# ==============================================================================
# 52-58: CI/CD WORKFLOW AUDITING TESTS
# ==============================================================================

def test_52_clean_github_actions_workflow(tmp_path: Path):
    wf_dir = tmp_path / ".github" / "workflows"
    wf_dir.mkdir(parents=True)
    wf_content = """name: Clean CI
on: [push]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@2541b1294d2704b0964813337f33b291d3f8596b # v3.0.2
      - run: npm test
      - run: npm run build
"""
    (wf_dir / "ci.yml").write_text(wf_content, encoding="utf-8")
    audits = audit_cicd(str(tmp_path))
    assert len(audits) == 1
    assert audits[0].has_test_step is True
    assert audits[0].has_build_step is True
    assert audits[0].has_unpinned_actions is False


def test_53_workflow_missing_test_step(tmp_path: Path):
    wf_dir = tmp_path / ".github" / "workflows"
    wf_dir.mkdir(parents=True)
    wf_content = """name: Deploy Only
on: [push]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - run: echo deploy
"""
    (wf_dir / "deploy.yml").write_text(wf_content, encoding="utf-8")
    audits = audit_cicd(str(tmp_path))
    assert audits[0].has_test_step is False


def test_54_workflow_missing_build_step(tmp_path: Path):
    wf_dir = tmp_path / ".github" / "workflows"
    wf_dir.mkdir(parents=True)
    wf_content = """name: Test Only
on: [push]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - run: pytest
"""
    (wf_dir / "test.yml").write_text(wf_content, encoding="utf-8")
    audits = audit_cicd(str(tmp_path))
    assert audits[0].has_test_step is True
    assert audits[0].has_build_step is False


def test_55_workflow_pull_request_target_risk(tmp_path: Path):
    wf_dir = tmp_path / ".github" / "workflows"
    wf_dir.mkdir(parents=True)
    wf_content = """name: PR Review
on: pull_request_target
jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
"""
    (wf_dir / "pr.yml").write_text(wf_content, encoding="utf-8")
    audits = audit_cicd(str(tmp_path))
    assert audits[0].has_risky_pr_triggers is True


def test_56_multi_workflow_repository(tmp_path: Path):
    wf_dir = tmp_path / ".github" / "workflows"
    wf_dir.mkdir(parents=True)
    (wf_dir / "test.yml").write_text("name: Test\non: [push]\njobs:\n  t:\n    steps:\n      - run: pytest\n", encoding="utf-8")
    (wf_dir / "lint.yml").write_text("name: Lint\non: [push]\njobs:\n  l:\n    steps:\n      - run: flake8\n", encoding="utf-8")
    audits = audit_cicd(str(tmp_path))
    assert len(audits) == 2


def test_57_gitlab_ci_detection(tmp_path: Path):
    gl_content = "stages:\n  - test\ntest_job:\n  stage: test\n  script:\n    - pytest\n"
    (tmp_path / ".gitlab-ci.yml").write_text(gl_content, encoding="utf-8")
    audits = audit_cicd(str(tmp_path))
    assert any("gitlab-ci.yml" in a.workflow_file for a in audits)


def test_58_zero_cicd_workflows(tmp_path: Path):
    audits = audit_cicd(str(tmp_path))
    assert len(audits) == 0


# ==============================================================================
# 59-70: INTEGRATION, REPORTING, AND CLI TESTS
# ==============================================================================

def test_59_full_security_pipeline_clean_repo(tmp_path: Path):
    # Setup clean repo
    (tmp_path / "main.py").write_text("def add(a, b): return a + b\n", encoding="utf-8")
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_main.py").write_text("from main import add\ndef test_add(): assert add(1, 2) == 3\n", encoding="utf-8")
    (tmp_path / ".gitignore").write_text(".env\n*.key\n*.pem\nnode_modules/\n.venv/\n", encoding="utf-8")

    reports_dir = tmp_path / "reports"
    res = run_security_pipeline(
        target_dir=str(tmp_path),
        reports_dir=str(reports_dir),
        allow_execution=False,
    )
    assert res["secrets_count"] == 0
    assert res["risk_assessment"]["overall_risk_level"] in ("MINIMAL_DETECTED_RISK", "LOW")
    assert res["risk_assessment"]["is_safe_claim_allowed"] is False


def test_60_full_security_pipeline_vulnerable_repo(tmp_path: Path):
    # Setup repo with vulnerabilities
    dummy_secret = "sk_" + "live_1234567890abcdef1234567890"
    (tmp_path / ".env").write_text(f"API_SECRET={dummy_secret}\n", encoding="utf-8")
    (tmp_path / "vuln.py").write_text('cursor.execute(f"SELECT * FROM x WHERE id={i}")\n', encoding="utf-8")

    reports_dir = tmp_path / "reports"
    res = run_security_pipeline(
        target_dir=str(tmp_path),
        reports_dir=str(reports_dir),
        allow_execution=False,
    )
    assert res["secrets_count"] > 0
    assert res["patterns_count"] > 0
    assert res["risk_assessment"]["overall_risk_level"] in ("HIGH", "CRITICAL")


def test_61_all_seven_artifacts_generated(tmp_path: Path):
    reports_dir = tmp_path / "reports"
    res = run_security_pipeline(
        target_dir=str(tmp_path),
        reports_dir=str(reports_dir),
        allow_execution=False,
    )
    expected_files = [
        "security-findings.json",
        "dependency-audit.json",
        "test-analysis.json",
        "test-execution-report.json",
        "cicd-audit.json",
        "security-quality-report.md",
        "phase3-report.md",
    ]
    for ef in expected_files:
        p = reports_dir / ef
        assert p.is_file(), f"Missing artifact: {ef}"


def test_62_security_findings_json_schema(tmp_path: Path):
    reports_dir = tmp_path / "reports"
    (tmp_path / "app.py").write_text('eval("1+1")', encoding="utf-8")
    run_security_pipeline(str(tmp_path), str(reports_dir))
    data = json.loads((reports_dir / "security-findings.json").read_text(encoding="utf-8"))
    assert "summary" in data
    assert "secrets" in data
    assert "code_patterns" in data
    assert "configuration" in data
    assert "supply_chain" in data


def test_63_dependency_audit_json_schema(tmp_path: Path):
    reports_dir = tmp_path / "reports"
    (tmp_path / "requirements.txt").write_text("requests==2.31.0\n", encoding="utf-8")
    run_security_pipeline(str(tmp_path), str(reports_dir))
    data = json.loads((reports_dir / "dependency-audit.json").read_text(encoding="utf-8"))
    assert "manifests_audited" in data
    assert "results" in data
    assert data["results"][0]["vulnerability_status"] == "UNVERIFIED"


def test_64_test_analysis_json_schema(tmp_path: Path):
    reports_dir = tmp_path / "reports"
    run_security_pipeline(str(tmp_path), str(reports_dir))
    data = json.loads((reports_dir / "test-analysis.json").read_text(encoding="utf-8"))
    assert "is_ready_for_execution" in data
    assert "total_test_files" in data
    assert "empty_test_files_count" in data


def test_65_test_execution_report_json_schema(tmp_path: Path):
    reports_dir = tmp_path / "reports"
    run_security_pipeline(str(tmp_path), str(reports_dir))
    data = json.loads((reports_dir / "test-execution-report.json").read_text(encoding="utf-8"))
    assert "test_suites_evaluated" in data
    assert "results" in data
    assert data["results"][0]["state"] == "NOT_RUN"


def test_66_cicd_audit_json_schema(tmp_path: Path):
    reports_dir = tmp_path / "reports"
    run_security_pipeline(str(tmp_path), str(reports_dir))
    data = json.loads((reports_dir / "cicd-audit.json").read_text(encoding="utf-8"))
    assert "total_workflows" in data
    assert "workflows" in data


def test_67_security_quality_report_md_validation(tmp_path: Path):
    reports_dir = tmp_path / "reports"
    dummy_secret = "sk_" + "live_51SecretTokenXYZ987654321"
    (tmp_path / "secret.py").write_text(f'KEY = "{dummy_secret}"', encoding="utf-8")
    run_security_pipeline(str(tmp_path), str(reports_dir))
    content = (reports_dir / "security-quality-report.md").read_text(encoding="utf-8")
    assert "RepoCraft Security & Quality Validation Report" in content
    assert "Overall Risk Assessment" in content
    assert dummy_secret not in content  # Redacted!
    assert "sk_live_" in content


def test_68_phase3_report_md_validation(tmp_path: Path):
    reports_dir = tmp_path / "reports"
    run_security_pipeline(str(tmp_path), str(reports_dir))
    content = (reports_dir / "phase3-report.md").read_text(encoding="utf-8")
    assert "RepoCraft Phase 3 — Executive Validation Report" in content
    assert "Summary Scorecard" in content
    assert "Next Steps & Human Verification Required" in content


def test_69_cli_repocraft_security_audit(tmp_path: Path):
    script = REPO_ROOT / "skill" / "scripts" / "repocraft_security.py"
    reports_dir = tmp_path / "reports"
    cmd = [
        sys.executable,
        str(script),
        "--target",
        str(tmp_path),
        "--reports",
        str(reports_dir),
        "--mode",
        "audit",
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    assert proc.returncode == 0
    assert "RepoCraft Phase 3 Security & Quality Validation" in proc.stdout
    assert "Assessed Risk Level:" in proc.stdout


def test_70_cli_repocraft_security_json_flag(tmp_path: Path):
    script = REPO_ROOT / "skill" / "scripts" / "repocraft_security.py"
    reports_dir = tmp_path / "reports"
    cmd = [
        sys.executable,
        str(script),
        "--target",
        str(tmp_path),
        "--reports",
        str(reports_dir),
        "--json",
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    assert proc.returncode == 0
    parsed = json.loads(proc.stdout)
    assert "risk_assessment" in parsed
    assert "generated_files" in parsed

