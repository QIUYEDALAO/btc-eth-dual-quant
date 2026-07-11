#!/usr/bin/env bash
set -euo pipefail

scenario="${1:-}"
shift || true
case "$scenario" in
  base) fee="0.0015" ;;
  cost-x2) fee="0.0030" ;;
  stress-a) fee="0.0040" ;;
  stress-b) fee="0.0055" ;;
  *) echo "Usage: $0 {base|cost-x2|stress-a|stress-b}" >&2; exit 2 ;;
esac

cd "$(dirname "$0")/.."
result_root="${M1G_RESULT_ROOT:-user_data/backtest_results/m1g-is}"
result_dir="${result_root}/${scenario}"
mkdir -p "$result_dir"
exec bash scripts/ft_research.sh backtesting \
  --config user_data/configs/config.m1g-research.json \
  --strategy M1GPanicDislocationMeanReversion \
  --timeframe 1h \
  --timeframe-detail 5m \
  --data-format-ohlcv jsongz \
  --pairs BTC/USDT ETH/USDT \
  --timerange 20200701-20240911 \
  --fee "$fee" \
  --export trades \
  --backtest-directory "$result_dir" \
  --notes "m1g-is:${scenario}" \
  --cache none \
  "$@"
