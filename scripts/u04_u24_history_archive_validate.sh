#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
python3 scripts/u04_u24_history_archive_check.py
if [[ "${ARCHIVE_REPLAY:-0}" == "1" ]]; then
  bash scripts/u04_u24_history_archive_replay.sh
fi
