#!/usr/bin/env bash
set -euo pipefail
repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"; cd "$repo_root"
export PYTHONPATH="${PYTHONPATH:-.deps:.venv/lib/python3.12/site-packages:src}"; python_cmd="${PYTHON:-python3}"
"$python_cmd" scripts/u06_cross_sectional_paper_protocol_check.py
"$python_cmd" -m unittest -v tests.test_u06_cross_sectional_paper_protocol
"$python_cmd" scripts/u06_cross_sectional_design_check.py
"$python_cmd" scripts/project_state_transition_check.py
"$python_cmd" scripts/project_context_check.py
git diff --check
