#!/usr/bin/env bash
set -euo pipefail

PY_CMD="${PYTHON:-python3}"
export PYTHONPATH="${PYTHONPATH:-.deps:src:.}"

bash scripts/project_validate.sh
"$PY_CMD" scripts/liquid_universe_contract_check.py
"$PY_CMD" scripts/project_state_transition_check.py
"$PY_CMD" -m unittest \
  tests.test_liquid_universe_contract \
  tests.test_liquid_universe_qualification \
  tests.test_universe_gap_attribution \
  tests.test_liquid_universe_end_to_end \
  tests.test_liquid_universe_fault_injection \
  tests.test_liquid_universe_state_machine -v
"$PY_CMD" -m unittest discover -s tests -v
"$PY_CMD" -m compileall src scripts
"$PY_CMD" scripts/m0_secret_scan.py

test -z "$(find . -path ./src/execution/live -print -o -path ./execution/live -print)"
test -z "$(git ls-files | rg '(^|/)(storage/raw|storage/duckdb|storage/logs|freqtrade_lab/user_data/(data|logs|backtest_results))/' || true)"
test -z "$(git ls-files | rg '(^|/)\.env($|\.)|M0_PRIVATE_SMOKE_REPORT\.local\.md$' || true)"
git diff --check
echo "LIQUID_UNIVERSE_V2_HARDENING_VALIDATE PASS"
