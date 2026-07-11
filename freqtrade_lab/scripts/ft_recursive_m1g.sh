#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
exec bash scripts/ft_research.sh recursive-analysis \
  --config user_data/configs/config.m1g-research.json \
  --strategy M1GPanicDislocationMeanReversion \
  --timeframe 1h \
  --data-format-ohlcv jsongz \
  --pairs BTC/USDT ETH/USDT \
  --timerange "${FT_TIMERANGE:-20200701-20240911}" \
  --startup-candle 170 250 340 \
  "$@"
