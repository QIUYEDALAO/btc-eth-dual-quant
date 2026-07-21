#!/usr/bin/env bash
set -euo pipefail

python3 scripts/external_strategy_boundary_source_preflight.py
PYTHONPATH=".deps:src" python3 -m unittest -v tests.test_external_strategy_boundary_source_preflight
