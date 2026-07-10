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
  local report="reports/m1/M1E_OFFICIAL_SOURCE_CONFLICT_DIAGNOSTICS.md"
  [[ -f "$report" ]] &&
  grep -qE '^- Status: diagnostics_complete_blocker_confirmed$' "$report" &&
  grep -qE '^- Conflict evidence rows: 30$' "$report" &&
  grep -qE '^- Fresh monthly ZIP hashes unchanged: 36/36$' "$report" &&
  grep -qE '^- monthly_daily_conflict_rest_supports_daily: 16$' "$report" &&
  grep -qE '^- higher_timeframe_flow_revision_confirmed_by_rest: 10$' "$report" &&
  grep -qE '^- child_aggregate_flow_confirmed_by_rest: 2$' "$report" &&
  grep -qE '^- unresolved_flow_revision: 2$' "$report" &&
  grep -qE '^- First six-month clean suffix start: 2022-11-01$' "$report" &&
  grep -qE '^- Clean-suffix full calendar: 1338 days$' "$report" &&
  grep -qE '^- Clean-suffix sealed 30% OOS calendar: 402 days$' "$report" &&
  grep -qE '^- Clean suffix sample budget: blocked$' "$report" &&
  grep -qE '^- M1E PR3 sample-budget branch authorized: no$' "$report" &&
  grep -qE '^- M2 authorized: no$' "$report"
}

read_only_scan() {
  local order="order" post="PO""ST" delete_word="DE""LETE" fill="fill" engine="engine"
  local pattern="(/api/v3/${order}|/fapi/v1/${order}|/sapi/v1/margin/${order}|${post}|${delete_word}|place_${order}|cancel_${order}|create_${order}|simulate_${fill}|matching_${engine}|freqtrade[[:space:]]+trade)"
  if command -v rg >/dev/null 2>&1; then ! rg -n "$pattern" src/btc_eth_dual_quant/data/m1e_conflict_diagnostics.py scripts/m1e_diagnose_source_conflicts.py;
  else ! grep -R -n -E "$pattern" src/btc_eth_dual_quant/data/m1e_conflict_diagnostics.py scripts/m1e_diagnose_source_conflicts.py; fi
}

artifact_scan() {
  local tracked
  tracked="$(git ls-files | grep -E '(^|/)\.env($|\.)|^storage/(raw|duckdb|logs)/|^freqtrade_lab/user_data/(data|logs|backtest_results|hyperopt_results)/|\.duckdb$|\.sqlite($|-)|M0_PRIVATE_SMOKE_REPORT\.local\.md$' || true)"
  [[ -z "$tracked" ]] || { printf '%s\n' "$tracked"; return 1; }
}

run_check "M1E data validation" bash scripts/m1e_data_validate.sh
run_check "conflict diagnostic tests" "$PY_CMD" -m unittest tests/test_m1e_conflict_diagnostics.py -v
run_check "compileall" "$PY_CMD" -m compileall src scripts
run_check "conflict report gate" report_guard
run_check "read-only/no-trading scan" read_only_scan
run_check "execution/live scan" bash -c '[[ -z "$(find . -path ./src/execution/live -print -o -path ./execution/live -print)" ]]'
run_check "secret scan" "$PY_CMD" scripts/m0_secret_scan.py
run_check "runtime artifact scan" artifact_scan
run_check "git diff --check" git diff --check

echo
echo "M1E conflict validation summary"
for result in "${RESULTS[@]}"; do echo "- $result"; done
echo "PASS=$PASS_COUNT FAIL=$FAIL_COUNT"
[[ "$FAIL_COUNT" -eq 0 ]]
