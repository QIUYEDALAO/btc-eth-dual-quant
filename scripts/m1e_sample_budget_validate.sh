#!/usr/bin/env bash
set -u
PY_CMD="${PYTHON:-python3}"
export PYTHONPATH="${PYTHONPATH:-.deps:src}"
PASS_COUNT=0; FAIL_COUNT=0; RESULTS=()
run_check() { local name="$1"; shift; echo "==> $name"; if "$@"; then RESULTS+=("PASS $name"); PASS_COUNT=$((PASS_COUNT+1)); else RESULTS+=("FAIL $name"); FAIL_COUNT=$((FAIL_COUNT+1)); fi; }
report_guard() {
  local report="reports/m1/M1E_1H_SAMPLE_BUDGET_REPORT.md"
  [[ -f "$report" ]] &&
  grep -qE '^- Status: sample_budget_pass_design_only$' "$report" &&
  grep -qE '^\| Full history \| 2191 days \| pass \|$' "$report" &&
  grep -qE '^\| IS \| 1533 days \| diagnostic \|$' "$report" &&
  grep -qE '^\| Sealed OOS start \| 2024-09-11 \| frozen split \|$' "$report" &&
  grep -qE '^\| Sealed OOS \| 658 days \| pass \|$' "$report" &&
  grep -qE '^- OOS prices/returns accessed: no$' "$report" &&
  grep -qE '^- IS-only design review authorized: yes$' "$report" &&
  grep -qE '^- Strategy code authorized: no$' "$report" &&
  grep -qE '^- Freqtrade backtesting authorized: no$' "$report" &&
  grep -qE '^- M2 authorized: no$' "$report"
}
artifact_scan() { [[ -z "$(git ls-files | grep -E '(^|/)\.env($|\.)|^storage/(raw|duckdb|logs)/|^freqtrade_lab/user_data/(data|logs|backtest_results|hyperopt_results)/|\.duckdb$|\.sqlite($|-)' || true)" ]]; }
run_check "M1E requalification validation" bash scripts/m1e_requalification_validate.sh
run_check "M1E sample-budget tests" "$PY_CMD" -m unittest tests/test_m1e_sample_budget.py tests/test_t5_sample_budget.py -v
run_check "compileall" "$PY_CMD" -m compileall src scripts
run_check "sample-budget report gate" report_guard
run_check "execution/live scan" bash -c '[[ -z "$(find . -path ./src/execution/live -print -o -path ./execution/live -print)" ]]'
run_check "secret scan" "$PY_CMD" scripts/m0_secret_scan.py
run_check "runtime artifact scan" artifact_scan
run_check "git diff --check" git diff --check
echo; echo "M1E sample-budget validation summary"; for result in "${RESULTS[@]}"; do echo "- $result"; done; echo "PASS=$PASS_COUNT FAIL=$FAIL_COUNT"
[[ "$FAIL_COUNT" -eq 0 ]]
