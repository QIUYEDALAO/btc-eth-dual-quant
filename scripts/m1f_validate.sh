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

git_diff_check() {
  if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    git diff --check
  else
    echo "git diff --check skipped: not a git worktree"
    return 0
  fi
}

required_files() {
  test -f freqtrade_lab/docker-compose.yml &&
  test -f freqtrade_lab/user_data/configs/config.dryrun.example.json &&
  test -f freqtrade_lab/user_data/strategies/M1ATrendValidationStrategy.py &&
  test -f reports/m1/M1F_FREQTRADE_FEASIBILITY_REPORT.md &&
  test -f reports/m1/M1F_FREQTRADE_FUNDING_ARBITRAGE_GAP_ANALYSIS.md &&
  test -f deploy/vps/sync_to_vps.sh &&
  test -f deploy/vps/prepare_python_deps.sh &&
  test -f deploy/vps/install_docker_ubuntu.sh &&
  test -f deploy/vps/remote_bootstrap.sh &&
  test -f deploy/vps/remote_freqtrade_smoke.sh &&
  test -f deploy/vps/README.md &&
  test -f deploy/vps/harden_ufw_readme.md &&
  test -f deploy/vps/remote_webui_dryrun_readme.md &&
  test -f reports/m1/M1F_FREQTRADE_DOCKER_SMOKE_REPORT.md &&
  test -f freqtrade_lab/WEBUI_中文说明.md &&
  test -f freqtrade_lab/安全操作清单.md &&
  test -f reports/m1/M1F_中文验收摘要.md &&
  test -f freqtrade_lab/scripts/ft_webui_local.sh &&
  test -f freqtrade_lab/scripts/ft_webui_stop.sh &&
  test -f freqtrade_lab/runtime-manifest.json &&
  test -f freqtrade_lab/scripts/ft_research.sh &&
  test -f freqtrade_lab/scripts/ft_verify_runtime.sh &&
  test -f scripts/freqtrade_runtime_manifest.py &&
  test -f scripts/freqtrade_data_provenance.py &&
  test -f freqtrade_lab/user_data/strategies/README.md &&
  test -f src/btc_eth_dual_quant/backtest/README.md
}

research_entry_guard() {
  local entry="freqtrade_lab/scripts/ft_research.sh"
  local command
  for command in download-data list-data backtesting lookahead-analysis recursive-analysis webserver; do
    grep -q "$command" "$entry" || return 1
  done
  grep -q 'ft_research\.sh backtesting' freqtrade_lab/scripts/ft_backtest_m1a_trend.sh &&
  grep -q 'ft_research\.sh download-data' freqtrade_lab/scripts/ft_download_spot_data.sh &&
  grep -q 'ft_research\.sh webserver' freqtrade_lab/scripts/ft_webui_local.sh
}

smoke_report_guard() {
  local report="reports/m1/M1F_FREQTRADE_DOCKER_SMOKE_REPORT.md"
  if grep -q 'Status: pass' "$report"; then
    grep -q 'no API key used: yes' "$report" &&
    grep -q 'no live trading: yes' "$report" &&
    grep -q 'no runtime data committed: yes' "$report"
    return
  fi
  return 0
}

webui_local_guard() {
  local script="freqtrade_lab/scripts/ft_webui_local.sh"
  ! grep -q '0\.0\.0\.0' "$script" &&
  grep -q '127\.0\.0\.1' "$script" &&
  ! grep -q 'freqtrade[[:space:]]\+trade' "$script" &&
  grep -q 'ft_no_live_guard\.sh' "$script"
}

run_check "M0 validation" bash scripts/m0_validate.sh
run_check "M1A validation" bash scripts/m1a_validate.sh
run_check "Freqtrade no-live guard" bash freqtrade_lab/scripts/ft_no_live_guard.sh
run_check "Freqtrade pinned runtime manifest" "$PY_CMD" scripts/freqtrade_runtime_manifest.py validate
run_check "Freqtrade unified research entry" research_entry_guard
run_check "M1F required files" required_files
run_check "M1F smoke report guard" smoke_report_guard
run_check "WebUI local-only guard" webui_local_guard
run_check "compileall" env PYTHONPATH=.deps:src "$PY_CMD" -m compileall src scripts
run_check "read-only/no-trading scan" read_only_scan
run_check "execution/live scan" execution_live_scan
run_check "secret scan" "$PY_CMD" scripts/m0_secret_scan.py
run_check "git diff --check" git_diff_check

echo
echo "M1F validation summary"
for result in "${RESULTS[@]}"; do
  echo "- $result"
done
echo "PASS=$PASS_COUNT FAIL=$FAIL_COUNT"

if [[ "$FAIL_COUNT" -ne 0 ]]; then
  exit 1
fi
