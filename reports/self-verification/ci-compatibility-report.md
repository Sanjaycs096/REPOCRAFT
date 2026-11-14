# RepoCraft — Cross-Platform CI & Runner Compatibility Report

## 1. Operating System & Python Matrix

| Operating System | Python Version | Runner Image | UTF-8 Mode | Status | Notes |
| :--- | :---: | :--- | :---: | :---: | :--- |
| Linux (Ubuntu) | 3.9 | `ubuntu-22.04` | Yes | **PASS** | Explicit LTS image (Ubuntu 26.04 removed Python 3.9 toolcache) |
| Linux (Ubuntu) | 3.10 | `ubuntu-latest` | Yes | **PASS** | Validated |
| Linux (Ubuntu) | 3.11 | `ubuntu-latest` | Yes | **PASS** | Validated |
| Linux (Ubuntu) | 3.12 | `ubuntu-latest` | Yes | **PASS** | Validated |
| Windows | 3.9 | `windows-latest` | Yes | **PASS** | Protected by stream reconfigure & safe print |
| Windows | 3.10 | `windows-latest` | Yes | **PASS** | Protected by stream reconfigure & safe print |
| Windows | 3.11 | `windows-latest` | Yes | **PASS** | Protected by stream reconfigure & safe print |
| Windows | 3.12 | `windows-latest` | Yes | **PASS** | Protected by stream reconfigure & safe print |

## 2. Encoding Resiliency & Root Cause Analysis

- **Historical CI Failure:** Windows default console encoding (`cp1252`) raised `UnicodeEncodeError` when printing emojis or unicode paths in `install.py` and `repocraft_status.py`.
- **Resolution Applied:** Implemented stream reconfiguration to UTF-8 with replacement (`sys.stdout.reconfigure`), fallback ASCII-safe symbols (`[READY]`, `[PASS]`, `[FAIL]`), and `safe_print` across all CLI drivers.
- **Regression Verification:** Dedicated regression suite (`tests/integration/test_encoding_resiliency.py`) passes 100% under forced `PYTHONIOENCODING=cp1252`.

## 3. macOS CI Status Calibration

- macOS is **not** currently included in the GitHub Actions matrix to conserve runner minutes and avoid flaky ARM/x86 cache discrepancies.
- Documentation has been audited and calibrated to state that automated CI runs on Linux (Ubuntu) and Windows, with POSIX/macOS compatibility supported via standard Python libraries.