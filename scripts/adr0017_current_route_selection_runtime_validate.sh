#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
export PYTHONPATH=".:.deps:src${PYTHONPATH:+:$PYTHONPATH}"
python3 scripts/adr0017_current_route_selection_runtime_check.py
python3 -m unittest -v tests.test_adr0017_current_route_selection_runtime
python3 scripts/project_context_check.py
python3 scripts/external_strategy_route_check.py
python3 scripts/external_strategy_trial_accounting_check.py
python3 -m compileall -q src scripts
python3 scripts/m0_secret_scan.py
[[ -z "$(find . -path ./src/execution/live -print -o -path ./execution/live -print)" ]]
git diff --check
