#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
exec bash scripts/ft_research.sh recursive-analysis \
  --config user_data/configs/config.dryrun.example.json \
  --strategy M1ATrendValidationStrategy \
  --timeframe 1d \
  --data-format-ohlcv json \
  --pairs BTC/USDT ETH/USDT \
  --timerange "${FT_TIMERANGE:-20170817-20260709}" \
  --startup-candle 220 400
