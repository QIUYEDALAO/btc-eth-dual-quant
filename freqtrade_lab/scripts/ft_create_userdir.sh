#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
docker compose run --rm freqtrade create-userdir --userdir user_data
