#!/usr/bin/env bash
set -euo pipefail

if [[ -z "${VPS_HOST:-}" ]]; then
  echo "VPS_HOST is required. Example: export VPS_HOST=root@47.97.19.77" >&2
  exit 1
fi

VPS_APP_DIR="${VPS_APP_DIR:-~/apps/btc-eth-dual-quant}"
REPORT_PATH="reports/m1/M1F_FREQTRADE_DOCKER_SMOKE_REPORT.md"
SMOKE_TIMERANGE="${SMOKE_TIMERANGE:-20170817-20260709}"
MASKED_SERVER="$(printf '%s' "$VPS_HOST" | sed -E 's/@[0-9.]+/@***.***.***.***/')"
STATUS="fail"
PULL_STATUS="fail"
VERSION_STATUS="fail"
SHOW_CONFIG_STATUS="fail"
DOWNLOAD_STATUS="fail"
LIST_DATA_STATUS="fail"
BACKTEST_STATUS="fail"
LOOKAHEAD_STATUS="fail"
RECURSIVE_STATUS="fail"
LAST_OUTPUT=""

run_remote_check() {
  local command="$1"
  local output
  if ! output="$(ssh "$VPS_HOST" "cd '$VPS_APP_DIR/freqtrade_lab' && $command" 2>&1)"; then
    printf '%s\n' "$output"
    LAST_OUTPUT="$output"
    return 1
  fi
  printf '%s\n' "$output"
  LAST_OUTPUT="$output"
  if printf '%s\n' "$output" | grep -E 'invalid choice|Configuration error|CRITICAL|ERROR - Configuration error' >/dev/null; then
    return 1
  fi
  return 0
}

set +e
run_remote_check "bash scripts/ft_no_live_guard.sh"
GUARD_CODE=$?
if [[ "$GUARD_CODE" -eq 0 ]]; then
  run_remote_check "bash scripts/ft_pull.sh"
  [[ "$?" -eq 0 ]] && PULL_STATUS="pass"
  run_remote_check "bash scripts/ft_verify_runtime.sh"
  [[ "$?" -eq 0 ]] && VERSION_STATUS="pass"
  run_remote_check "docker compose run --rm freqtrade show-config --config user_data/configs/config.dryrun.example.json"
  [[ "$?" -eq 0 ]] && SHOW_CONFIG_STATUS="pass"
  run_remote_check "FT_TIMERANGE=${SMOKE_TIMERANGE} bash scripts/ft_download_spot_data.sh"
  [[ "$?" -eq 0 ]] && DOWNLOAD_STATUS="pass"
  run_remote_check "bash scripts/ft_list_data.sh"
  [[ "$?" -eq 0 ]] && LIST_DATA_STATUS="pass"
  run_remote_check "FT_TIMERANGE=${SMOKE_TIMERANGE} bash scripts/ft_backtest_m1a_trend.sh"
  [[ "$?" -eq 0 ]] && BACKTEST_STATUS="pass"
  run_remote_check "FT_TIMERANGE=${SMOKE_TIMERANGE} bash scripts/ft_lookahead_m1a.sh"
  [[ "$?" -eq 0 ]] && LOOKAHEAD_STATUS="pass"
  run_remote_check "FT_TIMERANGE=${SMOKE_TIMERANGE} bash scripts/ft_recursive_m1a.sh"
  [[ "$?" -eq 0 ]] && RECURSIVE_STATUS="pass"
fi
set -e

if [[ "$PULL_STATUS" == "pass" && "$VERSION_STATUS" == "pass" && "$SHOW_CONFIG_STATUS" == "pass" && "$DOWNLOAD_STATUS" == "pass" && "$LIST_DATA_STATUS" == "pass" && "$BACKTEST_STATUS" == "pass" && "$LOOKAHEAD_STATUS" == "pass" && "$RECURSIVE_STATUS" == "pass" ]]; then
  STATUS="pass"
fi

mkdir -p "$(dirname "$REPORT_PATH")"
cat > "$REPORT_PATH" <<EOF
# M1F Freqtrade Docker Smoke Report

Generated UTC: $(date -u +"%Y-%m-%dT%H:%M:%SZ")

- Status: ${STATUS}
- server: ${MASKED_SERVER}
- docker compose pull: ${PULL_STATUS}
- freqtrade version: ${VERSION_STATUS}
- show-config: ${SHOW_CONFIG_STATUS}
- download public spot data: ${DOWNLOAD_STATUS}
- list public spot data: ${LIST_DATA_STATUS}
- backtest M1ATrendValidationStrategy: ${BACKTEST_STATUS}
- lookahead-analysis M1ATrendValidationStrategy: ${LOOKAHEAD_STATUS}
- recursive-analysis M1ATrendValidationStrategy: ${RECURSIVE_STATUS}
- smoke timerange: ${SMOKE_TIMERANGE}
- no API key used: yes
- no live trading: yes
- no paper trading with real API: yes
- no execution/live: yes
- no runtime data committed: yes
EOF

cat "$REPORT_PATH"
[[ "$STATUS" == "pass" ]]
