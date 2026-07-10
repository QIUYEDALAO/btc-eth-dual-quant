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

expert_regression() {
  local root tmp expected observed
  root="$(pwd)"
  tmp="$(mktemp -d)" || return 1
  expected="842291287ca64967831fb36d1d1af2cbea4c77a80663f283d238f490e0a06bda"
  (
    cd "$tmp" || exit 1
    PYTHONPATH="$root/.deps:$root/src" "$PY_CMD" "$root/reports/expert/m1c_recompute.py" >/dev/null
  ) || { rm -rf "$tmp"; return 1; }
  observed="$($PY_CMD -c 'import hashlib,sys; print(hashlib.sha256(open(sys.argv[1], "rb").read()).hexdigest())' "$tmp/m1c_oos_daily_equity.csv")"
  rm -rf "$tmp"
  [[ "$observed" == "$expected" ]]
}

report_guard() {
  local report="reports/m1/T3_UNIFIED_METRICS_AND_POLICY_BENCHMARK_REPORT.md"
  [[ -f "$report" ]] || return 1
  grep -qE '^- Status: pass$' "$report" &&
  grep -qE '^- New strategy evaluated: no$' "$report" &&
  grep -qE '^- New candidate OOS opened: no$' "$report" &&
  grep -qE '^\| Base \| 975 \| 53\.4431% \| 17\.4039% \| 23\.9985% \| 0\.7882 \| 23\.4729% \|' "$report" &&
  grep -qE '^\| Cost x2 \| 975 \| 49\.9456% \| 16\.3938% \| 23\.9719% \| 0\.7528 \| 24\.4688% \|' "$report" &&
  grep -qE '^- T4 authorized: yes$' "$report" &&
  grep -qE '^- M1D feasibility authorized: no; T4 must pass first$' "$report" &&
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
    ! rg -n "$pattern" src scripts/t3_build_unified_metrics_report.py
  else
    ! grep -R -n -E "$pattern" src scripts/t3_build_unified_metrics_report.py
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

run_check "T2 validation" bash scripts/t2_validate.sh
run_check "T3 unit tests" "$PY_CMD" -m unittest tests/test_t3_unified_metrics.py -v
run_check "sealed expert recompute" expert_regression
run_check "compileall" "$PY_CMD" -m compileall src scripts
run_check "T3 report gate" report_guard
run_check "read-only/no-trading scan" read_only_scan
run_check "execution/live scan" execution_live_scan
run_check "secret scan" "$PY_CMD" scripts/m0_secret_scan.py
run_check "runtime artifact scan" artifact_scan
run_check "git diff --check" git diff --check

echo
echo "T3 validation summary"
for result in "${RESULTS[@]}"; do
  echo "- $result"
done
echo "PASS=$PASS_COUNT FAIL=$FAIL_COUNT"

if [[ "$FAIL_COUNT" -ne 0 ]]; then
  exit 1
fi
