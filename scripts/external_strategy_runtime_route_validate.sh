#!/usr/bin/env bash
set -euo pipefail

export PYTHONPATH="${PYTHONPATH:-.deps:src}"
python3 scripts/external_strategy_is_boundary_qualification.py
python3 -m unittest tests.test_external_strategy_runtime_route -v
