#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PY_CMD="${PYTHON:-python3}"
DATA_DIR="${T2_FREQTRADE_DATA_DIR:-$ROOT/freqtrade_lab/user_data/data/binance}"
LOG_DIR="${T2_LOG_DIR:-$ROOT/storage/logs}"
IMAGE="freqtradeorg/freqtrade:2026.6@sha256:d451af021d5e08b70580c0eea5848534e9846b57391b34821c0a5814416397e6"
RAW_OUTPUT="$LOG_DIR/t2_freqtrade_list_data.raw.log"
EVIDENCE="$LOG_DIR/t2_freqtrade_runtime_evidence.json"

command -v docker >/dev/null 2>&1 || { echo "docker is required for the pinned runtime check" >&2; exit 1; }
[[ -d "$DATA_DIR" ]] || { echo "T2 Freqtrade cache not found: $DATA_DIR" >&2; exit 1; }
mkdir -p "$LOG_DIR"

docker pull "$IMAGE" >/dev/null
docker run --rm \
  -v "$DATA_DIR:/freqtrade/user_data/data/binance:ro" \
  "$IMAGE" \
  list-data \
  --datadir /freqtrade/user_data/data/binance \
  --data-format-ohlcv jsongz \
  --show-timerange \
  --no-color 2>&1 | tee "$RAW_OUTPUT"

PYTHONPATH="$ROOT/.deps:$ROOT/src" "$PY_CMD" "$ROOT/scripts/t2_record_freqtrade_runtime.py" \
  --input "$RAW_OUTPUT" \
  --out "$EVIDENCE"
