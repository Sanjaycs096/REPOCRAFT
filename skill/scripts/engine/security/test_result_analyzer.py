"""Module H — Test Result Analyzer for RepoCraft Phase 3.

Parses test runner stdout/stderr to extract:
- Passed test count
- Failed test count
- Skipped / ignored test count
- Error summary
- Output sanitization / redaction
"""
from __future__ import annotations

import re
from typing import Optional, Tuple

from .secret_scanner import redact_string


def analyze_test_output(
    command: str, exit_code: int, stdout: str, stderr: str
) -> Tuple[Optional[int], Optional[int], Optional[int], Optional[str]]:
    """Parse output from supported test runners.

    Returns:
        (passed, failed, skipped, error_summary)
    """
    combined = f"{stdout}\n{stderr}"
    passed: Optional[int] = None
    failed: Optional[int] = None
    skipped: Optional[int] = None
    error_summary: Optional[str] = None

    # Pytest parser: e.g. "== 5 passed, 1 failed, 2 skipped in 0.12s =="
    # or "== 10 passed in 0.05s =="
    pytest_match = re.search(r"=+\s*(.*?)\s+in\s+[\d\.]+s\s*=+", combined)
    if pytest_match:
        summary_str = pytest_match.group(1)
        p_m = re.search(r"(\d+)\s+passed", summary_str)
        f_m = re.search(r"(\d+)\s+failed", summary_str)
        s_m = re.search(r"(\d+)\s+skipped", summary_str)
        if p_m:
            passed = int(p_m.group(1))
        if f_m:
            failed = int(f_m.group(1))
        if s_m:
            skipped = int(s_m.group(1))

    # Unittest parser: e.g. "Ran 12 tests in 0.005s\n\nOK" or "FAILED (failures=1, errors=1)"
    if passed is None and "Ran " in combined:
        ran_m = re.search(r"Ran\s+(\d+)\s+tests?", combined)
        if ran_m:
            total = int(ran_m.group(1))
            fail_m = re.search(r"failures=(\d+)", combined)
            err_m = re.search(r"errors=(\d+)", combined)
            skip_m = re.search(r"skipped=(\d+)", combined)

            f_count = (int(fail_m.group(1)) if fail_m else 0) + (int(err_m.group(1)) if err_m else 0)
            s_count = int(skip_m.group(1)) if skip_m else 0

            failed = f_count
            skipped = s_count
            passed = max(0, total - f_count - s_count)

    # Jest / Vitest parser: "Tests: 2 failed, 1 skipped, 5 passed, 8 total"
    jest_match = re.search(r"Tests:\s*(.*)", combined)
    if jest_match:
        j_str = jest_match.group(1)
        p_m = re.search(r"(\d+)\s+passed", j_str)
        f_m = re.search(r"(\d+)\s+failed", j_str)
        s_m = re.search(r"(\d+)\s+(?:skipped|todo)", j_str)
        if p_m:
            passed = int(p_m.group(1))
        if f_m:
            failed = int(f_m.group(1))
        if s_m:
            skipped = int(s_m.group(1))

    # Go test parser: e.g. "PASS" or "FAIL"
    if passed is None:
        if re.search(r"^PASS\b", combined, re.MULTILINE):
            passed = 1 if exit_code == 0 else 0
            failed = 0 if exit_code == 0 else 1
        elif re.search(r"^FAIL\b", combined, re.MULTILINE):
            failed = 1
            passed = 0

    # Cargo test parser: "test result: ok. 5 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out"
    cargo_match = re.search(
        r"test result:\s*\w+\.\s*(\d+)\s+passed;\s*(\d+)\s+failed;\s*(\d+)\s+ignored",
        combined,
    )
    if cargo_match:
        passed = int(cargo_match.group(1))
        failed = int(cargo_match.group(2))
        skipped = int(cargo_match.group(3))

    # Extract short error summary if failed
    if exit_code != 0:
        error_lines = []
        for line in reversed(combined.splitlines()):
            s = line.strip()
            if s and not s.startswith("="):
                error_lines.append(s)
                if len(error_lines) >= 3:
                    break
        if error_lines:
            error_summary = redact_string("; ".join(reversed(error_lines))[:200])

    return passed, failed, skipped, error_summary

