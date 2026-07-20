#!/usr/bin/env bash
set -euo pipefail
export PYTHONPATH=".:.deps:src${PYTHONPATH:+:$PYTHONPATH}"
python3 scripts/external_strategy_route_check.py
python3 scripts/external_strategy_trial_accounting_check.py
python3 -m unittest -v tests.test_external_strategy_route
