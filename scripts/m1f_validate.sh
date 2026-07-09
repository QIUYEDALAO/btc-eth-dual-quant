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

read_only_scan() {
  local order="order"
  local post="PO""ST"
  local delete_word="DE""LETE"
  local fill="fill"
  local engine="engine"
  local pattern="(/api/v3/${order}|/fapi/v1/${order}|/sapi/v1/margin/${order}|${post}|${delete_word}|place_${order}|cancel_${order}|create_${order}|simulate_${fill}|matching_${engine})"
  if command -v rg >/dev/null 2>&1; then
    ! rg -n "$pattern" src scripts freqtrade_lab
  else
    ! grep -R -n -E "$pattern" src scripts freqtrade_lab
  fi
}

execution_live_scan() {
  local output
  output="$(find . -path './src/execution/live' -print -o -path './execution/live' -print)"
  if [[ -n "$output" ]]; then
    printf '%s\n' "$output"
    return 1
  fi
  return 0
}

required_files() {
  test -f freqtrade_lab/docker-compose.yml &&
  test -f freqtrade_lab/user_data/configs/config.dryrun.example.json &&
  test -f freqtrade_lab/user_data/strategies/M1ATrendValidationStrategy.py &&
  test -f reports/m1/M1F_FREQTRADE_FEASIBILITY_REPORT.md &&
  test -f reports/m1/M1F_FREQTRADE_FUNDING_ARBITRAGE_GAP_ANALYSIS.md
}

run_check "M0 validation" bash scripts/m0_validate.sh
run_check "M1A validation" bash scripts/m1a_validate.sh
run_check "Freqtrade no-live guard" bash freqtrade_lab/scripts/ft_no_live_guard.sh
run_check "M1F required files" required_files
run_check "compileall" env PYTHONPATH=.deps:src "$PY_CMD" -m compileall src scripts
run_check "read-only/no-trading scan" read_only_scan
run_check "execution/live scan" execution_live_scan
run_check "secret scan" "$PY_CMD" scripts/m0_secret_scan.py
run_check "git diff --check" git diff --check

echo
echo "M1F validation summary"
for result in "${RESULTS[@]}"; do
  echo "- $result"
done
echo "PASS=$PASS_COUNT FAIL=$FAIL_COUNT"

if [[ "$FAIL_COUNT" -ne 0 ]]; then
  exit 1
fi
