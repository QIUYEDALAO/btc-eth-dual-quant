#!/usr/bin/env bash
set -u

PY_CMD="${PYTHON:-python3}"
export PYTHONPATH="${PYTHONPATH:-.deps:src}"
PASS_COUNT=0
FAIL_COUNT=0
RESULTS=()

run_check() {
  local name="$1"; shift
  echo "==> $name"
  if "$@"; then RESULTS+=("PASS $name"); PASS_COUNT=$((PASS_COUNT + 1));
  else RESULTS+=("FAIL $name"); FAIL_COUNT=$((FAIL_COUNT + 1)); fi
}

report_guard() {
  local report="reports/m1/M1E_1H_DATA_QUALIFICATION_REPORT.md"
  [[ -f "$report" ]] &&
  grep -qE '^- Status: blocked$' "$report" &&
  grep -qE '^- Research start: 2020-07-01$' "$report" &&
  grep -qE '^- Candidate evaluated: no$' "$report" &&
  grep -qE '^- OOS prices/returns accessed: no$' "$report" &&
  grep -qE '^- Freqtrade backtesting run: no$' "$report" &&
  grep -qE '^- Freqtrade list-data: pass$' "$report" &&
  grep -qE '^- Sample-budget stage authorized: no$' "$report" &&
  grep -qE '^\| 2021-01 \|' "$report" &&
  grep -qE '^\| 2022-04 \|' "$report" &&
  grep -qE '^- M2 authorized: no$' "$report"
}

read_only_scan() {
  local order="order" post="PO""ST" delete_word="DE""LETE" fill="fill" engine="engine"
  local pattern="(/api/v3/${order}|/fapi/v1/${order}|/sapi/v1/margin/${order}|${post}|${delete_word}|place_${order}|cancel_${order}|create_${order}|simulate_${fill}|matching_${engine}|freqtrade[[:space:]]+trade)"
  if command -v rg >/dev/null 2>&1; then ! rg -n "$pattern" src/btc_eth_dual_quant/data/m1e_qualification.py scripts/m1e_*.py;
  else ! grep -R -n -E "$pattern" src/btc_eth_dual_quant/data/m1e_qualification.py scripts/m1e_*.py; fi
}

artifact_scan() {
  local tracked
  tracked="$(git ls-files | grep -E '(^|/)\.env($|\.)|^storage/(raw|duckdb|logs)/|^freqtrade_lab/user_data/(data|logs|backtest_results|hyperopt_results)/|\.duckdb$|\.sqlite($|-)|M0_PRIVATE_SMOKE_REPORT\.local\.md$' || true)"
  [[ -z "$tracked" ]] || { printf '%s\n' "$tracked"; return 1; }
}

run_check "M1E contract validation" bash scripts/m1e_contract_validate.sh
run_check "M1E data unit tests" "$PY_CMD" -m unittest tests/test_m1e_data_qualification.py -v
run_check "compileall" "$PY_CMD" -m compileall src scripts
run_check "M1E data report gate" report_guard
run_check "read-only/no-trading scan" read_only_scan
run_check "execution/live scan" bash -c '[[ -z "$(find . -path ./src/execution/live -print -o -path ./execution/live -print)" ]]'
run_check "secret scan" "$PY_CMD" scripts/m0_secret_scan.py
run_check "runtime artifact scan" artifact_scan
run_check "git diff --check" git diff --check

echo
echo "M1E data validation summary"
for result in "${RESULTS[@]}"; do echo "- $result"; done
echo "PASS=$PASS_COUNT FAIL=$FAIL_COUNT"
[[ "$FAIL_COUNT" -eq 0 ]]
