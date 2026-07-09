#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
docker compose pull
bash scripts/ft_verify_runtime.sh
