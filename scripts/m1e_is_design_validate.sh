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

report_guard() {
  grep -qE '^- Status: economic_hypothesis_pass_isolation_only$' reports/m1/M1E_IS_ONLY_RULE_DESIGN.md &&
  grep -qE '^- Candidate evaluated: no$' reports/m1/M1E_IS_ONLY_RULE_DESIGN.md &&
  grep -qE '^- Formal strategy returns computed: no$' reports/m1/M1E_IS_ONLY_RULE_DESIGN.md &&
  grep -qE '^- OOS opened: no$' reports/m1/M1E_IS_ONLY_RULE_DESIGN.md &&
  grep -qE '^- Status: pass$' reports/m1/M1E_NON_DUPLICATION_REVIEW.md &&
  grep -qE '^- M1A rescue attempted: no$' reports/m1/M1E_NON_DUPLICATION_REVIEW.md
}

artifact_scan() {
  local tracked
  tracked="$(git ls-files | grep -E '(^|/)\.env($|\.)|^storage/(raw|duckdb|logs)/|^freqtrade_lab/user_data/(data|logs|backtest_results|hyperopt_results)/|\.duckdb$|\.sqlite($|-)|M0_PRIVATE_SMOKE_REPORT\.local\.md$' || true)"
  [[ -z "$tracked" ]] || { printf '%s\n' "$tracked"; return 1; }
}

run_check "candidate queue validation" bash scripts/candidate_queue_validate.sh
run_check "M1E IS design tests" "$PY_CMD" -m unittest tests/test_m1e_is_design.py -v
run_check "M1E IS design check" "$PY_CMD" scripts/m1e_is_design_check.py
run_check "compileall" "$PY_CMD" -m compileall src scripts
run_check "M1E IS design report gate" report_guard
run_check "execution/live scan" bash -c '[[ -z "$(find . -path ./src/execution/live -print -o -path ./execution/live -print)" ]]'
run_check "secret scan" "$PY_CMD" scripts/m0_secret_scan.py
run_check "runtime artifact scan" artifact_scan
run_check "git diff --check" git diff --check

echo
echo "M1E IS design validation summary"
for result in "${RESULTS[@]}"; do echo "- $result"; done
echo "PASS=$PASS_COUNT FAIL=$FAIL_COUNT"
[[ "$FAIL_COUNT" -eq 0 ]]
