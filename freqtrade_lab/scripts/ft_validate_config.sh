#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
bash scripts/ft_no_live_guard.sh
docker compose run --rm freqtrade show-config --config user_data/configs/config.dryrun.example.json
