#!/usr/bin/env bash
set -euo pipefail

if [[ -z "${VPS_HOST:-}" ]]; then
  echo "VPS_HOST is required. Example: export VPS_HOST=root@47.97.19.77" >&2
  exit 1
fi

VPS_APP_DIR="${VPS_APP_DIR:-~/apps/btc-eth-dual-quant}"
REPORT_PATH="reports/m1/M1F_FREQTRADE_DOCKER_SMOKE_REPORT.md"
SMOKE_TIMERANGE="${SMOKE_TIMERANGE:-20240101-}"
MASKED_SERVER="$(printf '%s' "$VPS_HOST" | sed -E 's/@[0-9.]+/@***.***.***.***/')"
STATUS="fail"
PULL_STATUS="fail"
VERSION_STATUS="fail"
SHOW_CONFIG_STATUS="fail"
DOWNLOAD_STATUS="fail"
BACKTEST_STATUS="fail"
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
  run_remote_check "docker compose pull"
  [[ "$?" -eq 0 ]] && PULL_STATUS="pass"
  run_remote_check "docker compose run --rm freqtrade --version"
  [[ "$?" -eq 0 ]] && VERSION_STATUS="pass"
  run_remote_check "docker compose run --rm freqtrade show-config --config user_data/configs/config.dryrun.example.json"
  [[ "$?" -eq 0 ]] && SHOW_CONFIG_STATUS="pass"
  run_remote_check "docker compose run --rm freqtrade download-data --config user_data/configs/config.dryrun.example.json --exchange binance --pairs BTC/USDT ETH/USDT --timeframes 1d --trading-mode spot --timerange ${SMOKE_TIMERANGE}"
  [[ "$?" -eq 0 ]] && DOWNLOAD_STATUS="pass"
  run_remote_check "docker compose run --rm freqtrade backtesting --config user_data/configs/config.dryrun.example.json --strategy M1ATrendValidationStrategy --timeframe 1d --pairs BTC/USDT ETH/USDT --timerange ${SMOKE_TIMERANGE}"
  [[ "$?" -eq 0 ]] && BACKTEST_STATUS="pass"
fi
set -e

if [[ "$PULL_STATUS" == "pass" && "$VERSION_STATUS" == "pass" && "$SHOW_CONFIG_STATUS" == "pass" && "$DOWNLOAD_STATUS" == "pass" && "$BACKTEST_STATUS" == "pass" ]]; then
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
- backtest M1ATrendValidationStrategy: ${BACKTEST_STATUS}
- smoke timerange: ${SMOKE_TIMERANGE}
- no API key used: yes
- no live trading: yes
- no paper trading with real API: yes
- no execution/live: yes
- no runtime data committed: yes
EOF

cat "$REPORT_PATH"
[[ "$STATUS" == "pass" ]]
