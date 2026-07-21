#!/usr/bin/env bash
set -euo pipefail
repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)";cd "$repo_root"
export PYTHONPATH="${PYTHONPATH:-.deps:.venv/lib/python3.12/site-packages:src}"
python3 scripts/u09_design_authorization_check.py
python3 -m unittest -v tests.test_u09_design_authorization
python3 scripts/u08_cross_sectional_paper_observation_check.py
python3 scripts/project_state_transition_check.py
python3 scripts/project_context_check.py
git diff --check
