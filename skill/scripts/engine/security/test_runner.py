"""Module G — Safe Test Execution Engine for RepoCraft Phase 3.

Executes discovered test suites safely under strict policies:
- Default mode is analysis-only: tests are NEVER executed without explicit authorization
- When authorized (--execute-tests), executes only pre-approved test commands
- Enforces strict execution timeout (default 30 seconds)
- Blocks risky commands (e.g. destructive commands, install/deploy steps)
- Redacts secrets from stdout/stderr outputs
- Captures pass/fail counts and duration
"""
from __future__ import annotations

import os
import shlex
import subprocess
import time
from pathlib import Path
from typing import List, Optional

from .secret_scanner import redact_string
from .test_result_analyzer import analyze_test_output
from .types import TestExecutionResult, TestExecutionState

ALLOWED_COMMAND_PREFIXES = [
    "pytest",
    "python -m pytest",
    "python -m unittest",
    "npm test",
    "npm run test",
    "yarn test",
    "pnpm test",
    "cargo test",
    "go test",
    "mvn test",
    "./gradlew test",
    "gradle test",
]

BLOCKED_PATTERNS = [
    "rm ",
    "del ",
    "format ",
    "curl ",
    "wget ",
    "sudo ",
    "install ",
    "deploy ",
    "publish ",
    "chmod ",
    "chown ",
    ";",
    "&&",
    "||",
    "|",
    ">",
    "<",
]

MAX_OUTPUT_CHARS = 20_000
DEFAULT_TIMEOUT_SECONDS = 30


def is_command_safe(command: str) -> bool:
    """Verify if a test command is permitted by the execution policy."""
    cmd_lower = command.strip().lower()

    # Must match at least one allowed prefix
    if not any(cmd_lower == prefix or cmd_lower.startswith(prefix + " ") for prefix in ALLOWED_COMMAND_PREFIXES):
        return False

    # Must not contain dangerous operators or keywords
    if any(blocked in cmd_lower for blocked in BLOCKED_PATTERNS):
        return False

    return True


def execute_test_command(
    command: str,
    target_dir: str,
    allow_execution: bool = False,
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
) -> TestExecutionResult:
    """Safely execute a single test command or return NOT_RUN if unauthorized."""
    root = Path(target_dir).resolve()

    # 1. If execution is not explicitly enabled, return NOT_RUN
    if not allow_execution:
        return TestExecutionResult(
            command=command,
            state=TestExecutionState.NOT_RUN,
            exit_code=None,
            duration_seconds=0.0,
            tests_passed=None,
            tests_failed=None,
            tests_skipped=None,
            raw_output_redacted="Test execution was not requested. Use --execute-tests to run tests under approval.",
            error_summary=None,
        )

    # 2. Safety policy check
    if not is_command_safe(command):
        return TestExecutionResult(
            command=command,
            state=TestExecutionState.BLOCKED_BY_POLICY,
            exit_code=None,
            duration_seconds=0.0,
            tests_passed=None,
            tests_failed=None,
            tests_skipped=None,
            raw_output_redacted=f"Command '{command}' is blocked by security execution policy.",
            error_summary="Command violates safe test execution policy",
        )

    # 3. Check ecosystem prerequisites
    if command.startswith(("npm ", "yarn ", "pnpm ")):
        if not (root / "node_modules").is_dir():
            return TestExecutionResult(
                command=command,
                state=TestExecutionState.MISSING_DEPENDENCIES,
                exit_code=None,
                duration_seconds=0.0,
                tests_passed=None,
                tests_failed=None,
                tests_skipped=None,
                raw_output_redacted="Node.js test execution blocked: 'node_modules' directory is missing.",
                error_summary="Dependencies are missing (node_modules not found)",
            )

    # 4. Execute command
    start_time = time.time()
    try:
        # On Windows, use shell=False with split args
        # Note: npm and gradlew on Windows may need shell=True or executable lookup,
        # but let's check command shape safely:
        args = shlex.split(command, posix=(os.name != "nt"))
        use_shell = os.name == "nt" and args[0] in ("npm", "yarn", "pnpm", "mvn", "gradle")

        proc = subprocess.run(
            command if use_shell else args,
            cwd=str(root),
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            shell=use_shell,
        )
        duration = time.time() - start_time
        stdout = proc.stdout or ""
        stderr = proc.stderr or ""
        exit_code = proc.returncode

        # Redact and truncate output
        combined = f"{stdout}\n{stderr}".strip()
        if len(combined) > MAX_OUTPUT_CHARS:
            combined = combined[:MAX_OUTPUT_CHARS] + "\n... [OUTPUT TRUNCATED]"
        redacted_output = redact_string(combined)

        passed, failed, skipped, error_summary = analyze_test_output(command, exit_code, stdout, stderr)

        state = TestExecutionState.PASSED if exit_code == 0 else TestExecutionState.FAILED

        return TestExecutionResult(
            command=command,
            state=state,
            exit_code=exit_code,
            duration_seconds=duration,
            tests_passed=passed,
            tests_failed=failed,
            tests_skipped=skipped,
            raw_output_redacted=redacted_output,
            error_summary=error_summary,
        )

    except subprocess.TimeoutExpired:
        duration = time.time() - start_time
        return TestExecutionResult(
            command=command,
            state=TestExecutionState.TIMED_OUT,
            exit_code=None,
            duration_seconds=duration,
            tests_passed=None,
            tests_failed=None,
            tests_skipped=None,
            raw_output_redacted=f"Execution timed out after {timeout_seconds} seconds.",
            error_summary=f"Timeout expired ({timeout_seconds}s limit)",
        )
    except Exception as exc:
        duration = time.time() - start_time
        return TestExecutionResult(
            command=command,
            state=TestExecutionState.EXECUTION_ERROR,
            exit_code=None,
            duration_seconds=duration,
            tests_passed=None,
            tests_failed=None,
            tests_skipped=None,
            raw_output_redacted=f"Execution failed with exception: {exc}",
            error_summary=str(exc),
        )

