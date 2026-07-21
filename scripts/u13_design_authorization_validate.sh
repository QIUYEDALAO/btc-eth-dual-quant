#!/usr/bin/env bash
set -euo pipefail
repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"
export PYTHONPATH="${PYTHONPATH:-.deps:.venv/lib/python3.12/site-packages:src}"
artifact_scan() { local tracked; tracked="$(git ls-files | grep -E '(^|/)\.env($|\.)|^storage/(raw|duckdb|logs)/|^freqtrade_lab/user_data/(data|logs|backtest_results|hyperopt_results)/|\.duckdb$|\.sqlite($|-)|M0_PRIVATE_SMOKE_REPORT\.local\.md$' || true)"; [[ -z "$tracked" ]] || { printf '%s\n' "$tracked"; return 1; }; }
read_only_scan() { local order="order" post="PO""ST" delete_word="DE""LETE" fill="fill" engine="engine"; local pattern="(/api/v3/${order}|/fapi/v1/${order}|/sapi/v1/margin/${order}|${post}|${delete_word}|place_${order}|cancel_${order}|create_${order}|simulate_${fill}|matching_${engine}|freqtrade[[:space:]]+trade)"; ! rg -n "$pattern" scripts/u13_design_authorization_check.py; }
python3 scripts/u13_design_authorization_check.py
python3 -m unittest -v tests.test_u13_design_authorization
python3 scripts/u12_cross_sectional_paper_observation_check.py
python3 scripts/project_state_transition_check.py
python3 scripts/project_context_check.py
python3 -m unittest discover -s tests -v
python3 -m compileall -q src scripts
read_only_scan
[[ -z "$(find . -path ./src/execution/live -print -o -path ./execution/live -print)" ]]
python3 scripts/m0_secret_scan.py
artifact_scan
git diff --check
