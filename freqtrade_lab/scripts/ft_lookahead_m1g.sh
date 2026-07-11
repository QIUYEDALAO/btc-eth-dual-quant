#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
exec bash scripts/ft_research.sh lookahead-analysis \
  --config user_data/configs/config.m1g-research.json \
  --strategy M1GPanicDislocationMeanReversion \
  --timeframe 1h \
  --timeframe-detail 5m \
  --data-format-ohlcv jsongz \
  --pairs BTC/USDT ETH/USDT \
  --timerange "${FT_TIMERANGE:-20200701-20240911}" \
  --minimum-trade-amount 1 \
  --targeted-trade-amount 20 \
  "$@"
