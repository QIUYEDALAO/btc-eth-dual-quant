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

artifact_scan() {
  ! git ls-files | grep -E '(^|/)(storage/(raw|duckdb|logs)|freqtrade_lab/user_data/(data|logs|backtest_results)|.*\.env($|\.)|.*\.sqlite$)'
}

execution_scan() {
  [[ ! -e src/execution/live && ! -e execution/live ]]
}

run_check "ADR-0013 conformance" "$PY_CMD" scripts/adr0013_conformance_check.py
run_check "V3 contract and registry" "$PY_CMD" scripts/liquid_universe_v3_contract_check.py
run_check "V3 conflict-policy tests" "$PY_CMD" -m unittest \
  tests.test_liquid_universe_v3_conflict_policy \
  tests.test_liquid_universe_v3_resolution_registry \
  tests.test_liquid_universe_v3_end_to_end \
  tests.test_liquid_universe_v3_fault_injection -v
run_check "V2 source-conflict regression" "$PY_CMD" -m unittest \
  tests.test_liquid_universe_v2_source_conflicts \
  tests.test_liquid_universe_v2_requalification -v
run_check "compileall" "$PY_CMD" -m compileall -q src scripts
run_check "project validation" bash scripts/project_validate.sh
run_check "secret scan" "$PY_CMD" scripts/m0_secret_scan.py
run_check "execution/live scan" execution_scan
run_check "runtime artifact scan" artifact_scan
run_check "git diff --check" git diff --check

echo
echo "Liquid universe V3 policy validation summary"
for result in "${RESULTS[@]}"; do echo "- $result"; done
echo "PASS=$PASS_COUNT FAIL=$FAIL_COUNT"
[[ "$FAIL_COUNT" -eq 0 ]]
