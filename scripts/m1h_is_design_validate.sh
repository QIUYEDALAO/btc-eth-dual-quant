#!/usr/bin/env bash
set -u
PY_CMD="${PYTHON:-python3}"
export PYTHONPATH="${PYTHONPATH:-.deps:src}"
PASS_COUNT=0; FAIL_COUNT=0; RESULTS=()
run_check() { local name="$1"; shift; echo "==> $name"; if "$@"; then RESULTS+=("PASS $name"); PASS_COUNT=$((PASS_COUNT+1)); else RESULTS+=("FAIL $name"); FAIL_COUNT=$((FAIL_COUNT+1)); fi; }
report_guard() {
  grep -qE '^- Status: economic_hypothesis_pass_paper_protocol_only$' reports/m1/M1H_IS_ONLY_RULE_DESIGN.md &&
  grep -qE '^- Candidate events evaluated: no$' reports/m1/M1H_IS_ONLY_RULE_DESIGN.md &&
  grep -qE '^- Formal strategy returns computed: no$' reports/m1/M1H_IS_ONLY_RULE_DESIGN.md &&
  grep -qE '^- OOS opened: no$' reports/m1/M1H_IS_ONLY_RULE_DESIGN.md &&
  grep -qE '^- Status: pass_design_level$' reports/m1/M1H_NON_DUPLICATION_REVIEW.md &&
  grep -qE '^- Status: constraint_pass_no_exit_selected$' reports/m1/M1H_EXECUTION_REPRESENTABILITY_REVIEW.md
}
read_only_scan() { local order="order" post="PO""ST" delete_word="DE""LETE" fill="fill" engine="engine"; local pattern="(/api/v3/${order}|/fapi/v1/${order}|/sapi/v1/margin/${order}|${post}|${delete_word}|place_${order}|cancel_${order}|create_${order}|simulate_${fill}|matching_${engine}|freqtrade[[:space:]]+trade)"; if command -v rg >/dev/null 2>&1; then ! rg -n "$pattern" src scripts freqtrade_lab/scripts freqtrade_lab/user_data/strategies; else ! grep -R -n -E --exclude-dir=__pycache__ --binary-files=without-match "$pattern" src scripts freqtrade_lab/scripts freqtrade_lab/user_data/strategies; fi; }
artifact_scan() { local tracked; tracked="$(git ls-files | grep -E '(^|/)\.env($|\.)|^storage/(raw|duckdb|logs)/|^freqtrade_lab/user_data/(data|logs|backtest_results|hyperopt_results)/|\.duckdb$|\.sqlite($|-)|M0_PRIVATE_SMOKE_REPORT\.local\.md$' || true)"; [[ -z "$tracked" ]] || { printf '%s\n' "$tracked"; return 1; }; }
run_check "M1G failed IS evidence" bash scripts/m1g_is_validate.sh
run_check "M1H IS design tests" "$PY_CMD" -m unittest tests.test_m1h_is_design -v
run_check "M1H IS design check" "$PY_CMD" scripts/m1h_is_design_check.py
run_check "compileall" "$PY_CMD" -m compileall src scripts
run_check "M1H report gate" report_guard
run_check "read-only scan" read_only_scan
run_check "execution/live scan" bash -c '[[ -z "$(find . -path ./src/execution/live -print -o -path ./execution/live -print)" ]]'
run_check "secret scan" "$PY_CMD" scripts/m0_secret_scan.py
run_check "runtime artifact scan" artifact_scan
run_check "git diff --check" git diff --check
echo; echo "M1H IS design validation summary"; for result in "${RESULTS[@]}"; do echo "- $result"; done; echo "PASS=$PASS_COUNT FAIL=$FAIL_COUNT"; [[ "$FAIL_COUNT" -eq 0 ]]
