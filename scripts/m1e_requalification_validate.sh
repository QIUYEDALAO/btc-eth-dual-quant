#!/usr/bin/env bash
set -u
PY_CMD="${PYTHON:-python3}"
export PYTHONPATH="${PYTHONPATH:-.deps:src}"
PASS_COUNT=0; FAIL_COUNT=0; RESULTS=()
run_check() { local name="$1"; shift; echo "==> $name"; if "$@"; then RESULTS+=("PASS $name"); PASS_COUNT=$((PASS_COUNT+1)); else RESULTS+=("FAIL $name"); FAIL_COUNT=$((FAIL_COUNT+1)); fi; }
report_guard() {
  local report="reports/m1/M1E_CANONICAL_5M_REQUALIFICATION_REPORT.md"
  [[ -f "$report" ]] &&
  grep -qE '^- Status: pass$' "$report" &&
  grep -qE '^- Research start: 2020-07-01$' "$report" &&
  grep -qE '^- Unresolved canonical 5m conflicts: 0$' "$report" &&
  grep -qE '^- Canonical incomplete child buckets: 0$' "$report" &&
  grep -qE '^- Freqtrade list-data: pass$' "$report" &&
  grep -qE '^- Metadata-only sample-budget stage authorized: yes$' "$report" &&
  grep -qE '^- Strategy code authorized: no$' "$report" &&
  grep -qE '^- OOS prices/returns accessed: no$' "$report" &&
  grep -qE '^- M2 authorized: no$' "$report"
}
artifact_scan() { [[ -z "$(git ls-files | grep -E '(^|/)\.env($|\.)|^storage/(raw|duckdb|logs)/|^freqtrade_lab/user_data/(data|logs|backtest_results|hyperopt_results)/|\.duckdb$|\.sqlite($|-)' || true)" ]]; }
run_check "M1E source-owner validation" bash scripts/m1e_source_owner_validate.sh
run_check "canonical-5m tests" "$PY_CMD" -m unittest tests/test_m1e_data_qualification.py -v
run_check "compileall" "$PY_CMD" -m compileall src scripts
run_check "requalification report gate" report_guard
run_check "execution/live scan" bash -c '[[ -z "$(find . -path ./src/execution/live -print -o -path ./execution/live -print)" ]]'
run_check "secret scan" "$PY_CMD" scripts/m0_secret_scan.py
run_check "runtime artifact scan" artifact_scan
run_check "git diff --check" git diff --check
echo; echo "M1E requalification validation summary"; for result in "${RESULTS[@]}"; do echo "- $result"; done; echo "PASS=$PASS_COUNT FAIL=$FAIL_COUNT"
[[ "$FAIL_COUNT" -eq 0 ]]
