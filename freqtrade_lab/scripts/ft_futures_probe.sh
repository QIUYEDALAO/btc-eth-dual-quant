#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

timerange="${FT_FUTURES_TIMERANGE:-20240101-20240201}"
config="/freqtrade/user_data/configs/config.futures-funding-backtest.example.json"

bash scripts/ft_research.sh download-data \
  --config "$config" \
  --trading-mode futures \
  --pairs BTC/USDT:USDT ETH/USDT:USDT \
  --timeframes 1d \
  --timerange "$timerange"

bash scripts/ft_research.sh list-data \
  --config "$config" \
  --trading-mode futures

bash scripts/ft_research.sh backtesting \
  --config "$config" \
  --strategy M1BFuturesFundingProbeStrategy \
  --timeframe 1d \
  --timerange "$timerange"
