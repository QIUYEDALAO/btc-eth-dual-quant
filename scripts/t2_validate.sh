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
  local report="reports/m0/T2_GOLDEN_DATA_AND_QUARANTINE_REPORT.md"
  [[ -f "$report" ]] || return 1
  grep -qE '^- Status: pass$' "$report" &&
  grep -qE '^- Research range: 2023-10-01 through ' "$report" &&
  grep -qE '^\| BTCUSDT \| 1445760 \|' "$report" &&
  grep -qE '^\| ETHUSDT \| 1445760 \|' "$report" &&
  [[ "$(grep -cE '^\| (BTCUSDT|ETHUSDT) \| 33 \| 96384 \| 0 \| 0 \| 0 \| 0 \| 0 \| `[0-9a-f]{64}` \| pass \|$' "$report")" -eq 2 ]] &&
  grep -qE '^- Runtime status: pass$' "$report" &&
  grep -qE '^- T3 authorized: yes$' "$report" &&
  grep -qE '^- M1D strategy code authorized: no$' "$report" &&
  grep -qE '^- M2 authorized: no$' "$report"
}

read_only_scan() {
  local order="order"
  local post="PO""ST"
  local delete_word="DE""LETE"
  local fill="fill"
  local engine="engine"
  local pattern="(/api/v3/${order}|/fapi/v1/${order}|/sapi/v1/margin/${order}|${post}|${delete_word}|place_${order}|cancel_${order}|create_${order}|simulate_${fill}|matching_${engine}|freqtrade[[:space:]]+trade)"
  if command -v rg >/dev/null 2>&1; then
    ! rg -n "$pattern" src scripts/t2_*.py scripts/t2_*.sh
  else
    ! grep -R -n -E "$pattern" src scripts/t2_*.py scripts/t2_*.sh
  fi
}

execution_live_scan() {
  [[ -z "$(find . -path './src/execution/live' -print -o -path './execution/live' -print)" ]]
}

artifact_scan() {
  local tracked
  tracked="$(git ls-files | grep -E '(^|/)\.env($|\.)|^storage/(raw|duckdb|logs)/|^freqtrade_lab/user_data/(data|logs|backtest_results|hyperopt_results)/|\.duckdb$|\.sqlite($|-)|M0_PRIVATE_SMOKE_REPORT\.local\.md$' || true)"
  if [[ -n "$tracked" ]]; then
    printf '%s\n' "$tracked"
    return 1
  fi
  return 0
}

run_check "T1 validation" bash scripts/t1_validate.sh
run_check "T2 unit tests" "$PY_CMD" -m unittest tests/test_t2_golden_data.py -v
run_check "compileall" "$PY_CMD" -m compileall src scripts
run_check "T2 report gate" report_guard
run_check "read-only/no-trading scan" read_only_scan
run_check "execution/live scan" execution_live_scan
run_check "secret scan" "$PY_CMD" scripts/m0_secret_scan.py
run_check "runtime artifact scan" artifact_scan
run_check "git diff --check" git diff --check

echo
echo "T2 validation summary"
for result in "${RESULTS[@]}"; do
  echo "- $result"
done
echo "PASS=$PASS_COUNT FAIL=$FAIL_COUNT"

if [[ "$FAIL_COUNT" -ne 0 ]]; then
  exit 1
fi
