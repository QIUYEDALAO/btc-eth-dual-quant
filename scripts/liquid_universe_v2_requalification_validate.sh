#!/usr/bin/env bash
set -euo pipefail
export PYTHONPATH="${PYTHONPATH:-.deps:src:.}"

bash scripts/liquid_universe_v2_hardening_validate.sh
python3 -m unittest tests.test_liquid_universe_v2_requalification -v
python3 scripts/liquid_universe_v2_requalification_check.py
python3 scripts/project_state_transition_check.py
python3 -m compileall src scripts
python3 scripts/m0_secret_scan.py
test -z "$(find . -path ./src/execution/live -print -o -path ./execution/live -print)"
test -z "$(git ls-files | grep -E '(^|/)(storage/(raw|duckdb|logs)|\.env($|\.)|M0_PRIVATE_SMOKE_REPORT\.local\.md$)' || true)"
git diff --check
echo "LIQUID_UNIVERSE_V2_REQUALIFICATION_VALIDATE PASS"
