#!/usr/bin/env bash
set -euo pipefail
repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)";cd "$repo_root";export PYTHONPATH="${PYTHONPATH:-.deps:.venv/lib/python3.12/site-packages:src}"
python3 scripts/u10_cross_sectional_paper_protocol_review_check.py
python3 -m unittest -v tests.test_u10_cross_sectional_paper_protocol_review
python3 scripts/u10_cross_sectional_paper_protocol_check.py
python3 scripts/project_state_transition_check.py
python3 scripts/project_context_check.py
git diff --check
