#!/usr/bin/env bash
set -u
PY_CMD="${PYTHON:-python3}"
export PYTHONPATH="${PYTHONPATH:-.deps:src}"
PASS_COUNT=0; FAIL_COUNT=0; RESULTS=()
run_check() { local name="$1"; shift; echo "==> $name"; if "$@"; then RESULTS+=("PASS $name"); PASS_COUNT=$((PASS_COUNT+1)); else RESULTS+=("FAIL $name"); FAIL_COUNT=$((FAIL_COUNT+1)); fi; }
report_guard() {
  local report="reports/m1/M1E_BINANCE_SOURCE_OWNER_ESCALATION.md" json="reports/m1/M1E_BINANCE_SOURCE_OWNER_EVIDENCE.json"
  [[ -f "$report" && -f "$json" ]] &&
  grep -qE '^- Status: ready_not_submitted$' "$report" &&
  grep -qE '^- Existing issue overlap rows: 16$' "$report" &&
  grep -qE '^- New supplemental rows: 14$' "$report" &&
  grep -qE '^- Monthly ZIP refetch hashes unchanged: 36/36$' "$report" &&
  grep -qE '^- External submission performed: no$' "$report" &&
  grep -qE '^- Raw payload included: no$' "$report" &&
  grep -qE '^- M1E contract resolved: no$' "$report" &&
  "$PY_CMD" - "$json" <<'PY'
import json, sys
d=json.load(open(sys.argv[1]))
assert d['status']=='ready_not_submitted' and d['supplemental_rows']==14
assert d['external_submission_performed'] is False and d['raw_payload_included'] is False
assert d['api_key_used'] is False and d['m2_authorized'] is False
PY
}
artifact_scan() { [[ -z "$(git ls-files | grep -E '(^|/)\.env($|\.)|^storage/(raw|duckdb|logs)/|^freqtrade_lab/user_data/(data|logs|backtest_results|hyperopt_results)/|\.duckdb$|\.sqlite($|-)' || true)" ]]; }
run_check "M1E conflict validation" bash scripts/m1e_conflict_validate.sh
run_check "source-owner package tests" "$PY_CMD" -m unittest tests/test_m1e_source_owner_package.py -v
run_check "compileall" "$PY_CMD" -m compileall src scripts
run_check "source-owner report gate" report_guard
run_check "execution/live scan" bash -c '[[ -z "$(find . -path ./src/execution/live -print -o -path ./execution/live -print)" ]]'
run_check "secret scan" "$PY_CMD" scripts/m0_secret_scan.py
run_check "runtime artifact scan" artifact_scan
run_check "git diff --check" git diff --check
echo; echo "M1E source-owner validation summary"; for result in "${RESULTS[@]}"; do echo "- $result"; done; echo "PASS=$PASS_COUNT FAIL=$FAIL_COUNT"
[[ "$FAIL_COUNT" -eq 0 ]]
