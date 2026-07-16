#!/usr/bin/env bash
set -u
PY_CMD="${PYTHON:-python3}"
export PYTHONPATH="${PYTHONPATH:-.deps:src}"
PASS_COUNT=0; FAIL_COUNT=0; RESULTS=()
run_check(){ local name="$1"; shift; echo "==> $name"; if "$@"; then RESULTS+=("PASS $name"); PASS_COUNT=$((PASS_COUNT+1)); else RESULTS+=("FAIL $name"); FAIL_COUNT=$((FAIL_COUNT+1)); fi; }
artifact_scan(){ [[ -z "$(git ls-files | grep -E '(^|/)\.env($|\.)|^storage/(raw|duckdb|logs)/|^freqtrade_lab/user_data/(data|logs|backtest_results)/|\.duckdb$|\.sqlite($|-)|M0_PRIVATE_SMOKE_REPORT\.local\.md$' || true)" ]]; }
read_only_scan(){ local o="order" p="PO""ST" d="DE""LETE" sim="simulate_""fill" engine="matching_""engine"; local pattern="(/api/v3/${o}|/fapi/v1/${o}|${p}|${d}|place_${o}|cancel_${o}|create_${o}|${sim}|${engine}|freqtrade[[:space:]]+trade)"; if command -v rg >/dev/null; then ! rg -n "$pattern" src scripts; else ! grep -R -n -E "$pattern" src scripts; fi; }
run_check "frozen protocol" bash scripts/u03f_v4_audit_protocol_validate.sh
run_check "auditor fixture/fault tests" "$PY_CMD" -m unittest discover -s tests -p 'test_u03f_v4_auditor*.py' -v
run_check "auditor independence checker" "$PY_CMD" scripts/u03f_v4_independent_audit_check.py
run_check "normal fixture smoke" "$PY_CMD" scripts/u03f_v4_independent_audit.py --fixture-smoke --order normal
run_check "reverse fixture smoke" "$PY_CMD" scripts/u03f_v4_independent_audit.py --fixture-smoke --order reverse
run_check "project validation" bash scripts/project_validate.sh
run_check "compileall" "$PY_CMD" -m compileall src scripts
run_check "read-only scan" read_only_scan
run_check "execution/live scan" bash -c '[[ -z "$(find . -path ./src/execution/live -print -o -path ./execution/live -print)" ]]'
run_check "secret scan" "$PY_CMD" scripts/m0_secret_scan.py
run_check "runtime artifact scan" artifact_scan
run_check "git diff --check" git diff --check
echo; echo "U-03F auditor implementation validation summary"; for result in "${RESULTS[@]}"; do echo "- $result"; done; echo "PASS=$PASS_COUNT FAIL=$FAIL_COUNT"; [[ "$FAIL_COUNT" -eq 0 ]]
