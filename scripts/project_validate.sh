#!/usr/bin/env bash
set -u

PY_CMD="${PYTHON:-python3}"
export PYTHONPATH="${PYTHONPATH:-.deps:src}"

PASS_COUNT=0
FAIL_COUNT=0
RESULTS=()

record_pass() {
  RESULTS+=("PASS $1")
  PASS_COUNT=$((PASS_COUNT + 1))
}

record_fail() {
  RESULTS+=("FAIL $1")
  FAIL_COUNT=$((FAIL_COUNT + 1))
}

run_check() {
  local name="$1"
  shift
  echo "==> $name"
  if "$@"; then
    record_pass "$name"
  else
    record_fail "$name"
  fi
}

git_diff_check() {
  if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    git diff --check
  else
    echo "git diff --check skipped: not a git worktree"
    return 0
  fi
}

maybe_m1b_validate() {
  if [[ -f scripts/m1b_validate.sh ]]; then
    bash scripts/m1b_validate.sh
  else
    echo "scripts/m1b_validate.sh not present on this branch; skipped"
  fi
}

run_check "project context check" "$PY_CMD" scripts/project_context_check.py
run_check "context summary" "$PY_CMD" scripts/context_summary.py
run_check "strategy trial ledger check" "$PY_CMD" scripts/strategy_trial_ledger_check.py
run_check "external strategy trial accounting" "$PY_CMD" scripts/external_strategy_trial_accounting_check.py
run_check "external strategy runtime boundary status" "$PY_CMD" scripts/external_strategy_is_boundary_qualification.py
run_check "external strategy boundary authority source status" bash scripts/external_strategy_boundary_authority_validate.sh
run_check "ADR-0018 scheduled cessation contract" bash scripts/adr0018_scheduled_market_cessation_validate.sh
run_check "M0 validation" bash scripts/m0_validate.sh
run_check "M1A validation" bash scripts/m1a_validate.sh
run_check "M1F validation" bash scripts/m1f_validate.sh
run_check "M1B validation if present" maybe_m1b_validate
run_check "git diff --check" git_diff_check

echo
echo "Project validation summary"
for result in "${RESULTS[@]}"; do
  echo "- $result"
done
echo "PASS=$PASS_COUNT FAIL=$FAIL_COUNT"

if [[ "$FAIL_COUNT" -ne 0 ]]; then
  exit 1
fi
