#!/usr/bin/env bash
set -u

PY_CMD="${PYTHON:-python3}"
export PYTHONPATH="${PYTHONPATH:-.deps:src}"
PASS_COUNT=0; FAIL_COUNT=0; RESULTS=()

run_check() {
  local name="$1"; shift
  echo "==> $name"
  if "$@"; then RESULTS+=("PASS $name"); PASS_COUNT=$((PASS_COUNT + 1));
  else RESULTS+=("FAIL $name"); FAIL_COUNT=$((FAIL_COUNT + 1)); fi
}

report_state_gate() {
  grep -qE '^- Status: frozen_before_result$' reports/m1/M1H_PAPER_PROTOCOL.md &&
  grep -qE '^- Trial status: declared_unopened$' reports/m1/M1H_PAPER_PROTOCOL.md &&
  grep -qE '^- Event scan executed: no$' reports/m1/M1H_PAPER_PROTOCOL.md &&
  grep -qE '^- Formal strategy returns computed: no$' reports/m1/M1H_PAPER_PROTOCOL.md &&
  grep -qE '^- OOS opened: no$' reports/m1/M1H_PAPER_PROTOCOL.md || return 1

  if grep -qE '^current_phase: M1H paper protocol frozen pending review$' PROJECT_STATE.yaml; then
    grep -qE '^current_status: m1h_paper_protocol_frozen_no_outcome_oos_sealed_no_m2$' PROJECT_STATE.yaml
  elif grep -qE '^current_phase: M1H data qualification then sealed-IS paper feasibility authorized not started$' PROJECT_STATE.yaml; then
    grep -qE '^current_status: m1h_protocol_merged_m1h03_authorized_not_started_oos_sealed_no_m2$' PROJECT_STATE.yaml
  elif grep -qE '^current_phase: M1H failed feasibility; BTC/ETH two-asset indicator research stopped$' PROJECT_STATE.yaml; then
    grep -qE '^current_status: m1h_failed_feasibility_candidate_queue_exhausted_oos_sealed_no_m2$' PROJECT_STATE.yaml
  elif grep -qE '^current_phase: BTC/ETH candidate queue exhausted; liquid-universe ADR authorized$' PROJECT_STATE.yaml; then
    grep -qE '^current_status: btc_eth_candidate_queue_exhausted_liquid_universe_adr_authorized_no_m2$' PROJECT_STATE.yaml
  else
    return 1
  fi
}

read_only_scan() {
  local order="order" post="PO""ST" delete_word="DE""LETE" fill="fill" engine="engine"
  local pattern="(/api/v3/${order}|/fapi/v1/${order}|/sapi/v1/margin/${order}|${post}|${delete_word}|place_${order}|cancel_${order}|create_${order}|simulate_${fill}|matching_${engine}|freqtrade[[:space:]]+trade)"
  if command -v rg >/dev/null 2>&1; then ! rg -n "$pattern" src scripts freqtrade_lab/scripts freqtrade_lab/user_data/strategies
  else ! grep -R -n -E --exclude-dir=__pycache__ --binary-files=without-match "$pattern" src scripts freqtrade_lab/scripts freqtrade_lab/user_data/strategies; fi
}

artifact_scan() {
  local tracked
  tracked="$(git ls-files | grep -E '(^|/)\.env($|\.)|^storage/(raw|duckdb|logs)/|^freqtrade_lab/user_data/(data|logs|backtest_results|hyperopt_results)/|\.duckdb$|\.sqlite($|-)|M0_PRIVATE_SMOKE_REPORT\.local\.md$' || true)"
  [[ -z "$tracked" ]] || { printf '%s\n' "$tracked"; return 1; }
}

run_check "M1H design validation" bash scripts/m1h_is_design_validate.sh
run_check "M1H protocol tests" "$PY_CMD" -m unittest tests.test_m1h_paper_protocol -v
run_check "M1H protocol checker" "$PY_CMD" scripts/m1h_paper_protocol_check.py
run_check "project validation" bash scripts/project_validate.sh
run_check "compileall" "$PY_CMD" -m compileall src scripts
run_check "report/state gate" report_state_gate
run_check "read-only scan" read_only_scan
run_check "execution/live scan" bash -c '[[ -z "$(find . -path ./src/execution/live -print -o -path ./execution/live -print)" ]]'
run_check "secret scan" "$PY_CMD" scripts/m0_secret_scan.py
run_check "runtime artifact scan" artifact_scan
run_check "git diff --check" git diff --check

echo
echo "M1H paper protocol validation summary"
for result in "${RESULTS[@]}"; do echo "- $result"; done
echo "PASS=$PASS_COUNT FAIL=$FAIL_COUNT"
[[ "$FAIL_COUNT" -eq 0 ]]
