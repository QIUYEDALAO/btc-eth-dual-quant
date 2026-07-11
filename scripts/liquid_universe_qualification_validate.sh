#!/usr/bin/env bash
set -euo pipefail
export PYTHONPATH="${PYTHONPATH:-.deps:src:.}"
bash scripts/liquid_universe_contract_validate.sh
python3 -m unittest tests.test_liquid_universe_qualification -v
python3 -m unittest tests.test_universe_gap_attribution -v
python3 scripts/liquid_universe_qualification_check.py
python3 scripts/liquid_universe_gap_attribution_check.py
python3 -m compileall src scripts
python3 scripts/m0_secret_scan.py
test -z "$(find . -path ./src/execution/live -print -o -path ./execution/live -print)"
git diff --check
echo "LIQUID_UNIVERSE_QUALIFICATION_VALIDATE PASS"
