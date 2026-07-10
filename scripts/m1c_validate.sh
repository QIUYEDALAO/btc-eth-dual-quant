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

read_only_scan() {
  local order="order"
  local post="PO""ST"
  local delete_word="DE""LETE"
  local fill="fill"
  local engine="engine"
  local pattern="(/api/v3/${order}|/fapi/v1/${order}|/sapi/v1/margin/${order}|${post}|${delete_word}|place_${order}|cancel_${order}|create_${order}|simulate_${fill}|matching_${engine}|freqtrade[[:space:]]+trade)"
  if command -v rg >/dev/null 2>&1; then
    ! rg -n "$pattern" src scripts freqtrade_lab/scripts freqtrade_lab/user_data/strategies
  else
    ! grep -R -n -E "$pattern" src scripts freqtrade_lab/scripts freqtrade_lab/user_data/strategies
  fi
}

execution_live_scan() {
  local output
  output="$(find . -path './src/execution/live' -print -o -path './execution/live' -print)"
  [[ -z "$output" ]] || { printf '%s\n' "$output"; return 1; }
}

no_forbidden_artifacts() {
  ! git ls-files | grep -E '(^|/)(\.env($|\.)|storage/(raw|duckdb|logs)/|.*\.duckdb$|.*\.sqlite$|backtest_results/|M0_PRIVATE_SMOKE_REPORT\.local\.md$)'
}

run_check "M0 validation" bash scripts/m0_validate.sh
run_check "M1C design contract" "$PY_CMD" scripts/m1c_validate_design.py
run_check "M1C strategy and timing tests" "$PY_CMD" -m unittest tests.test_m1c_rotation_strategy -v
run_check "compileall" "$PY_CMD" -m compileall src scripts freqtrade_lab/user_data/strategies
run_check "read-only/no-trading scan" read_only_scan
run_check "execution/live scan" execution_live_scan
run_check "secret scan" "$PY_CMD" scripts/m0_secret_scan.py
run_check "no forbidden tracked artifacts" no_forbidden_artifacts
run_check "git diff check" git diff --check

echo
echo "M1C validation summary"
for result in "${RESULTS[@]}"; do
  echo "- $result"
done
echo "PASS=$PASS_COUNT FAIL=$FAIL_COUNT"

if [[ "$FAIL_COUNT" -ne 0 ]]; then
  exit 1
fi
