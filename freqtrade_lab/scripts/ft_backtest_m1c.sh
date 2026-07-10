#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
exec bash scripts/ft_research.sh backtesting \
  --config user_data/configs/config.m1c-rotation-research.json \
  --strategy BTCETHRelativeStrengthRotation \
  --timeframe 1d \
  --data-format-ohlcv json \
  --pairs BTC/USDT ETH/USDT \
  --timerange "${FT_TIMERANGE:-20170817-}" \
  --fee "${FT_FEE:-0.0015}" \
  --cache none \
  "$@"
