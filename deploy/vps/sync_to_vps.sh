#!/usr/bin/env bash
set -euo pipefail

if [[ -z "${VPS_HOST:-}" ]]; then
  echo "VPS_HOST is required. Example: export VPS_HOST=root@47.97.19.77" >&2
  exit 1
fi

VPS_APP_DIR="${VPS_APP_DIR:-~/apps/btc-eth-dual-quant}"

echo "Running local M1F validation before sync..."
bash scripts/m1f_validate.sh

echo "Creating remote app directory: ${VPS_APP_DIR}"
ssh "$VPS_HOST" "mkdir -p '$VPS_APP_DIR'"

echo "Syncing project to ${VPS_HOST}:${VPS_APP_DIR}"
rsync -az --delete \
  --exclude '.git/' \
  --exclude '.env' \
  --exclude '.env.*' \
  --exclude '.deps/' \
  --exclude '.venv/' \
  --exclude '__pycache__/' \
  --exclude '.pytest_cache/' \
  --exclude 'storage/raw/' \
  --exclude 'storage/duckdb/' \
  --exclude 'storage/logs/' \
  --exclude 'storage/*.db' \
  --exclude 'storage/*.duckdb' \
  --exclude 'reports/m0/M0_PRIVATE_SMOKE_REPORT.local.md' \
  --exclude 'freqtrade_lab/.env' \
  --exclude 'freqtrade_lab/.env.*' \
  --exclude 'freqtrade_lab/user_data/data/' \
  --exclude 'freqtrade_lab/user_data/logs/' \
  --exclude 'freqtrade_lab/user_data/backtest_results/' \
  --exclude 'freqtrade_lab/user_data/hyperopt_results/' \
  --exclude 'freqtrade_lab/user_data/*.sqlite' \
  --exclude 'freqtrade_lab/user_data/*.sqlite-shm' \
  --exclude 'freqtrade_lab/user_data/*.sqlite-wal' \
  ./ "$VPS_HOST:$VPS_APP_DIR/"

echo "Preparing remote Python validation dependencies..."
ssh "$VPS_HOST" "cd '$VPS_APP_DIR' && bash deploy/vps/prepare_python_deps.sh"

echo "Running remote M1F validation..."
ssh "$VPS_HOST" "cd '$VPS_APP_DIR' && bash scripts/m1f_validate.sh"

echo "VPS sync completed."
