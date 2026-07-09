#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
bash scripts/ft_no_live_guard.sh
docker compose run --rm freqtrade backtesting \
  --config user_data/configs/config.dryrun.example.json \
  --strategy M1ATrendValidationStrategy \
  --timeframe 1d \
  --pairs BTC/USDT ETH/USDT
