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
  local report="reports/m0/T1_CANONICAL_MINUTE_DATA_REPORT.md"
  [[ -f "$report" ]] || return 1
  grep -qE '^- Status: pass$' "$report" || return 1
  grep -qE '^- Research start: 2023-10-01$' "$report" || return 1
  grep -qE '^- Zero unexplained relevant gaps: pass$' "$report" || return 1
  grep -qE '^- T2 authorized: yes$' "$report" || return 1
  grep -qE '^- M1D strategy code authorized: no$' "$report" || return 1
  grep -qE '^- M2 authorized: no$' "$report" || return 1
}

run_check "project validation" bash scripts/project_validate.sh
run_check "T1 unit tests" "$PY_CMD" -m unittest tests/test_t1_minute_archive.py -v
run_check "compileall" "$PY_CMD" -m compileall src scripts
run_check "T1 report guard" report_guard
run_check "secret scan" "$PY_CMD" scripts/m0_secret_scan.py
run_check "git diff --check" git diff --check

echo
echo "T1 validation summary"
for result in "${RESULTS[@]}"; do
  echo "- $result"
done
echo "PASS=$PASS_COUNT FAIL=$FAIL_COUNT"

if [[ "$FAIL_COUNT" -ne 0 ]]; then
  exit 1
fi
