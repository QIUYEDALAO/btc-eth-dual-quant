#!/usr/bin/env bash
set -u

PY_CMD="${PYTHON:-python3}"
export PYTHONPATH=".:.deps:src${PYTHONPATH:+:$PYTHONPATH}"
PASS_COUNT=0; FAIL_COUNT=0; RESULTS=()

run_check() {
  local name="$1"; shift
  echo "==> $name"
  if "$@"; then RESULTS+=("PASS $name"); PASS_COUNT=$((PASS_COUNT + 1));
  else RESULTS+=("FAIL $name"); FAIL_COUNT=$((FAIL_COUNT + 1)); fi
}

artifact_scan() {
  local tracked
  tracked="$(git ls-files | grep -E '(^|/)\.env($|\.)|^storage/(raw|duckdb|logs)/|^freqtrade_lab/user_data/(data|logs|backtest_results|hyperopt_results)/|\.duckdb$|\.sqlite($|-)|M0_PRIVATE_SMOKE_REPORT\.local\.md$' || true)"
  [[ -z "$tracked" ]] || { printf '%s\n' "$tracked"; return 1; }
}

read_only_scan() {
  local order="order" post="PO""ST" delete_word="DE""LETE" fill="fill" engine="engine"
  local pattern="(/api/v3/${order}|/fapi/v1/${order}|/sapi/v1/margin/${order}|${post}|${delete_word}|place_${order}|cancel_${order}|create_${order}|simulate_${fill}|matching_${engine}|freqtrade[[:space:]]+trade)"
  ! rg -n "$pattern" src scripts freqtrade_lab/scripts freqtrade_lab/user_data/strategies
}

run_check "ADR-0015 independent review tests" "$PY_CMD" -m unittest tests.test_adr0015_independent_review -v
run_check "ADR-0015 independent review checker" "$PY_CMD" scripts/adr0015_independent_review_check.py
run_check "ADR-0015 Draft regression" "$PY_CMD" scripts/adr0015_policy_draft_check.py
run_check "invalid-interval diagnostic evidence checker" "$PY_CMD" scripts/liquid_universe_v4_invalid_interval_adjudication_check.py
run_check "invalid-interval protocol regression" "$PY_CMD" scripts/u03f_v4_invalid_interval_protocol_check.py
run_check "project validation" bash scripts/project_validate.sh
run_check "compileall" "$PY_CMD" -m compileall -q src scripts
run_check "read-only scan" read_only_scan
run_check "execution/live scan" bash -c '[[ -z "$(find . -path ./src/execution/live -print -o -path ./execution/live -print)" ]]'
run_check "secret scan" "$PY_CMD" scripts/m0_secret_scan.py
run_check "runtime artifact scan" artifact_scan
run_check "git diff --check" git diff --check

echo
echo "ADR-0015 independent policy review validation summary"
for result in "${RESULTS[@]}"; do echo "- $result"; done
echo "PASS=$PASS_COUNT FAIL=$FAIL_COUNT"
[[ "$FAIL_COUNT" -eq 0 ]]
