#!/usr/bin/env bash
set -euo pipefail
export PYTHONPATH="${PYTHONPATH:-.deps:src:.}"

bash scripts/liquid_universe_v2_requalification_validate.sh
python3 -m unittest tests.test_liquid_universe_v2_source_conflicts -v
python3 scripts/liquid_universe_v2_source_conflict_check.py
python3 scripts/project_context_check.py
python3 scripts/project_state_transition_check.py
python3 -m compileall src scripts
python3 scripts/m0_secret_scan.py
order_word="ord""er"
fill_word="fi""ll"
engine_word="eng""ine"
trade_pattern="(/api/v3/${order_word}|/fapi/v1/${order_word}|/sapi/v1/margin/${order_word}|place_${order_word}|cancel_${order_word}|create_${order_word}|simulate_${fill_word}|matching_${engine_word})"
test -z "$(rg -n "$trade_pattern" src scripts || true)"
test -z "$(find . -path ./src/execution/live -print -o -path ./execution/live -print)"
test -z "$(git ls-files | grep -E '(^|/)(storage/(raw|duckdb|logs)|\.env($|\.)|M0_PRIVATE_SMOKE_REPORT\.local\.md$)' || true)"
git diff --check
echo "LIQUID_UNIVERSE_V2_SOURCE_CONFLICT_VALIDATE PASS"
