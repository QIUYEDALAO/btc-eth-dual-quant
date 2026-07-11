#!/usr/bin/env bash
set -u
PY_CMD="${PYTHON:-python3}"
export PYTHONPATH="${PYTHONPATH:-.deps:src}"
PASS_COUNT=0; FAIL_COUNT=0; RESULTS=()
run_check() { local name="$1"; shift; echo "==> $name"; if "$@"; then RESULTS+=("PASS $name"); PASS_COUNT=$((PASS_COUNT+1)); else RESULTS+=("FAIL $name"); FAIL_COUNT=$((FAIL_COUNT+1)); fi; }
report_guard() { grep -qE '^- Status: implementation_pass_no_performance_run$' reports/m1/M1G_IMPLEMENTATION_STATUS.md && grep -qE '^- Performance backtest executed: no$' reports/m1/M1G_IMPLEMENTATION_STATUS.md && grep -qE '^- OOS opened: no$' reports/m1/M1G_IMPLEMENTATION_STATUS.md; }
read_only_scan() { local order="order" post="PO""ST" delete_word="DE""LETE" fill="fill" engine="engine"; local pattern="(/api/v3/${order}|/fapi/v1/${order}|/sapi/v1/margin/${order}|${post}|${delete_word}|place_${order}|cancel_${order}|create_${order}|simulate_${fill}|matching_${engine}|freqtrade[[:space:]]+trade)"; if command -v rg >/dev/null 2>&1; then ! rg -n "$pattern" src scripts freqtrade_lab/scripts freqtrade_lab/user_data/strategies; else ! grep -R -n -E --exclude-dir=__pycache__ --binary-files=without-match "$pattern" src scripts freqtrade_lab/scripts freqtrade_lab/user_data/strategies; fi; }
artifact_scan() { local tracked; tracked="$(git ls-files | grep -E '(^|/)\.env($|\.)|^storage/(raw|duckdb|logs)/|^freqtrade_lab/user_data/(data|logs|backtest_results|hyperopt_results)/|\.duckdb$|\.sqlite($|-)|M0_PRIVATE_SMOKE_REPORT\.local\.md$' || true)"; [[ -z "$tracked" ]] || { printf '%s\n' "$tracked"; return 1; }; }
run_check "M1G capability validation" bash scripts/m1g_freqtrade_capability_validate.sh
run_check "M1G strategy and audit tests" "$PY_CMD" -m unittest tests.test_m1g_freqtrade_strategy -v
run_check "M1G implementation check" "$PY_CMD" scripts/m1g_implementation_check.py
run_check "M1G pinned runtime evidence" "$PY_CMD" scripts/m1g_runtime_evidence_check.py
run_check "compileall" "$PY_CMD" -m compileall src scripts freqtrade_lab/user_data/strategies
run_check "implementation report gate" report_guard
run_check "read-only scan" read_only_scan
run_check "execution/live scan" bash -c '[[ -z "$(find . -path ./src/execution/live -print -o -path ./execution/live -print)" ]]'
run_check "secret scan" "$PY_CMD" scripts/m0_secret_scan.py
run_check "runtime artifact scan" artifact_scan
run_check "git diff --check" git diff --check
echo; echo "M1G implementation validation summary"; for result in "${RESULTS[@]}"; do echo "- $result"; done; echo "PASS=$PASS_COUNT FAIL=$FAIL_COUNT"; [[ "$FAIL_COUNT" -eq 0 ]]
