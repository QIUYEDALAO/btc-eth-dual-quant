#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
bash scripts/ft_no_live_guard.sh
docker compose run --rm freqtrade list-markets \
  --exchange binance \
  --trading-mode futures \
  --pairs BTC/USDT:USDT ETH/USDT:USDT
