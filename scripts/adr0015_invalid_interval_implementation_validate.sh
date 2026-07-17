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

no_trading_scan() {
  local order_word="ord""er" fill_word="fi""ll" engine_word="eng""ine"
  local pattern="(/api/v3/${order_word}|/fapi/v1/${order_word}|/sapi/v1/margin/${order_word}|place_${order_word}|cancel_${order_word}|create_${order_word}|simulate_${fill_word}|matching_${engine_word})"
  test -z "$(rg -n "$pattern" src scripts || true)"
}

execution_scan() {
  [[ ! -e src/execution/live && ! -e execution/live ]]
}

changed_paths() {
  {
    git diff --name-only origin/main
    git ls-files --others --exclude-standard | rg -v '(^|/)[^/]+\.egg-info/' || true
  } | sort -u
}

artifact_scan() {
  ! {
    git ls-files
    git ls-files --others --exclude-standard
  } | rg '(^|/)(storage/(raw|duckdb|logs)|freqtrade_lab/user_data/(data|logs|backtest_results)|.*\.env($|\.)|.*\.sqlite$)'
}

scope_scan() {
  local changed invalid
  changed="$(changed_paths)"
  invalid="$(printf '%s\n' "$changed" | rg -v '^(AGENTS\.md|NEXT_ACTION\.md|PROJECT_EXECUTION_CHECKLIST\.md|PROJECT_LEDGER\.md|PROJECT_STATE\.yaml|reports/INDEX\.md|config/liquid_spot_invalid_interval_policy_v1\.json|reports/m0/ADR_0015_INVALID_INTERVAL_POLICY_IMPLEMENTATION_STATUS\.md|src/btc_eth_dual_quant/data/invalid_interval_quarantine\.py|scripts/liquid_universe_v4_public_run\.py|scripts/adr0015_invalid_interval_implementation_(check\.py|validate\.sh)|scripts/project_state_transition_check\.py|tests/test_adr0015_invalid_interval_policy\.py|tests/test_liquid_universe_v3_klay_conflict\.py)$' || true)"
  test -z "$invalid"
}

frozen_evidence_scan() {
  test -z "$(changed_paths | rg '^(docs/decisions/proposals/adr0015_invalid_interval_policy_model\.json|config/liquid_spot_(universe_contract_v4|lifecycle_policy_v4|lifecycle_event_resolutions_v4)\.json|reports/m0/evidence/|storage/raw/)' || true)"
}

run_check "ADR-0015 implementation tests and fault injection" "$PY_CMD" -m unittest tests.test_adr0015_invalid_interval_policy -v
run_check "V4 production-path regressions" "$PY_CMD" -m unittest tests.test_liquid_universe_v4_public_run tests.test_u03f_v4_repair_implementation -v
run_check "ADR-0015 implementation checker" "$PY_CMD" scripts/adr0015_invalid_interval_implementation_check.py
run_check "ADR-0015 adoption regression" "$PY_CMD" -m unittest tests.test_adr0015_adoption -v
run_check "ADR-0015 adoption frozen evidence" "$PY_CMD" scripts/adr0015_adoption_check.py --evidence-only
run_check "ADR-0015 independent-review regression" "$PY_CMD" -m unittest tests.test_adr0015_independent_review -v
run_check "ADR-0015 Draft regression" "$PY_CMD" scripts/adr0015_policy_draft_check.py
run_check "full unit suite" "$PY_CMD" -m unittest discover -s tests -v
run_check "project validation" bash scripts/project_validate.sh
run_check "project context check" "$PY_CMD" scripts/project_context_check.py
run_check "project state transition check" "$PY_CMD" scripts/project_state_transition_check.py
run_check "compileall" "$PY_CMD" -m compileall -q src scripts
run_check "secret scan" "$PY_CMD" scripts/m0_secret_scan.py
run_check "no-trading scan" no_trading_scan
run_check "execution/live scan" execution_scan
run_check "runtime artifact scan" artifact_scan
run_check "implementation-only changed-path scan" scope_scan
run_check "frozen evidence immutability scan" frozen_evidence_scan
run_check "git diff --check" git diff --check

echo
echo "ADR-0015 invalid-interval implementation validation summary"
for result in "${RESULTS[@]}"; do echo "- $result"; done
echo "PASS=$PASS_COUNT FAIL=$FAIL_COUNT"
[[ "$FAIL_COUNT" -eq 0 ]]
