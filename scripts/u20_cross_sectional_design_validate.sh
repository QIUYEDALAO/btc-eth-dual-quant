#!/usr/bin/env bash
set -euo pipefail
repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"
export PYTHONPATH="${PYTHONPATH:-.deps:.venv/lib/python3.12/site-packages:src}"
python3 scripts/u20_cross_sectional_design_check.py
python3 -m unittest -v tests.test_u20_cross_sectional_design
python3 scripts/u20_design_authorization_check.py
python3 scripts/project_state_transition_check.py
python3 scripts/project_context_check.py
python3 -m unittest discover -s tests -q
python3 -m compileall -q src scripts
[[ -z "$(find . -path ./src/execution/live -print -o -path ./execution/live -print)" ]]
python3 scripts/m0_secret_scan.py
git diff --check
