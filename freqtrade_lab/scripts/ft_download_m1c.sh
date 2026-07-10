#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
exec bash scripts/ft_research.sh download-data \
  --config user_data/configs/config.m1c-rotation-research.json \
  --trading-mode spot \
  --timeframes 1d \
  --pairs BTC/USDT ETH/USDT \
  --data-format-ohlcv json \
  --timerange "${FT_TIMERANGE:-20170817-}" \
  "$@"
