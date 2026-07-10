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

ledger_guard() {
  "$PY_CMD" - <<'PY'
from pathlib import Path
from btc_eth_dual_quant.audit.feasibility import validate_candidate_identity

hypothesis = (
    "M1D-15M-DISCRETE-DISLOCATION: BTC/USDT and ETH/USDT spot; completed 15m candles identify "
    "discrete large-price-dislocation events; enter no earlier than the next 15m open; 1m data is "
    "execution detail only; no shorting or leverage."
)
validate_candidate_identity(
    Path("STRATEGY_TRIAL_LEDGER.yaml"),
    candidate_id="M1D-15M-DISCRETE-DISLOCATION",
    expected_hypothesis=hypothesis,
    expected_sha256="fdccf79b213f87fc9ee1cb74daf42f67e7ba63fba6de9990851c2eec9e11e1a7",
)
PY
}

report_guard() {
  local report="reports/m1/T4_IS_ONLY_FEASIBILITY_HARNESS_REPORT.md"
  [[ -f "$report" ]] || return 1
  grep -qE '^- Status: pass$' "$report" &&
  grep -qE '^- Candidate evaluated: no$' "$report" &&
  grep -qE '^- OOS returns accessed: no$' "$report" &&
  grep -qE '^\| Sealed OOS days \(last 30%\) \| 302 \| fail \|$' "$report" &&
  grep -qE '^\| Required OOS days \| 540 \| fixed \|$' "$report" &&
  grep -qE '^- T4 harness foundation: pass$' "$report" &&
  grep -qE '^- T5 calendar gate currently pass: no$' "$report" &&
  grep -qE '^- M1D strategy code authorized: no$' "$report" &&
  grep -qE '^- M2 authorized: no$' "$report"
}

read_only_scan() {
  local order="order" post="PO""ST" delete_word="DE""LETE" fill="fill" engine="engine"
  local pattern="(/api/v3/${order}|/fapi/v1/${order}|/sapi/v1/margin/${order}|${post}|${delete_word}|place_${order}|cancel_${order}|create_${order}|simulate_${fill}|matching_${engine}|freqtrade[[:space:]]+trade)"
  if command -v rg >/dev/null 2>&1; then
    ! rg -n "$pattern" src scripts/t4_*.py
  else
    ! grep -R -n -E "$pattern" src scripts/t4_*.py
  fi
}

execution_live_scan() {
  [[ -z "$(find . -path './src/execution/live' -print -o -path './execution/live' -print)" ]]
}

artifact_scan() {
  local tracked
  tracked="$(git ls-files | grep -E '(^|/)\.env($|\.)|^storage/(raw|duckdb|logs)/|^freqtrade_lab/user_data/(data|logs|backtest_results|hyperopt_results)/|\.duckdb$|\.sqlite($|-)|M0_PRIVATE_SMOKE_REPORT\.local\.md$' || true)"
  [[ -z "$tracked" ]] || { printf '%s\n' "$tracked"; return 1; }
}

run_check "T3 validation" bash scripts/t3_validate.sh
run_check "T4 unit tests" "$PY_CMD" -m unittest tests/test_t4_feasibility.py -v
run_check "trial-ledger lock" ledger_guard
run_check "compileall" "$PY_CMD" -m compileall src scripts
run_check "T4 report gate" report_guard
run_check "read-only/no-trading scan" read_only_scan
run_check "execution/live scan" execution_live_scan
run_check "secret scan" "$PY_CMD" scripts/m0_secret_scan.py
run_check "runtime artifact scan" artifact_scan
run_check "git diff --check" git diff --check

echo
echo "T4 validation summary"
for result in "${RESULTS[@]}"; do echo "- $result"; done
echo "PASS=$PASS_COUNT FAIL=$FAIL_COUNT"
[[ "$FAIL_COUNT" -eq 0 ]]
