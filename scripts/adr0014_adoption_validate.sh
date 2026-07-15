#!/usr/bin/env bash
set -u

PY_CMD="${PYTHON:-python3}"
export PYTHONPATH="${PYTHONPATH:-.deps:src:.}"
TARGET_SHA="31c967c785128671769eb713baed265da8ae0f2a"
EVIDENCE_ONLY=false
if [[ "${1:-}" == "--evidence-only" ]]; then
  EVIDENCE_ONLY=true
elif [[ -n "${1:-}" ]]; then
  echo "unknown argument: $1" >&2
  exit 2
fi
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

reviewed_draft_checks() {
  local temp_dir result
  temp_dir="$(mktemp -d)"
  git archive "$TARGET_SHA" | tar -x -C "$temp_dir"
  (
    cd "$temp_dir" || exit 1
    PYTHONPATH="$OLDPWD/.deps:$temp_dir/src:$temp_dir" "$PY_CMD" -m unittest tests.test_adr0014_draft_policy -v
    PYTHONPATH="$OLDPWD/.deps:$temp_dir/src:$temp_dir" "$PY_CMD" scripts/adr0014_draft_policy_check.py
  )
  result=$?
  rm -rf "$temp_dir"
  return "$result"
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
  ! git ls-files | grep -E '(^|/)(storage/(raw|duckdb|logs)|freqtrade_lab/user_data/(data|logs|backtest_results)|.*\.env($|\.)|.*\.sqlite$)'
}

adoption_scope_scan() {
  local changed
  changed="$(git diff --name-only origin/main...)"
  test -z "$(printf '%s\n' "$changed" | grep -E '^(src/|config/|reports/m0/evidence/liquid_universe_v4/)' || true)"
}

run_check "frozen Draft structured checks" reviewed_draft_checks
run_check "ADR-0014 adoption tests" "$PY_CMD" -m unittest tests.test_adr0014_adoption -v
if [[ "$EVIDENCE_ONLY" == true ]]; then
  run_check "ADR-0014 adoption manifest and evidence Gate" "$PY_CMD" scripts/adr0014_adoption_check.py --evidence-only
else
  run_check "ADR-0014 adoption manifest and repository Gate" "$PY_CMD" scripts/adr0014_adoption_check.py
fi
run_check "required-changes review regression" "$PY_CMD" -m unittest tests.test_adr0014_required_changes_review -v
run_check "KLAY adjudication regression" "$PY_CMD" -m unittest tests.test_liquid_universe_v3_klay_conflict -v
run_check "full unit suite" "$PY_CMD" -m unittest discover -s tests -v
run_check "project validation" bash scripts/project_validate.sh
run_check "project context check" "$PY_CMD" scripts/project_context_check.py
run_check "project state transition check" "$PY_CMD" scripts/project_state_transition_check.py
run_check "compileall" "$PY_CMD" -m compileall -q src scripts
run_check "secret scan" "$PY_CMD" scripts/m0_secret_scan.py
run_check "no-trading scan" no_trading_scan
run_check "execution/live scan" execution_scan
run_check "runtime artifact scan" artifact_scan
if [[ "$EVIDENCE_ONLY" == false ]]; then
  run_check "adoption-only changed-path scan" adoption_scope_scan
fi
run_check "git diff --check" git diff --check

echo
echo "ADR-0014 adoption validation summary"
for result in "${RESULTS[@]}"; do echo "- $result"; done
echo "PASS=$PASS_COUNT FAIL=$FAIL_COUNT"
[[ "$FAIL_COUNT" -eq 0 ]]
