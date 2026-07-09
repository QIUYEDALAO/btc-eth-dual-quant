#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
bash scripts/ft_no_live_guard.sh
docker compose run --rm freqtrade download-data \
  --config user_data/configs/config.dryrun.example.json \
  --exchange binance \
  --pairs BTC/USDT ETH/USDT \
  --timeframes 1d \
  --trading-mode spot
