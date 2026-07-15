#!/usr/bin/env bash
set -u

PY_CMD="${PYTHON:-python3}"
export PYTHONPATH="${PYTHONPATH:-.deps:src:.}"
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

no_trading_scan() {
  local order_word="ord""er"
  local fill_word="fi""ll"
  local engine_word="eng""ine"
  local pattern="(/api/v3/${order_word}|/fapi/v1/${order_word}|/sapi/v1/margin/${order_word}|place_${order_word}|cancel_${order_word}|create_${order_word}|simulate_${fill_word}|matching_${engine_word})"
  if command -v rg >/dev/null 2>&1; then
    test -z "$(rg -n "$pattern" src scripts || true)"
  else
    test -z "$(grep -R -n -E "$pattern" src scripts || true)"
  fi
}

run_check "V3 blocked requalification regression" bash scripts/liquid_universe_v3_requalification_validate.sh
run_check "KLAY adjudication tests" "$PY_CMD" -m unittest tests.test_liquid_universe_v3_klay_conflict -v
run_check "ADR-0013 and V3 policy tests" "$PY_CMD" -m unittest \
  tests.test_adr0013_draft_policy \
  tests.test_adr0013_independent_review \
  tests.test_liquid_universe_v3_conflict_policy \
  tests.test_liquid_universe_v3_resolution_registry \
  tests.test_liquid_universe_v3_fault_injection \
  tests.test_liquid_universe_v3_requalification -v
run_check "KLAY offline evidence and immutable baselines" "$PY_CMD" scripts/liquid_universe_v3_klay_conflict_check.py
run_check "full unit suite" "$PY_CMD" -m unittest discover -s tests -v
run_check "project validation" bash scripts/project_validate.sh
run_check "project context check" "$PY_CMD" scripts/project_context_check.py
run_check "project state transition check" "$PY_CMD" scripts/project_state_transition_check.py
run_check "V3 contract and registry check" "$PY_CMD" scripts/liquid_universe_v3_contract_check.py
run_check "compileall" "$PY_CMD" -m compileall -q src scripts
run_check "secret scan" "$PY_CMD" scripts/m0_secret_scan.py
run_check "no-trading scan" no_trading_scan
run_check "execution/live scan" execution_scan
run_check "runtime artifact scan" artifact_scan
run_check "git diff --check" git diff --check

echo
echo "Liquid universe V3 KLAY conflict validation summary"
for result in "${RESULTS[@]}"; do echo "- $result"; done
echo "PASS=$PASS_COUNT FAIL=$FAIL_COUNT"
[[ "$FAIL_COUNT" -eq 0 ]]
