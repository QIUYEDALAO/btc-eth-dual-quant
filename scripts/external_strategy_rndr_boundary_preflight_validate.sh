#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

python3 scripts/external_strategy_rndr_boundary_preflight.py
python3 -m unittest -q tests.test_external_strategy_rndr_boundary_preflight
