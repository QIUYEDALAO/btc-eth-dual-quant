#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
exec bash scripts/ft_research.sh list-data \
  --config user_data/configs/config.dryrun.example.json \
  --data-format-ohlcv json \
  --trading-mode spot \
  --show-timerange
