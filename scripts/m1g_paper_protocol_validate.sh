#!/usr/bin/env bash
set -u
PY_CMD="${PYTHON:-python3}"
export PYTHONPATH="${PYTHONPATH:-.deps:src}"
PASS_COUNT=0; FAIL_COUNT=0; RESULTS=()
run_check() { local name="$1"; shift; echo "==> $name"; if "$@"; then RESULTS+=("PASS $name"); PASS_COUNT=$((PASS_COUNT+1)); else RESULTS+=("FAIL $name"); FAIL_COUNT=$((FAIL_COUNT+1)); fi; }
report_guard() { grep -qE '^- Status: frozen_before_result$' reports/m1/M1G_IS_PAPER_PROTOCOL.md && grep -qE '^- Event scan executed: no$' reports/m1/M1G_IS_PAPER_PROTOCOL.md && grep -qE '^- Candidate outcomes accessed: no$' reports/m1/M1G_IS_PAPER_PROTOCOL.md && grep -qE '^- OOS opened: no$' reports/m1/M1G_IS_PAPER_PROTOCOL.md; }
artifact_scan() { local tracked; tracked="$(git ls-files | grep -E '(^|/)\.env($|\.)|^storage/(raw|duckdb|logs)/|^freqtrade_lab/user_data/(data|logs|backtest_results|hyperopt_results)/|\.duckdb$|\.sqlite($|-)|M0_PRIVATE_SMOKE_REPORT\.local\.md$' || true)"; [[ -z "$tracked" ]] || { printf '%s\n' "$tracked"; return 1; }; }
run_check "M1G design validation" bash scripts/m1g_is_design_validate.sh
run_check "M1G protocol tests" "$PY_CMD" -m unittest tests/test_m1g_paper_protocol.py -v
run_check "M1G protocol check" "$PY_CMD" scripts/m1g_paper_protocol_check.py
run_check "compileall" "$PY_CMD" -m compileall src scripts
run_check "M1G protocol report gate" report_guard
run_check "execution/live scan" bash -c '[[ -z "$(find . -path ./src/execution/live -print -o -path ./execution/live -print)" ]]'
run_check "secret scan" "$PY_CMD" scripts/m0_secret_scan.py
run_check "runtime artifact scan" artifact_scan
run_check "git diff --check" git diff --check
echo; echo "M1G paper protocol validation summary"; for result in "${RESULTS[@]}"; do echo "- $result"; done; echo "PASS=$PASS_COUNT FAIL=$FAIL_COUNT"; [[ "$FAIL_COUNT" -eq 0 ]]
