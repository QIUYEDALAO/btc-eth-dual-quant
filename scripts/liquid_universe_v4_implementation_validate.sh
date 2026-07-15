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

report_gate() {
  local report="reports/m0/LIQUID_SPOT_UNIVERSE_V4_IMPLEMENTATION_STATUS.md"
  grep -Fq -- '- Status: `implementation_pass_fixture_only_public_requalification_not_run`' "$report" &&
    grep -Fq -- '- Real public requalification run: no' "$report" &&
    grep -Fq -- '- V4 active qualification authority: no' "$report" &&
    grep -Fq -- '- U-03F authorized: no' "$report" &&
    grep -Fq -- '- U-04 authorized: no' "$report"
}

no_trading_scan() {
  local order_word="ord""er" fill_word="fi""ll" engine_word="eng""ine"
  local pattern="(/api/v3/${order_word}|/fapi/v1/${order_word}|/sapi/v1/margin/${order_word}|place_${order_word}|cancel_${order_word}|create_${order_word}|simulate_${fill_word}|matching_${engine_word})"
  if command -v rg >/dev/null 2>&1; then
    test -z "$(rg -n "$pattern" src scripts || true)"
  else
    test -z "$(grep -R -n -E "$pattern" src scripts || true)"
  fi
}

execution_scan() {
  [[ ! -e src/execution/live && ! -e execution/live ]]
}

artifact_scan() {
  ! git ls-files | grep -E '(^|/)(storage/(raw|duckdb|logs)|freqtrade_lab/user_data/(data|logs|backtest_results)|reports/m0/evidence/liquid_universe_v4|.*\.env($|\.)|.*\.sqlite$)'
}

implementation_scope_scan() {
  local changed invalid
  changed="$(git diff --name-only origin/main...)"
  invalid="$(printf '%s\n' "$changed" | grep -Ev '^(AGENTS\.md|NEXT_ACTION\.md|PROJECT_EXECUTION_CHECKLIST\.md|PROJECT_LEDGER\.md|PROJECT_STATE\.yaml|reports/INDEX\.md|reports/m0/LIQUID_SPOT_UNIVERSE_V4_IMPLEMENTATION_STATUS\.md|config/liquid_spot_(universe_contract_v4|lifecycle_policy_v4|lifecycle_event_resolutions_v4)\.json|src/btc_eth_dual_quant/data/(lifecycle_availability|lifecycle_artifacts|liquid_universe_pipeline_v4)\.py|scripts/(adr0014_adoption_check|project_state_transition_check|liquid_universe_v4_contract_check)\.py|scripts/(adr0014_adoption_validate|liquid_universe_v4_implementation_validate)\.sh|tests/(v4_lifecycle_fixtures|test_adr0014_adoption|test_liquid_universe_v4_[a-z_]+|test_liquid_universe_state_machine|test_liquid_universe_v3_klay_conflict)\.py|\.github/workflows/(adr0014-adoption|liquid-universe-v4-implementation)\.yml)$' || true)"
  test -z "$invalid"
}

run_check "ADR-0014 adoption regression" "$PY_CMD" -m unittest tests.test_adr0014_adoption -v
run_check "ADR-0014 adoption evidence Gate" "$PY_CMD" scripts/adr0014_adoption_check.py --evidence-only
run_check "V3 contract regression" "$PY_CMD" scripts/liquid_universe_v3_contract_check.py
run_check "KLAY adjudication regression" "$PY_CMD" -m unittest tests.test_liquid_universe_v3_klay_conflict -v
run_check "V4 lifecycle tests and fault matrix" "$PY_CMD" -m unittest discover -s tests -p 'test_liquid_universe_v4_*.py' -v
run_check "V4 contract policy registry Gate" "$PY_CMD" scripts/liquid_universe_v4_contract_check.py
run_check "V4 implementation report Gate" report_gate
run_check "full unit suite" "$PY_CMD" -m unittest discover -s tests -v
run_check "project validation" bash scripts/project_validate.sh
run_check "project context check" "$PY_CMD" scripts/project_context_check.py
run_check "project state transition check" "$PY_CMD" scripts/project_state_transition_check.py
run_check "compileall" "$PY_CMD" -m compileall -q src scripts
run_check "secret scan" "$PY_CMD" scripts/m0_secret_scan.py
run_check "no-trading scan" no_trading_scan
run_check "execution/live scan" execution_scan
run_check "runtime and public-run artifact scan" artifact_scan
run_check "implementation-only changed-path scan" implementation_scope_scan
run_check "git diff --check" git diff --check

echo
echo "Liquid universe V4 implementation validation summary"
for result in "${RESULTS[@]}"; do echo "- $result"; done
echo "PASS=$PASS_COUNT FAIL=$FAIL_COUNT"
[[ "$FAIL_COUNT" -eq 0 ]]
