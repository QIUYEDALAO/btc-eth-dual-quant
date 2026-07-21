#!/usr/bin/env bash
set -euo pipefail
export PYTHONPATH="${PYTHONPATH:-.deps:.venv/lib/python3.12/site-packages:src}"
python3 scripts/u14_cross_sectional_paper_observation_check.py
python3 -m unittest tests.test_u14_cross_sectional_paper_observation -v
python3 scripts/project_state_transition_check.py
python3 scripts/project_context_check.py
python3 scripts/m0_secret_scan.py
test ! -e src/execution/live
test ! -e execution/live
git diff --check
