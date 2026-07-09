#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
exec bash scripts/ft_research.sh download-data \
  --config user_data/configs/config.dryrun.example.json \
  --exchange binance \
  --pairs BTC/USDT ETH/USDT \
  --timeframes 1d \
  --trading-mode spot \
  --data-format-ohlcv json \
  --timerange "${FT_TIMERANGE:-20170817-20260709}"
