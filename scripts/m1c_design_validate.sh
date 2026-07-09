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

no_forbidden_artifacts() {
  ! git ls-files | grep -E '(^|/)(\.env($|\.)|storage/(raw|duckdb|logs)/|.*\.duckdb$|.*\.sqlite$|M0_PRIVATE_SMOKE_REPORT\.local\.md$)'
}

run_check "project validation" bash scripts/project_validate.sh
run_check "M1C design contract" "$PY_CMD" scripts/m1c_validate_design.py
run_check "M1C design tests" "$PY_CMD" -m unittest tests.test_m1c_rotation_design -v
run_check "compileall" "$PY_CMD" -m compileall src scripts tests
run_check "no forbidden tracked artifacts" no_forbidden_artifacts
run_check "secret scan" "$PY_CMD" scripts/m0_secret_scan.py
run_check "git diff check" git diff --check

echo
echo "M1C design validation summary"
for result in "${RESULTS[@]}"; do
  echo "- $result"
done
echo "PASS=$PASS_COUNT FAIL=$FAIL_COUNT"

if [[ "$FAIL_COUNT" -ne 0 ]]; then
  exit 1
fi
