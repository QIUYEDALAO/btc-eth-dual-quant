#!/usr/bin/env bash
set -euo pipefail

if [[ -z "${VPS_HOST:-}" ]]; then
  echo "VPS_HOST is required. Example: export VPS_HOST=root@47.97.19.77" >&2
  exit 1
fi

VPS_APP_DIR="${VPS_APP_DIR:-~/apps/btc-eth-dual-quant}"

ssh "$VPS_HOST" "cd '$VPS_APP_DIR' && \
  bash deploy/vps/prepare_python_deps.sh && \
  bash deploy/vps/install_docker_ubuntu.sh && \
  bash scripts/m1f_validate.sh && \
  test -f freqtrade_lab/docker-compose.yml && \
  test -f freqtrade_lab/user_data/configs/config.dryrun.example.json && \
  test -f freqtrade_lab/user_data/strategies/M1ATrendValidationStrategy.py"

echo "Remote bootstrap completed. No live trading, API key, or .env setup was performed."
