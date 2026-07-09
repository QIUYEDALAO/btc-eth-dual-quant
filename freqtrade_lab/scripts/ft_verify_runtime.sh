#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
bash scripts/ft_no_live_guard.sh

observed_version="$(docker compose run --rm freqtrade --version)"
printf '%s\n' "$observed_version"
python3 ../scripts/freqtrade_runtime_manifest.py validate \
  --manifest runtime-manifest.json \
  --compose docker-compose.yml \
  --observed-version "$observed_version"
