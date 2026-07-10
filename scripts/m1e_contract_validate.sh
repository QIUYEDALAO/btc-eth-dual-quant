#!/usr/bin/env bash
set -u

PY_CMD="${PYTHON:-python3}"
export PYTHONPATH="${PYTHONPATH:-.deps:src}"
PASS_COUNT=0
FAIL_COUNT=0
RESULTS=()

run_check() {
  local name="$1"
  shift
  echo "==> $name"
  if "$@"; then
    RESULTS+=("PASS $name")
    PASS_COUNT=$((PASS_COUNT + 1))
  else
    RESULTS+=("FAIL $name")
    FAIL_COUNT=$((FAIL_COUNT + 1))
  fi
}

report_guard() {
  local report="reports/m1/M1E_1H_PRODUCT_DATA_CONTRACT.md"
  [[ -f "$report" ]] &&
  grep -qE '^- Status: design_contract_pass$' "$report" &&
  grep -qE '^- Candidate evaluated: no$' "$report" &&
  grep -qE '^- OOS opened: no$' "$report" &&
  grep -qE '^- Strategy code authorized: no$' "$report" &&
  grep -qE '^- Freqtrade backtesting authorized: no$' "$report" &&
  grep -qE '^- M2 authorized: no$' "$report"
}

read_only_scan() {
  local order="order" post="PO""ST" delete_word="DE""LETE" fill="fill" engine="engine"
  local pattern="(/api/v3/${order}|/fapi/v1/${order}|/sapi/v1/margin/${order}|${post}|${delete_word}|place_${order}|cancel_${order}|create_${order}|simulate_${fill}|matching_${engine}|freqtrade[[:space:]]+trade)"
  if command -v rg >/dev/null 2>&1; then
    ! rg -n "$pattern" scripts/m1e_*.py config/m1e_*.json
  else
    ! grep -R -n -E "$pattern" scripts/m1e_*.py config/m1e_*.json
  fi
}

artifact_scan() {
  local tracked
  tracked="$(git ls-files | grep -E '(^|/)\.env($|\.)|^storage/(raw|duckdb|logs)/|^freqtrade_lab/user_data/(data|logs|backtest_results|hyperopt_results)/|\.duckdb$|\.sqlite($|-)|M0_PRIVATE_SMOKE_REPORT\.local\.md$' || true)"
  [[ -z "$tracked" ]] || { printf '%s\n' "$tracked"; return 1; }
}

run_check "T5 validation" bash scripts/t5_validate.sh
run_check "M1E contract tests" "$PY_CMD" -m unittest tests/test_m1e_contract.py -v
run_check "M1E contract check" "$PY_CMD" scripts/m1e_contract_check.py
run_check "compileall" "$PY_CMD" -m compileall src scripts
run_check "M1E contract report gate" report_guard
run_check "read-only/no-trading scan" read_only_scan
run_check "execution/live scan" bash -c '[[ -z "$(find . -path ./src/execution/live -print -o -path ./execution/live -print)" ]]'
run_check "secret scan" "$PY_CMD" scripts/m0_secret_scan.py
run_check "runtime artifact scan" artifact_scan
run_check "git diff --check" git diff --check

echo
echo "M1E contract validation summary"
for result in "${RESULTS[@]}"; do echo "- $result"; done
echo "PASS=$PASS_COUNT FAIL=$FAIL_COUNT"
[[ "$FAIL_COUNT" -eq 0 ]]
