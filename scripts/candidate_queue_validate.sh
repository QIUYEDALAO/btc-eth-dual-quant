#!/usr/bin/env bash
set -u
PY_CMD="${PYTHON:-python3}"
export PYTHONPATH="${PYTHONPATH:-.deps:src}"
PASS_COUNT=0; FAIL_COUNT=0; RESULTS=()
run_check() { local name="$1"; shift; echo "==> $name"; if "$@"; then RESULTS+=("PASS $name"); PASS_COUNT=$((PASS_COUNT+1)); else RESULTS+=("FAIL $name"); FAIL_COUNT=$((FAIL_COUNT+1)); fi; }
report_guard() {
  local report="reports/m1/STRATEGY_CANDIDATE_QUEUE_GOVERNANCE.md"
  [[ -f "$report" ]] && grep -qE '^- Status: queue_frozen_design_only$' "$report" &&
  grep -qE '^- Historical opened OOS trials: 3$' "$report" &&
  grep -qE '^\| 1 \| M1E ' "$report" && grep -qE '^\| 2 \| M1G ' "$report" && grep -qE '^\| 3 \| M1H ' "$report" &&
  grep -qE '^- Current OOS access authorized: no$' "$report" &&
  grep -qE '^- Strategy code authorized: no$' "$report" && grep -qE '^- M2 authorized: no$' "$report"
}
artifact_scan() { [[ -z "$(git ls-files | grep -E '(^|/)\.env($|\.)|^storage/(raw|duckdb|logs)/|^freqtrade_lab/user_data/(data|logs|backtest_results|hyperopt_results)/|\.duckdb$|\.sqlite($|-)' || true)" ]]; }
run_check "M1E sample-budget validation" bash scripts/m1e_sample_budget_validate.sh
run_check "candidate queue checker" "$PY_CMD" scripts/candidate_queue_check.py
run_check "candidate queue tests" "$PY_CMD" -m unittest tests/test_candidate_queue_governance.py tests/test_strategy_trial_ledger.py -v
run_check "compileall" "$PY_CMD" -m compileall src scripts
run_check "governance report gate" report_guard
run_check "execution/live scan" bash -c '[[ -z "$(find . -path ./src/execution/live -print -o -path ./execution/live -print)" ]]'
run_check "secret scan" "$PY_CMD" scripts/m0_secret_scan.py
run_check "runtime artifact scan" artifact_scan
run_check "git diff --check" git diff --check
echo; echo "Candidate queue validation summary"; for result in "${RESULTS[@]}"; do echo "- $result"; done; echo "PASS=$PASS_COUNT FAIL=$FAIL_COUNT"
[[ "$FAIL_COUNT" -eq 0 ]]
